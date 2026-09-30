// Isolated, in-memory demo API. Never connects to production storage or models.
const http = require('node:http');
const { randomUUID } = require('node:crypto');

function createPreviewServer() {
  const handbook = { file_id: randomUUID(), file_name: '产品使用手册.md', size: 18420,
    chunk_count: 12, status: 'SUCCESS', upload_time: '2026-09-30T02:00:00Z' };
  const notes = { file_id: randomUUID(), file_name: '技术架构与开发规范.md', size: 26300,
    chunk_count: 18, status: 'SUCCESS', upload_time: '2026-09-29T06:00:00Z' };
  const collections = new Map([['product-handbook', [handbook]], ['engineering-notes', [notes]], ['empty-workspace', []]]);
  const answer = '## 从资料到可追溯的回答\n\nDX-RAG 将文档整理成可检索的知识，帮助你快速找到答案。\n\n### 建议的使用顺序\n\n1. **选择知识库**：让问题与相关资料处于同一个空间。\n2. **描述具体问题**：补充场景、对象与需要比较的内容。\n3. **核对参考来源**：展开回答下方的来源，查看文件名与相关性分数。\n\n> 本回答由隔离演示 API 提供，仅用于检查界面与交互。\n\n```typescript\nconst question = "这份文档的核心结论是什么？";\n```';
  return http.createServer(async (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    const send = (status, body) => {
      res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify(body));
    };
    const fail = (status, code, message) => send(status, { error: { code, message, details: {} } });
    if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }
    const url = new URL(req.url, 'http://127.0.0.1');
    const pathname = decodeURIComponent(url.pathname);
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const raw = Buffer.concat(chunks);
    let body = {};
    if (raw.length && req.headers['content-type']?.includes('application/json')) {
      try { body = JSON.parse(raw); } catch { fail(422, 'REQUEST_VALIDATION_ERROR', 'Invalid JSON'); return; }
    }
    if (pathname === '/api/health') { send(200, { status: 'ok' }); return; }
    if (pathname === '/api/collections' && req.method === 'GET') {
      send(200, { collections: [...collections].map(([name, files]) => ({ name, file_count: files.length })) }); return;
    }
    if (pathname === '/api/collections' && req.method === 'POST') {
      if (!/^[A-Za-z0-9_-]{1,64}$/.test(body.name || '')) { fail(422, 'INVALID_COLLECTION_NAME', '知识库名称无效'); return; }
      if (collections.has(body.name)) { fail(409, 'COLLECTION_ALREADY_EXISTS', '知识库已存在'); return; }
      collections.set(body.name, []); send(201, { name: body.name, message: 'Created in demo memory' }); return;
    }
    if (pathname.startsWith('/api/collections/')) {
      const name = pathname.slice('/api/collections/'.length);
      if (!collections.has(name)) { fail(404, 'COLLECTION_NOT_FOUND', '知识库不存在'); return; }
      if (req.method === 'DELETE') { collections.delete(name); send(200, { name, message: 'Deleted in demo memory' }); return; }
      if (req.method === 'PUT') {
        if (!/^[A-Za-z0-9_-]{1,64}$/.test(body.new_name || '')) { fail(422, 'INVALID_COLLECTION_NAME', '知识库名称无效'); return; }
        if (collections.has(body.new_name)) { fail(409, 'COLLECTION_ALREADY_EXISTS', '知识库已存在'); return; }
        collections.set(body.new_name, collections.get(name)); collections.delete(name);
        send(200, { old_name: name, new_name: body.new_name, message: 'Renamed in demo memory' }); return;
      }
    }
    if (pathname === '/api/query' && req.method === 'POST') {
      await new Promise(resolve => setTimeout(resolve, 650));
      const files = collections.get(body.collection_name);
      if (!files) { fail(404, 'COLLECTION_NOT_FOUND', '知识库不存在'); return; }
      if (!files.length) { fail(409, 'COLLECTION_EMPTY', '知识库暂无文档'); return; }
      send(200, { answer, query: body.question, collection_name: body.collection_name,
        sources: files.map(file => ({ file_id: file.file_id, file_name: file.file_name,
          chunk_id: randomUUID(), relevance_score: 0.872 })) }); return;
    }
    if (pathname === '/api/upload' && req.method === 'POST') {
      const multipart = raw.toString('utf8');
      const name = multipart.match(/name="collection_name"\r\n\r\n([^\r]+)/)?.[1];
      const fileName = multipart.match(/filename="([^"]+)"/)?.[1];
      const files = collections.get(name);
      if (!files) { fail(404, 'COLLECTION_NOT_FOUND', '知识库不存在'); return; }
      if (!fileName) { fail(422, 'INVALID_FILE_NAME', '文件名无效'); return; }
      if (files.some(file => file.file_name === fileName)) { fail(409, 'FILE_ALREADY_EXISTS', '同名文件已存在'); return; }
      const file = { file_id: randomUUID(), file_name: fileName, size: raw.length,
        chunk_count: 1, status: 'SUCCESS', upload_time: new Date().toISOString() };
      files.push(file);
      send(200, { status: 'SUCCESS', message: 'Demo only: no parsing or embedding performed',
        file_id: file.file_id, file_name: fileName, chunks: 1, collection_name: name, warnings: [] }); return;
    }
    if (pathname.startsWith('/api/files')) {
      const name = url.searchParams.get('collection_name');
      const files = collections.get(name);
      if (!files) { fail(404, 'COLLECTION_NOT_FOUND', '知识库不存在'); return; }
      if (pathname === '/api/files') { send(200, { collection_name: name, files }); return; }
      const id = pathname.split('/')[3];
      const file = files.find(item => item.file_id === id);
      if (!file) { fail(404, 'FILE_NOT_FOUND', '文件不存在'); return; }
      if (pathname.endsWith('/preview')) {
        const content = '这是隔离演示文件的预览。所有改动仅保存在当前预览进程的内存中，重启后重置。';
        send(200, { file_id: id, file_name: file.file_name, collection_name: name,
          content, preview_chars: content.length, total_chars: content.length }); return;
      }
      if (req.method === 'DELETE') {
        collections.set(name, files.filter(item => item.file_id !== id));
        send(200, { file_name: file.file_name, collection_name: name, message: 'Deleted in demo memory' }); return;
      }
    }
    fail(404, 'NOT_FOUND', 'Demo endpoint not found');
  });
}

module.exports = { createPreviewServer };
