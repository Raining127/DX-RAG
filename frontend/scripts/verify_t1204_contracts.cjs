// T1204 deterministic component contract probe; no browser or new framework.
// Uses installed TypeScript/React/Ant Design and Node's built-in assertions.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const react = require('react');
const antd = require('antd');
const root = path.resolve(__dirname, '..');
let states = [];
let cursor = 0;
let requests = 0;
const hooks = {
  ...react,
  useState(initial) {
    const index = cursor++;
    if (!(index in states)) states[index] = initial;
    return [states[index], value => { states[index] = value; }];
  },
  useRef: value => ({ current: value }),
  useEffect: () => {},
  useCallback: callback => callback,
};
const cache = new Map();
function load(relative) {
  if (cache.has(relative)) return cache.get(relative);
  const source = fs.readFileSync(path.join(root, relative), 'utf8');
  const exports = {};
  const compiled = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX,
    esModuleInterop: true, target: ts.ScriptTarget.ES2020,
  } }).outputText;
  vm.runInNewContext(compiled, { exports, require(name) {
    if (name === 'react') return hooks;
    if (name === '@/lib/api-client') return {
      ApiError: class extends Error {},
      uploadFile() { requests++; throw Error('Unexpected request'); },
    };
    if (name.startsWith('@/')) return load(name.slice(2) + '.ts');
    return require(name);
  } }, { filename: relative });
  cache.set(relative, exports);
  return exports;
}
function find(element, type) {
  if (!element || typeof element !== 'object') return undefined;
  if (element.type === type) return element;
  for (const child of react.Children.toArray(element.props?.children)) {
    const match = find(child, type);
    if (match) return match;
  }
}
const Component = load('components/FileUpload.tsx').default;
function render() {
  cursor = 0;
  return Component({ collections: [{name: 'audit-kb', file_count: 0}],
    collectionState: 'ready', collectionError: '', collectionMutation: null,
    onRetryCollections() {} });
}
let passed = 0;
for (const [size, rejected] of [[51 * 1024 ** 2, true], [50 * 1024 ** 2, false]]) {
  states = [];
  requests = 0;
  const dragger = find(render(), antd.Upload.Dragger);
  assert.ok(dragger);
  const result = dragger.props.beforeUpload({name: 'audit.txt', size});
  assert.equal(result, rejected ? antd.Upload.LIST_IGNORE : true);
  assert.equal(requests, 0);
  if (rejected) {
    const alert = find(render(), antd.Alert);
    assert.equal(alert.props.type, 'error');
    assert.equal(alert.props.description, '文件大小超过 50MB 限制。');
  }
  passed++;
  console.log(JSON.stringify({bytes: size, rejected, uploadCalls: requests, pass: true}));
}
console.log(`SUMMARY: ${passed}/${passed} PASS; DETERMINISTIC component handler/state; NOT browser upload`);
