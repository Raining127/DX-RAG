// Real QAPanel + real streaming API/decoder, with a controlled fetch and
// simulated React hooks. No browser, HTTP socket, backend, or model is used.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const React = require('react');
const antd = require('antd');
const root = path.resolve(__dirname, '..');
const modules = new Map();
const cells = [];
let cursor = 0, dirty = true, effects = [], tree, calls = [], httpReplies = [];
let props;
const encoder = new TextEncoder();
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
      const previous = cells[i]; cells[i] = {deps};
      effects.push(() => { previous?.cleanup?.(); cells[i].cleanup = callback(); });
    }
  },
};

// Each request returns a browser-compatible stream whose chunks are released
// by the test. Its abort observer deliberately models fetch cancellation.
function controlledFetch(url, init) {
  let controller;
  const body = new ReadableStream({ start(value) { controller = value; } });
  const call = {url, init, body: JSON.parse(init.body), aborted: false,
    push(chunk) { controller.enqueue(typeof chunk === 'string' ? encoder.encode(chunk) : chunk); },
    close() { controller.close(); },
  };
  init.signal.addEventListener('abort', () => {
    call.aborted = true;
    try { controller.error(new DOMException('aborted', 'AbortError')); } catch {}
  }, {once: true});
  calls.push(call);
  const reply = httpReplies.shift();
  if (reply) return Promise.resolve(new Response(JSON.stringify({error: {
    code: reply.code, message: reply.message, details: {},
  }}), {status: reply.status, headers: {'Content-Type': 'application/json'}}));
  return Promise.resolve(new Response(body, {headers: {'Content-Type': 'text/event-stream'}}));
}

function load(relative) {
  if (modules.has(relative)) return modules.get(relative);
  const exports = {};
  const source = fs.readFileSync(path.join(root, relative), 'utf8');
  const compiled = ts.transpileModule(source, {compilerOptions: {
    module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX,
    esModuleInterop: true, target: ts.ScriptTarget.ES2020,
  }}).outputText;
  vm.runInNewContext(compiled, {
    exports, AbortController, Date, console, setTimeout, clearTimeout, TextDecoder,
    fetch: (...args) => controlledFetch(...args), process: {env: {}},
    require(name) {
      if (name === 'react') return hooks;
      if (name === 'react-markdown') return {__esModule: true, default: 'markdown'};
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
const QAPanel = load('components/QAPanel.tsx').default;
function all(element, predicate) {
  if (!element || typeof element !== 'object') return [];
  return [...(predicate(element) ? [element] : []),
    ...React.Children.toArray(element.props?.children).flatMap(child => all(child, predicate))];
}
const text = node => typeof node === 'string' || typeof node === 'number' ? String(node)
  : node && typeof node === 'object' ? [node.props?.message, node.props?.description,
      ...React.Children.toArray(node.props?.children)].map(text).join('') : '';
const displayed = () => text(tree);
const button = label => all(tree, n => n.type === antd.Button && text(n).includes(label))[0];
const input = () => all(tree, n => n.type === antd.Input.TextArea)[0];
const sources = () => all(tree, n => n.type === antd.Collapse);
const event = (type, value) => `event: ${type}\ndata: ${JSON.stringify(value)}\n\n`;

async function settle() {
  for (let rounds = 0; rounds < 50; rounds++) {
    if (dirty) { dirty = false; cursor = 0; tree = QAPanel(props); }
    const queue = effects; effects = []; queue.forEach(effect => effect());
    await new Promise(resolve => setImmediate(resolve));
    if (!dirty && !effects.length) return;
  }
  throw new Error('Hook scheduler did not settle');
}
async function reset() {
  for (const value of cells) value?.cleanup?.();
  await new Promise(resolve => setImmediate(resolve));
  cells.length = 0; effects = []; dirty = true; calls = []; httpReplies = [];
  props = {collections: [{name: 'alpha', file_count: 1}, {name: 'beta', file_count: 1}],
    collectionState: 'ready', collectionError: '', onRetryCollections() {}};
  await settle();
}
async function type(value) { input().props.onChange({target: {value}}); await settle(); }
async function send(value) {
  await type(value); button('发送问题').props.onClick(); await settle(); return calls.at(-1);
}
async function push(call, value) { call.push(value); await settle(); }
async function complete(call, answer, refs = []) {
  await push(call, event('delta', {text: answer}) + event('done', {sources: refs}));
}

const tests = [];
const test = (name, fn) => tests.push([name, fn]);

test('split UTF-8 reaches component incrementally; sources appear only at done', async () => {
  await reset(); const call = await send('哪里有资料');
  assert.equal(call.body.collection_name, 'alpha');
  await push(call, event('status', {stage: 'generating'}));
  assert.match(displayed(), /正在生成回答/);
  const bytes = encoder.encode(event('delta', {text: '文档🙂'}));
  for (const byte of bytes) call.push(Uint8Array.of(byte));
  await settle(); assert.match(displayed(), /文档🙂/); assert.equal(sources().length, 0);
  await push(call, event('done', {sources: [{file_id:'f',file_name:'文档',chunk_id:'c',relevance_score:.7}]}));
  assert.equal(sources().length, 1); assert.match(displayed(), /回答完成/);
});

test('partial stop aborts reader; retry replaces old text and preserves draft', async () => {
  await reset(); const first = await send('停止问题');
  await push(first, event('delta', {text: '旧内容'})); await type('下题草稿');
  button('停止生成').props.onClick(); await settle();
  assert.ok(first.aborted); assert.match(displayed(), /已停止/); assert.match(displayed(), /旧内容/);
  button('重新生成').props.onClick(); await settle();
  const next = calls.at(-1); assert.equal(next.body.question, '停止问题');
  assert.equal(input().props.value, '下题草稿'); assert.doesNotMatch(displayed(), /旧内容/);
  await push(next, event('incomplete', {reason: 'empty'}));
  assert.match(displayed(), /回答为空/); assert.doesNotMatch(displayed(), /旧内容/);
});

test('partial protocol error is visible and does not enter later history', async () => {
  await reset(); const first = await send('成功问题'); await complete(first, '成功答案');
  const second = await send('失败问题');
  await push(second, event('delta', {text:'部分回答'}) + 'event: done\ndata: {"sources":null}\n\n');
  assert.match(displayed(), /部分回答/); assert.match(displayed(), /回答数据异常/);
  assert.equal(sources().length, 0); assert.ok(button('重新生成'));
  const third = await send('下一问题');
  assert.deepEqual(third.body.history, [
    {role:'user', content:'成功问题'}, {role:'assistant', content:'成功答案'},
  ]);
  assert.equal(button('重新生成'), undefined);
});

test('length and empty incomplete events remain retryable and outside history', async () => {
  await reset(); const first = await send('截断');
  await push(first, event('delta',{text:'部分'}) + event('incomplete',{reason:'length'}));
  assert.match(displayed(), /回答已截断/); assert.ok(button('重新生成'));
  const second = await send('空回答'); await push(second, event('incomplete',{reason:'empty'}));
  assert.match(displayed(), /回答为空/); assert.ok(button('重新生成'));
  const third = await send('后续'); assert.deepEqual(third.body.history, []);
});

test('EOF and stream error preserve content without sources', async () => {
  for (const terminal of ['', event('error',{code:'LLM_UNAVAILABLE',message:'不可用'})]) {
    await reset(); const call = await send('连接问题');
    await push(call, event('delta',{text:'部分正文'}) + terminal);
    if (!terminal) { call.close(); await settle(); }
    assert.match(displayed(), /部分正文/); assert.ok(button('重新生成'));
    assert.match(displayed(), terminal ? /暂时不可用/ : /连接已中断/);
    assert.equal(sources().length, 0);
  }
});

test('after deadline all unaccepted terminal kinds and EOF become timeout', async () => {
  const originalNow = Date.now; let now = originalNow(); Date.now = () => now;
  try {
    for (const terminal of [event('done',{sources:[]}), event('incomplete',{reason:'length'}),
      event('error',{code:'LLM_AUTH_FAILED',message:'auth'}), '']) {
      await reset(); const call = await send('迟到问题');
      await push(call, event('delta',{text:'已收到'})); now += 240000;
      if (terminal) await push(call, terminal); else { call.close(); await settle(); }
      assert.match(displayed(), /问答超时/); assert.match(displayed(), /已收到/);
      assert.equal(sources().length, 0); assert.ok(button('重新生成'));
    }
  } finally { Date.now = originalNow; }
});

test('accepted completion survives later clock advance and next turn includes it', async () => {
  const originalNow = Date.now; let now = originalNow(); Date.now = () => now;
  try {
    await reset(); const first = await send('完成问题');
    const lateStop = button('停止生成').props.onClick;
    await complete(first,'完整答案');
    assert.equal(sources().length, 0, 'empty sources must not render an empty source list');
    now += 240000; lateStop(); await settle(); assert.match(displayed(), /回答完成/);
    assert.doesNotMatch(displayed(), /问答超时/);
    const next = await send('后续问题');
    assert.deepEqual(next.body.history, [
      {role:'user',content:'完成问题'}, {role:'assistant',content:'完整答案'},
    ]);
  } finally { Date.now = originalNow; }
});

test('after deadline user stop is timeout and retains the partial answer', async () => {
  const originalNow = Date.now; let now = originalNow(); Date.now = () => now;
  try {
    await reset(); const call = await send('停止超时');
    await push(call, event('delta',{text:'已经输出'})); now += 240000;
    button('停止生成').props.onClick(); await settle();
    assert.ok(call.aborted); assert.match(displayed(), /问答超时/);
    assert.doesNotMatch(displayed(), /已停止/); assert.match(displayed(), /已经输出/);
    const next = await send('继续'); assert.deepEqual(next.body.history, []);
  } finally { Date.now = originalNow; }
});

test('switching collection aborts stream and removes old contents', async () => {
  await reset(); const call = await send('旧库问题'); await push(call,event('delta',{text:'旧部分'}));
  await type('草稿'); all(tree,n => n.type === antd.Select)[0].props.onChange('beta'); await settle();
  assert.ok(call.aborted); assert.equal(input().props.value,'');
  assert.doesNotMatch(displayed(),/旧库问题|旧部分/);
  const next = await send('新库问题'); assert.equal(next.body.collection_name,'beta');
  assert.deepEqual(next.body.history,[]);
});

test('empty collection question survives navigation/upload and retries same turn', async () => {
  await reset();
  props = {...props, collections:[{name:'alpha',file_count:0},{name:'beta',file_count:1}]};
  dirty = true; await settle();
  httpReplies.push({status:409, code:'COLLECTION_EMPTY', message:'知识库暂无文档'});
  const first = await send('空库问题');
  assert.equal(first.body.question, '空库问题'); assert.match(displayed(), /请先上传文件/);
  assert.ok(button('重新生成'));
  await type('下一题草稿');
  props = {...props, isActive:false}; dirty = true; await settle();
  props = {...props, isActive:true, collections:[{name:'alpha',file_count:1},{name:'beta',file_count:1}]};
  dirty = true; await settle();
  assert.match(displayed(), /空库问题/); assert.equal(input().props.value, '下一题草稿');
  button('重新生成').props.onClick(); await settle();
  const retry = calls.at(-1); assert.equal(retry.body.question, '空库问题');
  assert.deepEqual(retry.body.history, []); assert.equal(input().props.value, '下一题草稿');
  await complete(retry, '新文档答案'); assert.match(displayed(), /回答完成/);
});

test('valid new submission invalidates older retry even when new HTTP request fails', async () => {
  await reset(); const first = await send('旧失败问题');
  await push(first, event('delta',{text:'旧部分'}) + event('error',{code:'LLM_UNAVAILABLE', message:'不可用'}));
  assert.ok(button('重新生成'));
  httpReplies.push({status:409, code:'COLLECTION_EMPTY', message:'知识库暂无文档'});
  const second = await send('新失败问题');
  assert.equal(second.body.question,'新失败问题'); assert.match(displayed(), /旧失败问题/);
  assert.match(displayed(), /旧部分/); assert.match(displayed(), /新失败问题/);
  assert.equal(all(tree,n => n.type === antd.Button && text(n).includes('重新生成')).length, 1);
  button('重新生成').props.onClick(); await settle();
  assert.equal(calls.at(-1).body.question, '新失败问题');
  assert.deepEqual(calls.at(-1).body.history, []);
});

(async () => {
  let passed = 0;
  for (const [name, fn] of tests) { await fn(); console.log(`PASS ${name}`); passed++; }
  await reset();
  console.log(`SUMMARY ${passed}/${tests.length} PASS; real component and SSE client with simulated hooks/fetch; no browser or HTTP`);
})().catch(error => { console.error(error); process.exitCode = 1; });
