// Controlled SSE/API contract checks. Uses Node's fetch/stream primitives and
// the installed TypeScript compiler; it does not contact a backend or model.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');
const ts = require('typescript');

const file = path.resolve(__dirname, '../lib/api-client.ts');
const compiled = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
}).outputText;
const loaded = new Module(file, module);
loaded.filename = file;
loaded.paths = module.paths;
loaded._compile(compiled, file);
const { streamQueryQA, queryQA } = loaded.exports;

const encoder = new TextEncoder();
const frame = (type, data, newline = '\n') =>
  `event: ${type}${newline}data: ${JSON.stringify(data)}${newline}${newline}`;
const success = (text = '回答', sources = []) =>
  frame('delta', { text }) + frame('done', { sources });
const source = { file_id: 'file', file_name: '文档', chunk_id: 'chunk', relevance_score: 0.7 };
const responseFrom = chunks => new Response(new ReadableStream({
  start(controller) {
    for (const chunk of chunks) controller.enqueue(typeof chunk === 'string' ? encoder.encode(chunk) : chunk);
    controller.close();
  },
}), { status: 200, headers: { 'Content-Type': 'text/event-stream' } });
const runStream = async (chunks, extraOptions = {}) => {
  const events = [];
  global.fetch = async () => responseFrom(chunks);
  await streamQueryQA('问题', '知识库', { ...extraOptions, onEvent: event => events.push(event) });
  return events;
};
const runFailure = async (chunks, code, extraOptions = {}) => {
  const events = [];
  global.fetch = async () => responseFrom(chunks);
  await assert.rejects(
    streamQueryQA('问题', '知识库', { ...extraOptions, onEvent: event => events.push(event) }),
    error => error.code === code,
  );
  return events;
};

const tests = [];
const test = (name, fn) => tests.push([name, fn]);

test('POST request body and first valid terminal', async () => {
  let captured;
  global.fetch = async (url, init) => {
    captured = { url, init };
    return responseFrom([frame('status', { stage: 'retrieving' }) + success('回答', [source]) + frame('error', {code: 'LATE', message: 'late'})]);
  };
  const events = [];
  await streamQueryQA('问题', '知识库', { topK: 3, history: [{role: 'user', content: '之前'}], onEvent: e => events.push(e) });
  assert.ok(String(captured.url).endsWith('/query/stream'));
  assert.equal(captured.init.method, 'POST');
  assert.deepEqual(JSON.parse(captured.init.body), { question: '问题', collection_name: '知识库', top_k: 3, history: [{role: 'user', content: '之前'}] });
  assert.deepEqual(events.map(e => e.type), ['status', 'delta', 'done']);
  assert.equal(events[2].sources[0].file_id, 'file');
});

test('invalid known event after terminal in the same chunk is ignored', async () => {
  const events = await runStream([success('完成') + 'event: delta\ndata: not-json\n\n']);
  assert.deepEqual(events.map(e => e.type), ['delta', 'done']);
});

test('UTF-8 split across every byte, frames split and combined', async () => {
  const bytes = encoder.encode(frame('status', {stage: 'generating'}) + success('汉🙂字'));
  const events = await runStream(Array.from(bytes, byte => Uint8Array.of(byte)));
  assert.deepEqual(events.map(e => e.type), ['status', 'delta', 'done']);
  assert.equal(events[1].text, '汉🙂字');
});

test('CRLF, bare CR, comments, multiline data and split CRLF', async () => {
  const chunks = [': heartbeat\r', '\nevent: status\rdata: {"stage":\rdata: "future"}\r\r',
    'event: delta\r\ndata: {"text":"甲"}\r', '\n\r', '\nevent: done\rdata: {"sources":[]}\r\r'];
  const events = await runStream(chunks);
  assert.deepEqual(events.map(e => e.type), ['status', 'delta', 'done']);
  assert.equal(events[0].stage, 'future');
  assert.equal(events[1].text, '甲');
});

test('unknown events ignored, extra fields accepted', async () => {
  const events = await runStream(['event: future\ndata: not-json\n\n' +
    frame('status', {stage: 'later', extra: 7}) + frame('delta', {text: 'x', extra: true}) +
    frame('done', {sources: [{...source, extra: true}], extra: 42})]);
  assert.deepEqual(events.map(e => e.type), ['status', 'delta', 'done']);
  assert.equal(events[0].stage, 'later');
});

test('unknown incomplete reason and stream errors are terminal', async () => {
  let events = await runStream([frame('incomplete', {reason: 'future'}) + success()]);
  assert.deepEqual(events.map(e => e.type), ['incomplete']);
  assert.equal(events[0].reason, 'future');
  events = await runStream([frame('error', {code: 'QUERY_TIMEOUT', message: '超时'}) + success()]);
  assert.deepEqual(events.map(e => e.type), ['error']);
  assert.equal(events[0].code, 'QUERY_TIMEOUT');
  events = await runStream([frame('status', {stage: ''}) + frame('incomplete', {reason: ''})]);
  assert.equal(events[0].stage, '');
  assert.equal(events[1].reason, '');
});

test('invalid known event JSON, missing and wrong fields are protocol errors', async () => {
  const invalid = [
    'event: status\ndata: {\n\n', frame('status', {}), frame('status', {stage: 1}),
    frame('delta', {}), frame('delta', {text: null}), frame('done', {}),
    frame('done', {sources: null}), frame('done', {sources: [{...source, relevance_score: '0.7'}]}),
    frame('done', {sources: [{...source, file_id: null}]}), frame('incomplete', {}),
    frame('incomplete', {reason: 1}), frame('error', {code: 'E'}), frame('error', {code: 1, message: 'x'}),
  ];
  for (const bad of invalid) await runFailure([frame('delta', {text: '已经输出'}) + bad], 'STREAM_PROTOCOL_ERROR');
});

test('blank answer followed by done fails using ECMAScript trim rules', async () => {
  for (const value of ['', ' \n\t', '\ufeff\u00a0\u2028']) {
    await runFailure([frame('delta', {text: value}) + frame('done', {sources: []})], 'STREAM_PROTOCOL_ERROR');
  }
  const events = await runStream([success('\u0085')]);
  assert.equal(events[0].text, '\u0085');
});

test('EOF before terminal including partial terminal frame is interrupted', async () => {
  for (const tail of ['', 'event: done\ndata: {"sources":[]}', 'event: done\ndata: {"sources":[]}\n']) {
    const events = await runFailure([frame('delta', {text: '部分'}) + tail], 'STREAM_INTERRUPTED');
    assert.equal(events[0].text, '部分');
  }
  await runFailure(['event: future\ndata: {}\n\n'], 'STREAM_INTERRUPTED');
});

test('HTTP error JSON is preserved, including QUERY_TIMEOUT', async () => {
  for (const [status, code] of [[409, 'COLLECTION_EMPTY'], [504, 'QUERY_TIMEOUT']]) {
    global.fetch = async () => new Response(JSON.stringify({error: {code, message: '提示', details: {}}}), {
      status, headers: {'Content-Type': 'application/json'},
    });
    await assert.rejects(streamQueryQA('问题', '库', {onEvent() {}}), error => error.code === code && error.status === status);
  }
});

test('network failure is distinguishable from cancellation', async () => {
  global.fetch = async () => { throw new TypeError('network disconnected'); };
  await assert.rejects(streamQueryQA('问题', '库', {onEvent() {}}), error => error.code === 'NETWORK_ERROR');
  const controller = new AbortController();
  controller.abort();
  await assert.rejects(streamQueryQA('问题', '库', {signal: controller.signal, onEvent() {}}), error => error.code === 'STREAM_CANCELLED');
});

test('stream read failure reports interruption and retains prior deltas', async () => {
  global.fetch = async () => {
    let count = 0;
    return new Response(new ReadableStream({
      pull(stream) {
        if (count++ === 0) stream.enqueue(encoder.encode(frame('delta', {text: '部分'})));
        else stream.error(new TypeError('connection lost'));
      },
    }), {headers: {'Content-Type': 'text/event-stream'}});
  };
  const events = [];
  await assert.rejects(streamQueryQA('问题', '库', {onEvent(e) { events.push(e); }}),
    error => error.code === 'STREAM_INTERRUPTED');
  assert.deepEqual(events.map(e => e.type), ['delta']);
  assert.equal(events[0].text, '部分');
});

test('cancelled request ignores a fetch result that arrives late', async () => {
  let resolveFetch;
  global.fetch = () => new Promise(resolve => { resolveFetch = resolve; });
  const controller = new AbortController();
  const events = [];
  const pending = streamQueryQA('问题', '库', {signal: controller.signal, onEvent(e) { events.push(e); }});
  controller.abort();
  await assert.rejects(pending, error => error.code === 'STREAM_CANCELLED');
  resolveFetch(responseFrom([success()]));
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(events, []);
});

test('cancelled request ignores a read result that arrives late', async () => {
  let resolveRead;
  let calls = 0;
  global.fetch = async () => ({ok: true, body: {getReader() { return {
    read() {
      if (calls++ === 0) return Promise.resolve({done: false, value: encoder.encode(frame('delta', {text: '先前'}))});
      return new Promise(resolve => { resolveRead = resolve; });
    },
    cancel() { return Promise.resolve(); },
  }; }}});
  const controller = new AbortController();
  const events = [];
  const pending = streamQueryQA('问题', '库', {signal: controller.signal, onEvent(e) { events.push(e); }});
  while (!resolveRead) await new Promise(resolve => setImmediate(resolve));
  controller.abort();
  await assert.rejects(pending, error => error.code === 'STREAM_CANCELLED');
  resolveRead({done: false, value: encoder.encode(success('迟到'))});
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(events.map(e => e.type), ['delta']);
  assert.equal(events[0].text, '先前');
});

test('abort during stream read preserves already delivered events', async () => {
  const controller = new AbortController();
  global.fetch = async (_url, init) => new Response(new ReadableStream({
    start(stream) {
      stream.enqueue(encoder.encode(frame('delta', {text: '部分'})));
      init.signal.addEventListener('abort', () => stream.error(new DOMException('cancelled', 'AbortError')));
    },
  }), {headers: {'Content-Type': 'text/event-stream'}});
  const events = [];
  await assert.rejects(streamQueryQA('问题', '库', {signal: controller.signal, onEvent(e) {
    events.push(e);
    if (e.type === 'delta') controller.abort();
  }}), error => error.code === 'STREAM_CANCELLED');
  assert.equal(events[0].text, '部分');
});

test('local deadline aborts a blocked fetch', async () => {
  let aborted = false;
  global.fetch = (_url, init) => new Promise((_resolve, reject) => {
    init.signal.addEventListener('abort', () => {
      aborted = true;
      reject(new DOMException('cancelled', 'AbortError'));
    });
  });
  await assert.rejects(streamQueryQA('问题', '库', {
    startedAt: Date.now() - 240000 + 25, onEvent() {},
  }), error => error.code === 'QUERY_TIMEOUT');
  assert.equal(aborted, true);
});

test('local deadline also aborts a blocked body after a delta', async () => {
  let aborted = false;
  global.fetch = async (_url, init) => new Response(new ReadableStream({
    start(stream) {
      stream.enqueue(encoder.encode(frame('delta', {text: '已有内容'})));
      init.signal.addEventListener('abort', () => {
        aborted = true;
        stream.error(new DOMException('cancelled', 'AbortError'));
      });
    },
  }), {headers: {'Content-Type': 'text/event-stream'}});
  const events = [];
  await assert.rejects(streamQueryQA('问题', '库', {
    startedAt: Date.now() - 240000 + 50, onEvent(e) { events.push(e); },
  }), error => error.code === 'QUERY_TIMEOUT');
  assert.equal(aborted, true);
  assert.deepEqual(events.map(e => e.type), ['delta']);
  assert.equal(events[0].text, '已有内容');
});

test('local deadline interrupts a blocked HTTP error body', async () => {
  let resolveJson;
  let requestSignal;
  global.fetch = async (_url, init) => {
    requestSignal = init.signal;
    return {ok: false, status: 409, json: () => new Promise(resolve => { resolveJson = resolve; })};
  };
  const events = [];
  await assert.rejects(streamQueryQA('问题', '库', {
    startedAt: Date.now() - 240000 + 25, onEvent(e) { events.push(e); },
  }), error => error.code === 'QUERY_TIMEOUT');
  assert.equal(requestSignal.aborted, true);
  resolveJson({error: {code: 'COLLECTION_EMPTY', message: 'empty', details: {}}});
  await new Promise(resolve => setImmediate(resolve));
  assert.deepEqual(events, []);
});

test('actual deadline wins over a late terminal even if timer has not run', async () => {
  const originalNow = Date.now;
  let now = originalNow();
  Date.now = () => now;
  try {
    global.fetch = async () => responseFrom([frame('delta', {text: '部分'}), frame('done', {sources: []})]);
    const events = [];
    await assert.rejects(streamQueryQA('问题', '库', {startedAt: now, onEvent(e) {
      events.push(e);
      if (e.type === 'delta') now += 240001;
    }}), error => error.code === 'QUERY_TIMEOUT');
    assert.deepEqual(events.map(e => e.type), ['delta']);
  } finally {
    Date.now = originalNow;
  }
});

test('deadline wins over late user stop; accepted terminal survives late stop', async () => {
  const originalNow = Date.now;
  let now = originalNow();
  Date.now = () => now;
  try {
    const firstController = new AbortController();
    global.fetch = async () => responseFrom([frame('delta', {text: '部分'})]);
    await assert.rejects(streamQueryQA('问题', '库', {startedAt: now, signal: firstController.signal, onEvent(e) {
      if (e.type === 'delta') { now += 240001; firstController.abort(); }
    }}), error => error.code === 'QUERY_TIMEOUT');

    const secondController = new AbortController();
    global.fetch = async () => responseFrom([success('完整')]);
    const events = [];
    await streamQueryQA('问题', '库', {startedAt: now, signal: secondController.signal, onEvent(e) {
      events.push(e);
      if (e.type === 'done') { now += 240001; secondController.abort(); }
    }});
    assert.deepEqual(events.map(e => e.type), ['delta', 'done']);
  } finally {
    Date.now = originalNow;
  }
});

test('old JSON queryQA still preserves its contract', async () => {
  let captured;
  global.fetch = async (url, init) => {
    captured = {url, init};
    return new Response(JSON.stringify({answer: '旧回答', sources: [], query: '问题', collection_name: '库'}), {
      headers: {'Content-Type': 'application/json'},
    });
  };
  const result = await queryQA('问题', '库');
  assert.ok(String(captured.url).endsWith('/query'));
  assert.equal(result.answer, '旧回答');
});

(async () => {
  const originalFetch = global.fetch;
  try {
    let passed = 0;
    for (const [name, fn] of tests) {
      await fn();
      console.log(`PASS ${name}`);
      passed++;
    }
    console.log(`SUMMARY: ${passed}/${tests.length} PASS; controlled Node streams and fetch, not real browser/HTTP`);
  } finally {
    global.fetch = originalFetch;
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
