// Controlled interaction tests for the real QAPanel component. React hooks and
// the streaming API are simulated; no browser, backend, or provider is used.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const antd = require('antd');
const root = path.resolve(__dirname, '..');

const cells = [];
const modules = new Map();
let cursor = 0, dirty = true, effects = [], tree, requests = [];
let conversation = {scrollTop: 0, scrollHeight: 1000, clientHeight: 100};
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
  useReducer(reducer, initial, init) {
    const i = cursor++;
    if (!(i in cells)) cells[i] = init ? init(initial) : initial;
    return [cells[i], action => { cells[i] = reducer(cells[i], action); dirty = true; }];
  },
  useRef(value) { const i = cursor++; return cells[i] ?? (cells[i] = {current: value}); },
  useMemo(factory, deps) {
    const i = cursor++;
    if (!same(cells[i]?.deps, deps)) cells[i] = {deps, value: factory()};
    return cells[i].value;
  },
  useCallback(callback, deps) { return hooks.useMemo(() => callback, deps); },
  useEffect(callback, deps) {
    const i = cursor++;
    if (!same(cells[i]?.deps, deps)) {
      const previous = cells[i];
      cells[i] = {deps};
      effects.push(() => { previous?.cleanup?.(); cells[i].cleanup = callback(); });
    }
  },
};
hooks.useLayoutEffect = hooks.useEffect;

class ApiError extends Error {
  constructor(message, {code, status = 0, details = {}}) {
    super(message); this.code = code; this.status = status; this.details = details;
  }
}
const api = {
  ApiError,
  streamQueryQA(question, collection, options) {
    let resolve, reject;
    const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
    const call = {question, collection, options, resolve, reject,
      emit(event) { options.onEvent(event); },
      done(sources = []) { options.onEvent({type: 'done', sources}); resolve(); },
      incomplete(reason) { options.onEvent({type: 'incomplete', reason}); resolve(); },
      fail(code, message = code) { reject(new ApiError(message, {code})); },
    };
    if (options.signal) {
      options.signal.addEventListener('abort', () => call.fail('STREAM_CANCELLED', '已停止生成'), {once: true});
    }
    requests.push(call);
    return promise;
  },
};

function load(relative) {
  if (modules.has(relative)) return modules.get(relative);
  const exports = {};
  const compiled = ts.transpileModule(fs.readFileSync(path.join(root, relative), 'utf8'), {
    compilerOptions: {module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX,
      esModuleInterop: true, target: ts.ScriptTarget.ES2020},
  }).outputText;
  vm.runInNewContext(compiled, {
    exports, AbortController, Date, console, setTimeout, clearTimeout,
    window: { matchMedia: () => ({matches: true}) },
    require(name) {
      if (name === 'react') return hooks;
      if (name === 'react-markdown') return {__esModule: true, default: 'markdown'};
      if (name === '@/lib/api-client') return api;
      if (name.startsWith('@/')) {
        const base = name.slice(2);
        return load(base + (fs.existsSync(path.join(root, base + '.tsx')) ? '.tsx' : '.ts'));
      }
      return require(name);
    },
  }, {filename: relative});
  modules.set(relative, exports);
  return exports;
}
function all(element, predicate) {
  if (!element || typeof element !== 'object') return [];
  return [...(predicate(element) ? [element] : []),
    ...React.Children.toArray(element.props?.children).flatMap(child => all(child, predicate))];
}
const text = node => typeof node === 'string' || typeof node === 'number' ? String(node)
  : node && typeof node === 'object' ? [node.props?.message, node.props?.description,
      ...React.Children.toArray(node.props?.children)].map(text).join('') : '';
const find = (type) => all(tree, node => node.type === type)[0];
const button = label => all(tree, node => node.type === antd.Button && text(node).includes(label))[0];
const input = () => find(antd.Input.TextArea);
const displayed = () => text(tree);
let props = { collections: [{name: 'kb-a', file_count: 1}, {name: 'kb-b', file_count: 1}],
  collectionState: 'ready', collectionError: '', onRetryCollections() {} };
const QAPanel = load('components/QAPanel.tsx').default;
async function settle() {
  for (let rounds = 0; rounds < 50; rounds++) {
    if (dirty) {
      dirty = false; cursor = 0; tree = QAPanel(props);
      const node = all(tree, element => element.props?.className === 'qa-conversation')[0];
      if (node?.ref && typeof node.ref === 'object') node.ref.current = conversation;
    }
    const queue = effects; effects = []; queue.forEach(effect => effect());
    await new Promise(resolve => setImmediate(resolve));
    if (!dirty && !effects.length) return;
  }
  throw new Error('Hook scheduler did not settle');
}
async function reset() {
  for (const value of cells) value?.cleanup?.();
  await new Promise(resolve => setImmediate(resolve));
  cells.length = 0; effects = []; dirty = true; requests = [];
  conversation = {scrollTop: 0, scrollHeight: 1000, clientHeight: 100};
  props = { collections: [{name: 'kb-a', file_count: 1}, {name: 'kb-b', file_count: 1}],
    collectionState: 'ready', collectionError: '', onRetryCollections() {} };
  await settle();
}
async function type(value) { input().props.onChange({target: {value}}); await settle(); }
async function send(value) {
  await type(value);
  assert.ok(button('发送问题')); button('发送问题').props.onClick();
  await settle(); return requests.at(-1);
}
async function emit(call, event) { call.emit(event); await settle(); }
async function complete(call, answer, sources = []) {
  await emit(call, {type: 'delta', text: answer});
  call.done(sources); await settle();
}

const tests = [];
const test = (name, fn) => tests.push([name, fn]);

test('stream statuses, incremental answer, source only on done and editable draft', async () => {
  await reset();
  const call = await send('问题一');
  assert.equal(call.question, '问题一'); assert.equal(call.collection, 'kb-a');
  await emit(call, {type: 'status', stage: 'retrieving'});
  assert.match(displayed(), /检索/);
  await emit(call, {type: 'status', stage: 'generating'});
  assert.match(displayed(), /生成/);
  await emit(call, {type: 'status', stage: 'retrying'});
  assert.match(displayed(), /重试/);
  await emit(call, {type: 'delta', text: '第一段'});
  assert.match(displayed(), /第一段/); assert.equal(all(tree, node => node.type === antd.Collapse).length, 0);
  await type('下一题草稿');
  assert.equal(input().props.value, '下一题草稿');
  assert.ok(button('发送问题').props.disabled);
  input().props.onKeyDown({key: 'Enter', ctrlKey: true, preventDefault() {}});
  await settle(); assert.equal(requests.length, 1);
  call.done([{file_id: 'f', file_name: '文档', chunk_id: 'c', relevance_score: .7}]);
  await settle();
  assert.equal(all(tree, node => node.type === antd.Collapse).length, 1);
  assert.equal(input().props.value, '下一题草稿');
});

test('stop before and after text; retry clears old text and keeps draft', async () => {
  await reset();
  let call = await send('原问题');
  await type('草稿'); button('停止生成').props.onClick(); await settle();
  assert.match(displayed(), /已停止/); assert.match(displayed(), /原问题/);
  assert.equal(all(tree, node => String(node.props?.className || '').includes('qa-message-assistant')).length, 0);
  assert.equal(input().props.value, '草稿');
  button('重新生成').props.onClick(); await settle();
  call = requests.at(-1); assert.equal(call.question, '原问题');
  await emit(call, {type: 'delta', text: '部分回答'});
  button('停止生成').props.onClick(); await settle();
  assert.match(displayed(), /部分回答/); assert.equal(input().props.value, '草稿');
  button('重新生成').props.onClick(); await settle();
  assert.doesNotMatch(displayed(), /部分回答/); assert.match(displayed(), /原问题/);
  assert.equal(input().props.value, '草稿');
  button('停止生成').props.onClick(); await settle();
  assert.doesNotMatch(displayed(), /部分回答/);
});

test('failed and incomplete turns stay visible but are excluded from later history', async () => {
  await reset();
  const first = await send('完成问题'); await complete(first, '完整回答');
  const failed = await send('失败问题');
  await emit(failed, {type: 'delta', text: '失败片段'});
  failed.fail('NETWORK_ERROR'); await settle();
  assert.match(displayed(), /失败片段/);
  const next = await send('新问题');
  assert.deepEqual(JSON.parse(JSON.stringify(next.options.history)), [
    {role: 'user', content: '完成问题'}, {role: 'assistant', content: '完整回答'},
  ]);
  assert.ok(!button('重新生成'), 'a new submitted round makes older retry unavailable');
  await emit(next, {type: 'delta', text: '截断片段'}); next.incomplete('length'); await settle();
  assert.match(displayed(), /截断/); assert.ok(button('重新生成'));
});

test('switching knowledge base aborts the old request and drops late results and draft', async () => {
  await reset();
  const call = await send('旧库问题'); await type('旧草稿');
  await emit(call, {type: 'delta', text: '旧片段'});
  find(antd.Select).props.onChange('kb-b'); await settle();
  assert.ok(call.options.signal.aborted);
  assert.equal(input().props.value, ''); assert.doesNotMatch(displayed(), /旧库问题|旧片段/);
  call.emit({type: 'delta', text: '迟到片段'}); call.done([]); await settle();
  assert.doesNotMatch(displayed(), /迟到片段|旧库问题/);
  const next = await send('新库问题'); assert.equal(next.collection, 'kb-b');
  assert.deepEqual(JSON.parse(JSON.stringify(next.options.history)), []);
});

test('entire visible session retained while request history limited to 20 completed messages', async () => {
  await reset();
  for (let i = 0; i < 12; i++) {
    const call = await send(`问题${i}`); await complete(call, `答案${i}`);
  }
  assert.match(displayed(), /问题0/); assert.match(displayed(), /答案0/);
  const next = await send('最新问题');
  const history = JSON.parse(JSON.stringify(next.options.history));
  assert.equal(history.length, 20);
  assert.deepEqual(history[0], {role: 'user', content: '问题2'});
  assert.deepEqual(history.at(-1), {role: 'assistant', content: '答案11'});
});

test('empty knowledge base preserves original question and supports retry', async () => {
  await reset();
  const call = await send('尚无文档的问题');
  call.fail('COLLECTION_EMPTY', '知识库为空'); await settle();
  assert.match(displayed(), /上传/); assert.match(displayed(), /尚无文档的问题/);
  assert.ok(button('重新生成'));
  props = {...props, isActive: false,
    collections: [{name: 'kb-a', file_count: 1}, {name: 'kb-b', file_count: 1}]};
  dirty = true; await settle();
  props = {...props, isActive: true}; dirty = true; await settle();
  assert.match(displayed(), /尚无文档的问题/); assert.ok(button('重新生成'));
  await type('稍后的草稿');
  button('重新生成').props.onClick(); await settle();
  assert.equal(requests.at(-1).question, '尚无文档的问题');
  assert.equal(input().props.value, '稍后的草稿');
});

test('unknown states, empty and unknown incomplete reasons are non-successful', async () => {
  await reset();
  let call = await send('问题一');
  await emit(call, {type: 'status', stage: 'future'});
  assert.match(displayed(), /正在处理/);
  call.incomplete('empty'); await settle();
  assert.match(displayed(), /回答为空/); assert.ok(button('重新生成'));
  call = await send('问题二');
  await emit(call, {type: 'delta', text: '有限回答'});
  call.incomplete('future'); await settle();
  assert.match(displayed(), /回答未完成/); assert.match(displayed(), /有限回答/);
  assert.equal(all(tree, node => node.type === antd.Collapse).length, 0);
  const next = await send('问题三');
  assert.deepEqual(JSON.parse(JSON.stringify(next.options.history)), []);
});

test('valid new submission invalidates previous retry even if request immediately fails', async () => {
  await reset();
  const first = await send('第一题'); first.fail('NETWORK_ERROR'); await settle();
  assert.ok(button('重新生成'));
  await type('   ');
  input().props.onKeyDown({key: 'Enter', ctrlKey: true, preventDefault() {}}); await settle();
  assert.equal(requests.length, 1); assert.ok(button('重新生成'));
  const second = await send('第二题'); second.fail('COLLECTION_EMPTY'); await settle();
  assert.match(displayed(), /第一题/); assert.match(displayed(), /第二题/);
  assert.equal(all(tree, node => node.type === antd.Button && text(node).includes('重新生成')).length, 1);
  button('重新生成').props.onClick(); await settle();
  assert.equal(requests.at(-1).question, '第二题');
});

test('retry discards failed content immediately and ignores prior attempt late events', async () => {
  await reset();
  const first = await send('重试问题');
  await emit(first, {type: 'delta', text: '旧部分'});
  first.fail('NETWORK_ERROR'); await settle();
  await type('新问题草稿');
  button('重新生成').props.onClick(); await settle();
  const second = requests.at(-1);
  assert.doesNotMatch(displayed(), /旧部分/); assert.equal(input().props.value, '新问题草稿');
  first.emit({type: 'delta', text: '迟到污染'}); first.done(); await settle();
  assert.doesNotMatch(displayed(), /迟到污染|旧部分/);
  second.fail('NETWORK_ERROR'); await settle();
  assert.doesNotMatch(displayed(), /旧部分/); assert.match(displayed(), /重试问题/);
  assert.equal(input().props.value, '新问题草稿');
});

test('switching away keeps generating and restores completed result on return', async () => {
  await reset();
  const call = await send('后台问题');
  props = {...props, isActive: false}; dirty = true; await settle();
  assert.equal(call.options.signal.aborted, false);
  await emit(call, {type: 'delta', text: '后台答案'});
  call.done(); await settle();
  props = {...props, isActive: true}; dirty = true; await settle();
  assert.match(displayed(), /后台问题/); assert.match(displayed(), /后台答案/);
  assert.equal(button('停止生成'), undefined);
});

test('scroll follows at bottom, pauses when scrolled up and resumes at bottom', async () => {
  await reset();
  const call = await send('长回答问题');
  let node = all(tree, element => element.props?.className === 'qa-conversation')[0];
  conversation.scrollTop = 300;
  node.props.onScroll({currentTarget: conversation});
  conversation.scrollHeight = 1200;
  await emit(call, {type: 'delta', text: '第一段'});
  assert.equal(conversation.scrollTop, 300, 'scroll remains where user is reading');
  node = all(tree, element => element.props?.className === 'qa-conversation')[0];
  conversation.scrollTop = 1100;
  node.props.onScroll({currentTarget: conversation});
  conversation.scrollHeight = 1400;
  await emit(call, {type: 'delta', text: '第二段'});
  assert.equal(conversation.scrollTop, 1400, 'scroll follows again after returning to bottom');
});

test('late user stop at deadline marks timeout, not stopped', async () => {
  await reset();
  const originalNow = Date.now;
  let now = originalNow();
  Date.now = () => now;
  try {
    const call = await send('超时问题');
    await emit(call, {type: 'delta', text: '已输出内容'});
    now += 240000;
    button('停止生成').props.onClick(); await settle();
    assert.match(displayed(), /问答超时/); assert.doesNotMatch(displayed(), /已停止/);
    assert.match(displayed(), /已输出内容/); assert.ok(call.options.signal.aborted);
  } finally { Date.now = originalNow; }
});

test('stream error event and local protocol errors retain content and permit retry', async () => {
  for (const viaStream of [true, false]) {
    await reset();
    const call = await send('出错问题');
    await emit(call, {type: 'delta', text: '已显示'});
    if (viaStream) {
      call.emit({type: 'error', code: 'QUERY_TIMEOUT', message: 'timeout'}); call.resolve();
    } else {
      call.fail('STREAM_PROTOCOL_ERROR', '回答数据异常，请重新生成');
    }
    await settle();
    assert.match(displayed(), /已显示/);
    assert.match(displayed(), viaStream ? /问答超时/ : /回答数据异常/);
    assert.ok(button('重新生成'));
    assert.equal(all(tree, node => node.type === antd.Collapse).length, 0);
    const next = await send('继续提问');
    assert.deepEqual(JSON.parse(JSON.stringify(next.options.history)), []);
  }
});

(async () => {
  let passed = 0;
  for (const [name, fn] of tests) { await fn(); console.log(`PASS ${name}`); passed++; }
  console.log(`SUMMARY ${passed}/${tests.length} PASS; real QAPanel with simulated hooks/API; no browser or HTTP`);
})().catch(error => { console.error(error); process.exitCode = 1; });
