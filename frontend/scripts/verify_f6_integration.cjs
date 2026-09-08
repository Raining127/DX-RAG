// Actual Home and feature components, deterministic API/hook scheduler.
// No browser, provider, new dependency, or source-string assertions.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const antd = require('antd');
const root = path.resolve(__dirname, '..');
const cells = new Map();
const cache = new Map();
let current, cursor, dirty = true, effects = [];
let serial = 0, rejectUpload = false, warningUpload = false;
const server = new Map([['kb-a', []], ['kb-b', []]]);
const calls = [];
const same = (a, b) => a && b && a.length === b.length && a.every((x, i) => Object.is(x, b[i]));
const hooks = {
  ...React,
  useState(initial) {
    const owner = current, i = cursor++;
    if (!(i in owner)) owner[i] = typeof initial === 'function' ? initial() : initial;
    return [owner[i], value => {
      const next = typeof value === 'function' ? value(owner[i]) : value;
      if (!Object.is(next, owner[i])) { owner[i] = next; dirty = true; }
    }];
  },
  useRef(value) { const i = cursor++; return current[i] ?? (current[i] = { current: value }); },
  useMemo(factory, deps) {
    const i = cursor++;
    if (!same(current[i]?.deps, deps)) current[i] = { deps, value: factory() };
    return current[i].value;
  },
  useCallback(callback, deps) { return hooks.useMemo(() => callback, deps); },
  useEffect(callback, deps) {
    const owner = current, i = cursor++;
    if (!same(owner[i]?.deps, deps)) {
      const previous = owner[i];
      owner[i] = { deps };
      effects.push(() => { previous?.cleanup?.(); owner[i].cleanup = callback(); });
    }
  },
};
const api = {
  ApiError: class extends Error {},
  async listCollections() {
    calls.push(['collections']);
    return { collections: [...server].map(([name, files]) => ({ name, file_count: files.length })) };
  },
  async listFiles(kb) { calls.push(['list', kb]); return { collection_name: kb, files: server.get(kb).slice() }; },
  async uploadFile(file, kb) {
    calls.push(['upload', kb]);
    if (rejectUpload) throw new Error('Controlled upload rejection');
    assert.ok(!server.get(kb).some(row => row.file_name === file.name));
    const row = { file_id: `file-${++serial}`, file_name: file.name, size: file.size,
      chunk_count: 1, status: warningUpload ? 'SUCCESS_WITH_WARNINGS' : 'SUCCESS', upload_time: '2026-09-07T00:00:00Z' };
    server.get(kb).push(row);
    return { ...row, collection_name: kb, chunks: 1,
      warnings: warningUpload ? [{ page_number: 2, error_code: 'OCR_PAGE_FAILED' }] : [] };
  },
  async previewFile(id, kb) {
    calls.push(['preview', kb, id]);
    const row = server.get(kb).find(file => file.file_id === id);
    assert.ok(row, 'preview stays in its KB');
    return { file_id: id, file_name: row.file_name, collection_name: kb, content: 'persisted fixture', preview_chars: 17, total_chars: 17 };
  },
  async deleteFile(id, kb) {
    calls.push(['delete', kb, id]);
    const row = server.get(kb).find(file => file.file_id === id);
    assert.ok(row, 'delete stays in its KB');
    server.set(kb, server.get(kb).filter(file => file.file_id !== id));
    return { file_name: row.file_name, collection_name: kb, message: 'deleted' };
  },
  async renameCollection(oldName, newName) {
    server.set(newName, server.get(oldName)); server.delete(oldName);
    return { old_name: oldName, new_name: newName };
  },
  async deleteCollection(name) { server.delete(name); return { name }; },
  async queryQA(question, kb, topK, history) {
    calls.push(['query', kb, history.length]);
    return { answer: 'fixture answer', sources: [], query: question, collection_name: kb };
  },
};
function load(relative) {
  if (cache.has(relative)) return cache.get(relative);
  const exports = {};
  const compiled = ts.transpileModule(fs.readFileSync(path.join(root, relative), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  vm.runInNewContext(compiled, { exports, require(name) {
    if (name === 'react') return hooks;
    if (name === '@/lib/api-client') return api;
    if (name.startsWith('@/')) {
      const base = name.slice(2);
      return load(base + (fs.existsSync(path.join(root, base + '.tsx')) ? '.tsx' : '.ts'));
    }
    return require(name);
  } }, { filename: relative });
  cache.set(relative, exports);
  return exports;
}
function all(element, predicate) {
  if (!element || typeof element !== 'object') return [];
  return [...(predicate(element) ? [element] : []),
    ...React.Children.toArray(element.props?.children).flatMap(child => all(child, predicate))];
}
const find = (tree, type) => all(tree, node => node.type === type)[0];
const text = node => typeof node === 'string' || typeof node === 'number' ? String(node)
  : node && typeof node === 'object' ? React.Children.toArray(node.props?.children).map(text).join('') : '';
const Home = load('app/page.tsx').default;
const features = Object.fromEntries(['FileUpload', 'FileManager', 'KnowledgeBaseManager', 'QAPanel']
  .map(name => [name, load(`components/${name}.tsx`).default]));
let home, trees = {}, props = {};
function render(name, Component, attributes) {
  if (!cells.has(name)) cells.set(name, []);
  current = cells.get(name); cursor = 0;
  return Component(attributes);
}
async function settle() {
  for (let round = 0; round < 50; round++) {
    if (dirty) {
      dirty = false;
      home = render('Home', Home, {});
      for (const [name, Component] of Object.entries(features)) {
        props[name] = find(home, Component).props;
        trees[name] = render(name, Component, props[name]);
      }
    }
    const queue = effects; effects = []; queue.forEach(effect => effect());
    await new Promise(resolve => setImmediate(resolve));
    if (!dirty && !effects.length) return;
  }
  throw new Error('Hook scheduler did not settle');
}
const rows = () => find(trees.FileManager, antd.Table)?.props.dataSource ?? [];
const count = kb => props.KnowledgeBaseManager.collections.find(row => row.name === kb)?.file_count;
const listCalls = kb => calls.filter(call => call[0] === 'list' && call[1] === kb).length;
function verifyCounts() {
  for (const [kb, files] of server) assert.equal(count(kb), files.length, `shared count ${kb}`);
  const displayed = all(trees.KnowledgeBaseManager, node => node.props?.className === 'kb-summary-value');
  assert.equal(text(displayed[1]), String([...server.values()].reduce((n, files) => n + files.length, 0)), 'rendered KB total');
}
async function upload(name = 'same.txt') {
  find(trees.FileUpload, antd.Upload.Dragger).props.customRequest({ file: { name, size: 17 } });
  await settle();
}
async function select(feature, kb) { find(trees[feature], antd.Select).props.onChange(kb); await settle(); }
function actions(row) {
  return find(trees.FileManager, antd.Table).props.columns.find(column => column.key === 'actions').render(undefined, row);
}
let passed = 0;
function pass(name) { passed++; console.log(`PASS ${name}`); }
async function main() {
  await settle();
  assert.equal(rows().length, 0); assert.equal(listCalls('kb-a'), 1);
  const qaInput = find(trees.QAPanel, antd.Input.TextArea);
  qaInput.props.onChange({ target: { value: 'preserve this draft' } }); await settle();
  await upload();
  assert.equal(server.get('kb-a').length, 1);
  assert.equal(rows().length, 1, 'F-6: mounted FileManager must refresh after same-KB upload');
  assert.equal(rows()[0].file_name, 'same.txt'); assert.equal(listCalls('kb-a'), 2);
  verifyCounts(); assert.equal(find(trees.QAPanel, antd.Input.TextArea).props.value, 'preserve this draft');
  pass('A: same-KB upload refreshes hidden mounted list and rendered/shared counts; QA draft preserved');

  find(trees.QAPanel, antd.Input.TextArea).props.onKeyDown({ key: 'Enter', ctrlKey: true, preventDefault() {} });
  await settle();
  const historyCount = () => all(trees.QAPanel, node => node.props?.className === 'qa-history-meter')[0].props['aria-label'];
  const previousHistory = historyCount();
  assert.ok(previousHistory.includes('2'));
  const first = rows()[0];
  find(actions(first), antd.Button).props.onClick(); await settle();
  assert.ok(text(trees.FileManager).includes('persisted fixture'));
  await find(actions(first), antd.Popconfirm).props.onConfirm(); await settle();
  assert.equal(rows().length, 0); verifyCounts();
  await upload(); assert.equal(rows().length, 1); assert.notEqual(rows()[0].file_id, first.file_id); verifyCounts();
  assert.equal(historyCount(), previousHistory, 'file lifecycle must not reset QA history');
  pass('B: upload/list/preview/delete/empty/count-zero/same-name-reupload/count-one in one session');

  const aId = rows()[0].file_id, aCalls = listCalls('kb-a');
  await select('FileUpload', 'kb-b'); await upload();
  assert.equal(rows()[0].file_id, aId); assert.equal(listCalls('kb-a'), aCalls); verifyCounts();
  await select('FileManager', 'kb-b'); assert.equal(rows().length, 1); assert.notEqual(rows()[0].file_id, aId);
  await find(actions(rows()[0]), antd.Popconfirm).props.onConfirm(); await settle();
  assert.equal(server.get('kb-a')[0].file_id, aId); verifyCounts();
  pass('C: KB-B upload/delete never refreshes or changes KB-A rows/count');

  warningUpload = true; await upload(); warningUpload = false;
  assert.equal(rows().length, 1); verifyCounts();
  const before = listCalls('kb-b'); rejectUpload = true; await upload('rejected.txt'); rejectUpload = false;
  assert.equal(listCalls('kb-b'), before); assert.equal(rows().length, 1); verifyCounts();
  pass('warning-success synchronizes; rejected upload changes neither count nor list');

  // Use actual KB modal/button handlers, not direct Home callback invocation.
  const card = all(trees.KnowledgeBaseManager, node => node.type === 'article').find(node => text(node).includes('kb-b'));
  const renameButton = all(card, node => node.type === antd.Button).find(node => text(node).includes('\u91cd\u547d\u540d'));
  assert.ok(renameButton); renameButton.props.onClick(); await settle();
  const modal = all(trees.KnowledgeBaseManager, node => node.type === antd.Modal && node.props.open)[0];
  find(modal, antd.Input).props.onChange({ target: { value: 'kb-renamed' } }); await settle();
  await all(trees.KnowledgeBaseManager, node => node.type === antd.Modal && node.props.open)[0].props.onOk(); await settle();
  assert.equal(find(trees.FileManager, antd.Select).props.value, 'kb-renamed'); assert.equal(rows().length, 1); verifyCounts();
  const renamedCard = all(trees.KnowledgeBaseManager, node => node.type === 'article').find(node => text(node).includes('kb-renamed'));
  await find(renamedCard, antd.Popconfirm).props.onConfirm(); await settle();
  assert.equal(find(trees.FileManager, antd.Select).props.value, 'kb-a'); assert.equal(rows()[0].file_id, aId); verifyCounts();
  pass('actual KB rename/delete callbacks retain identity/fallback and counts');
  console.log(`SUMMARY ${passed}/${passed} PASS; MOCKED API/hooks, actual Home + four components; no browser/provider`);
}
main().catch(error => { console.error(`FAIL ${error.message}`); process.exitCode = 1; });
