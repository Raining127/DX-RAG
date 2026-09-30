const path = require('node:path');
const { spawn } = require('node:child_process');
const { createPreviewServer } = require('./preview-api.cjs');

const port = Number(process.env.PREVIEW_PORT || 3001);
const apiPort = Number(process.env.PREVIEW_API_PORT || 8011);
const api = createPreviewServer();
let frontend;
api.on('error', error => { console.error(error.message); process.exitCode = 1; });
api.listen(apiPort, '127.0.0.1', () => {
  console.log(`Demo preview: http://127.0.0.1:${port} (in-memory fixtures; no live models or storage)`);
  frontend = spawn(process.execPath, [require.resolve('next/dist/bin/next'), 'dev', '-H', '127.0.0.1', '-p', String(port)], {
    cwd: path.resolve(__dirname, '..'), stdio: 'inherit',
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: '1', NEXT_PUBLIC_PREVIEW_MODE: '1',
      NEXT_PUBLIC_API_BASE_URL: `http://127.0.0.1:${apiPort}/api` },
  });
  frontend.on('exit', code => { api.close(); process.exitCode = code || 0; });
});
for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => { frontend?.kill(); api.close(); });
}
