// Exercise the preview server through in-memory request/response objects.
// No listening socket, production storage, or model service is used.
const assert = require('node:assert/strict');
const { Readable } = require('node:stream');
const { EventEmitter, once } = require('node:events');
const { createPreviewServer } = require('./preview-api.cjs');

const server = createPreviewServer();

function request(path, body, disconnectAfterDelta = false) {
  const req = Readable.from([Buffer.from(JSON.stringify(body))]);
  req.method = 'POST';
  req.url = path;
  req.headers = { 'content-type': 'application/json' };

  const res = new EventEmitter();
  res.headers = {};
  res.chunks = [];
  res.setHeader = (key, value) => { res.headers[key] = value; };
  res.writeHead = (status, headers) => { res.status = status; Object.assign(res.headers, headers); };
  res.write = chunk => {
    res.chunks.push(chunk);
    if (disconnectAfterDelta && chunk.startsWith('event: delta')) res.emit('close');
    return true;
  };
  res.end = chunk => {
    if (chunk) res.chunks.push(chunk);
    res.emit('finish');
    res.emit('close');
  };
  server.emit('request', req, res);
  return res;
}

async function main() {
  const payload = { question: '隔离测试问题', collection_name: 'product-handbook' };

  const empty = request('/api/query/stream', { ...payload, collection_name: 'empty-workspace' });
  await once(empty, 'finish');
  assert.equal(empty.status, 409);
  assert.equal(JSON.parse(empty.chunks.join('')).error.code, 'COLLECTION_EMPTY');
  console.log('PASS empty collection returns JSON error before streaming');

  const missing = request('/api/query/stream', { ...payload, collection_name: 'missing' });
  await once(missing, 'finish');
  assert.equal(missing.status, 404);
  assert.equal(JSON.parse(missing.chunks.join('')).error.code, 'COLLECTION_NOT_FOUND');
  console.log('PASS missing collection returns JSON error before streaming');

  const stream = request('/api/query/stream', payload);
  await once(stream, 'finish');
  assert.equal(stream.status, 200);
  assert.match(stream.headers['Content-Type'], /^text\/event-stream/);
  const events = stream.chunks.map(chunk => {
    const [kind, data] = chunk.trim().split('\n');
    return { type: kind.slice(7), data: JSON.parse(data.slice(6)) };
  });
  assert.deepEqual(events.slice(0, 2).map(event => event.data.stage), ['retrieving', 'generating']);
  const deltas = events.filter(event => event.type === 'delta');
  assert.ok(deltas.length > 1, 'answer must arrive in multiple deltas');
  assert.equal(events.at(-1).type, 'done');
  const [source] = events.at(-1).data.sources;
  assert.equal(typeof source.file_id, 'string');
  assert.equal(typeof source.file_name, 'string');
  assert.equal(typeof source.chunk_id, 'string');
  assert.equal(typeof source.relevance_score, 'number');
  console.log('PASS ordered status, multiple deltas and sources');

  const stopped = request('/api/query/stream', payload, true);
  await once(stopped, 'close');
  const count = stopped.chunks.length;
  await new Promise(resolve => setTimeout(resolve, 250));
  assert.equal(stopped.chunks.length, count);
  assert.ok(!stopped.chunks.some(chunk => chunk.startsWith('event: done')));
  console.log('PASS disconnected response stops future events');

  const legacy = request('/api/query', payload);
  await once(legacy, 'finish');
  assert.equal(legacy.status, 200);
  const result = JSON.parse(legacy.chunks.join(''));
  assert.equal(result.answer, deltas.map(event => event.data.text).join(''));
  assert.equal(result.query, payload.question);
  assert.equal(result.collection_name, payload.collection_name);
  console.log('PASS legacy JSON answer remains available');
  console.log('SUMMARY 5/5 PASS; in-memory request/response, no network or browser');
}

main().catch(error => { console.error(error); process.exitCode = 1; });
