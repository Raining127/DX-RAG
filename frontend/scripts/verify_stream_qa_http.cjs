// Real QAPanel and SSE client over loopback HTTP to real FastAPI/Uvicorn.
// React hooks and upstream storage/retrieval/model SDK are controlled fixtures.
// No real ChromaDB, documents, provider, browser or external network is used.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {spawn} = require('node:child_process');
const ts = require('typescript');
const React = require('react');
const antd = require('antd');
const root = path.resolve(__dirname, '..');
const backend = path.resolve(root, '../backend');
const child = spawn('python', ['-B', 'tests/stream_ui_fixture.py'], {
  cwd: backend, stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true,
});
let output = '', errors = '', exitCode;
const messages = [];
child.stdout.setEncoding('utf8');
child.stderr.setEncoding('utf8');
child.stdout.on('data', chunk => {
  output += chunk;
  while (output.includes('\n')) {
    const index = output.indexOf('\n');
    const line = output.slice(0, index); output = output.slice(index + 1);
    try { messages.push(JSON.parse(line)); } catch { errors += line + '\n'; }
  }
});
child.stderr.on('data', chunk => { errors += chunk; });
child.on('exit', code => { exitCode = code; });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function waitFor(predicate, label) {
  const deadline = Date.now() + 8000;
  while (Date.now() < deadline) {
    if (predicate()) return;
    if (exitCode !== undefined) throw new Error(`fixture exited (${exitCode}): ${errors}`);
    await delay(10);
  }
  throw new Error(`timed out waiting for ${label}; fixture stderr: ${errors}`);
}

const modules = new Map();
const cells = [];
let cursor = 0, dirty = true, effects = [], tree;
const calls = [];
let apiBase;
const same = (a, b) => a && b && a.length === b.length && a.every((x, i) => Object.is(x, b[i]));
const hooks = {
  ...React,
  useState(initial) {
    const i = cursor++;
    if (!(i in cells)) cells[i] = typeof initial === 'function' ? initial() : initial;
    return [cells[i], value => {
      const next = typeof value === 'function' ? value(cells[i]) : value;
      if (!Object.is(next, cells[i])) { cells[i] = next; dirty = true; }
    }];
  },
  useRef(value) { const i = cursor++; return cells[i] ?? (cells[i] = {current:value}); },
  useMemo(factory, deps) {
    const i = cursor++;
    if (!same(cells[i]?.deps, deps)) cells[i] = {deps, value:factory()};
    return cells[i].value;
  },
  useCallback(callback, deps) { return hooks.useMemo(() => callback, deps); },
  useEffect(callback, deps) {
    const i = cursor++;
    if (!same(cells[i]?.deps, deps)) {
      const previous = cells[i]; cells[i] = {deps};
      effects.push(() => { previous?.cleanup?.(); cells[i].cleanup = callback(); });
    }
  },
};
function load(relative) {
  if (modules.has(relative)) return modules.get(relative);
  const exports = {};
  const compiled = ts.transpileModule(fs.readFileSync(path.join(root, relative), 'utf8'), {
    compilerOptions: {module:ts.ModuleKind.CommonJS, jsx:ts.JsxEmit.ReactJSX,
      esModuleInterop:true, target:ts.ScriptTarget.ES2020},
  }).outputText;
  vm.runInNewContext(compiled, {exports, AbortController, Date, console, setTimeout, clearTimeout,
    TextDecoder, process:{env:{NEXT_PUBLIC_API_BASE_URL:apiBase}},
    fetch:(url, init) => {
      calls.push({url, body:JSON.parse(init.body), signal:init.signal});
      return fetch(url, init);
    },
    require(name) {
      if (name === 'react') return hooks;
      if (name === 'react-markdown') return {__esModule:true, default:'markdown'};
      if (name.startsWith('@/')) {
        const base = name.slice(2);
        return load(base + (fs.existsSync(path.join(root, base + '.tsx')) ? '.tsx' : '.ts'));
      }
      return require(name);
    },
  }, {filename:relative});
  modules.set(relative, exports);
  return exports;
}
function all(element, predicate) {
  if (!element || typeof element !== 'object') return [];
  return [...(predicate(element) ? [element] : []),
    ...React.Children.toArray(element.props?.children).flatMap(child => all(child, predicate))];
}
const text = node => typeof node === 'string' || typeof node === 'number' ? String(node)
  : node && typeof node === 'object' ? [node.props?.message,node.props?.description,
    ...React.Children.toArray(node.props?.children)].map(text).join('') : '';
const displayed = () => text(tree);
const button = label => all(tree,n => n.type === antd.Button && text(n).includes(label))[0];
const input = () => all(tree,n => n.type === antd.Input.TextArea)[0];
const sources = () => all(tree,n => n.type === antd.Collapse);
let QAPanel;
const props = {collections:[{name:'kb',file_count:1},{name:'empty-kb',file_count:0}],
  collectionState:'ready',collectionError:'',onRetryCollections(){}};
async function settle() {
  for (let i = 0; i < 50; i++) {
    if (dirty) { dirty = false; cursor = 0; tree = QAPanel(props); }
    const queue = effects; effects = []; queue.forEach(effect => effect());
    await new Promise(resolve => setImmediate(resolve));
    if (!dirty && !effects.length) return;
  }
  throw new Error('hook scheduler did not settle');
}
async function waitUI(predicate, label) {
  const deadline = Date.now() + 8000;
  while (Date.now() < deadline) {
    await settle();
    if (predicate()) return;
    if (exitCode !== undefined) throw new Error(`fixture exited (${exitCode}): ${errors}`);
    await delay(10);
  }
  throw new Error(`timed out waiting for UI ${label}; rendered: ${displayed()}; fixture: ${errors}`);
}
async function send(question) {
  input().props.onChange({target:{value:question}}); await settle();
  button('发送问题').props.onClick(); await settle();
}
const release = question => child.stdin.write(`release ${question}\n`);
const hasMessage = (event, question) => messages.some(m => m.event === event && m.question === question);

(async () => {
  try {
    await waitFor(() => messages.some(m => m.event === 'ready'), 'fixture startup');
    const port = messages.find(m => m.event === 'ready').port;
    apiBase = `http://127.0.0.1:${port}/api`;
    QAPanel = load('components/QAPanel.tsx').default;
    await settle();

    await send('normal');
    await waitUI(() => displayed().includes('首段:normal'), 'first delta');
    assert.ok(button('停止生成')); assert.equal(sources().length, 0);
    assert.doesNotMatch(displayed(), /回答完成/);
    assert.equal(calls[0].body.question, 'normal');
    release('normal');
    await waitUI(() => displayed().includes('回答完成'), 'completion');
    assert.match(displayed(), /首段:normal末段/); assert.equal(sources().length, 1);
    console.log('PASS real HTTP first delta before controlled model release and completed sources');

    await send('cancel');
    await waitUI(() => displayed().includes('首段:cancel'), 'cancel delta');
    button('停止生成').props.onClick(); await settle();
    assert.match(displayed(), /已停止/); assert.equal(calls.at(-1).signal.aborted, true);
    await waitFor(() => hasMessage('closed','cancel'), 'cancelled upstream close');
    assert.equal(button('重新生成') !== undefined, true);
    console.log('PASS real HTTP disconnect closes blocked upstream and retains partial answer');

    await send('length');
    await waitUI(() => displayed().includes('首段:length'), 'length delta');
    release('length'); await waitUI(() => displayed().includes('回答已截断'), 'length terminal');
    assert.ok(button('重新生成')); assert.equal(sources().length, 1);

    await send('empty');
    await waitFor(() => hasMessage('model','empty'), 'empty model request');
    release('empty'); await waitUI(() => displayed().includes('回答为空'), 'empty terminal');
    assert.ok(button('重新生成')); assert.equal(sources().length, 1);
    console.log('PASS real adapter and HTTP preserve truncated/empty turns without sources');

    await send('no-match');
    await waitUI(() => displayed().includes('首段:no-match'), 'no-match delta');
    release('no-match'); await waitUI(() => displayed().includes('首段:no-match末段'), 'no-match completion');
    await waitUI(() => displayed().includes('回答完成'), 'no-match done');
    assert.equal(sources().length, 1, 'no-match must not add another source list');
    assert.deepEqual(calls.at(-1).body.history, [
      {role:'user',content:'normal'}, {role:'assistant',content:'首段:normal末段'},
    ]);
    const modelMessage = messages.find(m => m.event === 'model' && m.question === 'no-match').message;
    assert.match(modelMessage, /User: normal/); assert.doesNotMatch(modelMessage, /User: cancel|User: length|User: empty/);
    console.log('PASS real HTTP no-match and completed-only history through backend prompt');
    console.log('SUMMARY 4/4 PASS; real QAPanel/SSE client + loopback FastAPI and real stream adapter; simulated hooks/retrieval/SDK, no browser or provider');
  } finally {
    for (const value of cells) value?.cleanup?.();
    if (exitCode === undefined) {
      child.stdin.end('stop\n');
      const deadline = Date.now() + 6000;
      while (exitCode === undefined && Date.now() < deadline) await delay(20);
      if (exitCode === undefined) {
        child.kill();
        throw new Error('fixture did not shut down gracefully');
      }
      if (exitCode !== 0) throw new Error(`fixture shutdown failed (${exitCode}): ${errors}`);
    }
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
