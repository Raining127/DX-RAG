// Browser UI regression against the explicitly isolated preview API.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.PREVIEW_BASE_URL || 'http://127.0.0.1:3001';
const out = process.env.UI_EVIDENCE_DIR || path.resolve(__dirname, '../../tmp/frontend-ui');
const passed = [];
const requests = [];
const pageErrors = [];
const consoleMessages = [];
const pass = name => { passed.push(name); console.log('PASS ' + name); };

(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM_PATH || undefined });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
    page.on('pageerror', error => pageErrors.push(error.message));
    page.on('console', message => { if (['error', 'warning'].includes(message.type())) consoleMessages.push(message.text()); });
    page.on('request', request => { if (new URL(request.url()).pathname === '/api/query') requests.push(request.postDataJSON()); });
    await page.goto(base, { timeout: 60000 });
    await page.waitForLoadState('networkidle');
    const input = page.getByRole('textbox', { name: '输入问题' });
    const nav = async name => { await page.getByRole('menuitem', { name, exact: true }).click(); await page.locator('#panel-title').filter({ hasText: name }).waitFor(); };
    const screenshot = name => page.screenshot({ path: path.join(out, name + '.png'), fullPage: true, animations: 'disabled' });
    const layout = async name => {
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth), name + ': no horizontal overflow');
      const rect = await page.locator('.qa-composer').boundingBox();
      assert.ok(rect.y >= 0 && rect.y + rect.height <= page.viewportSize().height + 1, name + ': composer inside viewport');
      pass(name + ': no overflow; composer visible');
    };
    const choose = async name => {
      await page.locator('.qa-panel .ant-select-selector').click();
      await page.locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option').filter({ hasText: name }).click();
    };
    const send = async (question, keyboard = false) => {
      await input.fill(question);
      if (keyboard) await input.press('Control+Enter');
      else await page.getByRole('button', { name: '发送问题' }).click();
      await page.locator('.qa-conversation[data-state="success"]').waitFor();
    };
    await page.locator('.kb-card').first().waitFor();
    assert.equal(await page.locator('#panel-title').innerText(), '知识库管理');
    assert.equal(await page.getByText('Phase 10', { exact: false }).count(), 0);
    await screenshot('desktop-collections');
    pass('default collection entry; development labels removed');
    for (const name of ['文件上传', '文件管理', '知识问答']) await nav(name);
    pass('all four navigation entries');
    await layout('1440px empty QA');
    await screenshot('desktop-qa-empty');
    await input.fill('如何使用知识库？');
    await input.press('Control+Enter');
    await page.getByText('正在检索证据并组织回答…').waitFor();
    assert.ok(await page.getByRole('button', { name: '发送问题' }).isDisabled());
    await page.locator('.qa-conversation[data-state="success"]').waitFor();
    assert.deepEqual(requests[0], { question: '如何使用知识库？', collection_name: 'product-handbook', history: [] });
    assert.ok(await page.locator('.qa-markdown h2').count());
    assert.ok(await page.locator('.qa-markdown strong').count());
    assert.ok(await page.locator('.qa-markdown ol').count());
    assert.ok(await page.locator('.qa-markdown pre code').count());
    await page.locator('.qa-sources .ant-collapse-header').last().click();
    await page.locator('.qa-source-score').waitFor();
    assert.equal(await page.locator('.qa-source-score code').innerText(), '0.872');
    await page.locator('.qa-source-score').scrollIntoViewIfNeeded();
    await screenshot('desktop-qa-answer');
    pass('Ctrl+Enter, loading, unchanged request contract, Markdown and sources');

    await input.fill('保留的草稿');
    await nav('文件管理'); await nav('知识问答');
    assert.equal(await input.inputValue(), '保留的草稿');
    assert.equal(await page.locator('.qa-message-assistant').count(), 1);
    pass('navigation preserves draft and conversation');
    await choose('engineering-notes');
    assert.equal(await input.inputValue(), '');
    assert.equal(await page.locator('.qa-message').count(), 0);
    await send('工程规范有哪些？');
    assert.equal(requests.at(-1).collection_name, 'engineering-notes');
    assert.deepEqual(requests.at(-1).history, []);
    pass('switching KB clears history and sends to selected KB');
    for (let i = 0; i < 11; i++) await send('继续追问 ' + i);
    assert.equal(requests.at(-1).history.length, 20);
    assert.equal(await page.locator('.qa-message').count(), 20);
    await layout('20-message conversation');
    pass('20-message history limit');

    let failNext = true;
    await page.route('**/api/query', async route => {
      if (failNext) {
        failNext = false;
        await route.fulfill({ status: 500, json: { error: { code: 'LLM_UNAVAILABLE', message: 'Controlled failure', details: {} } } });
      } else await route.continue();
    });
    await input.fill('失败后重试');
    await page.getByRole('button', { name: '发送问题' }).click();
    await page.getByText('问答请求失败', { exact: true }).waitFor();
    const failedRequest = requests.at(-1);
    assert.equal(await page.locator('.qa-message-assistant').count(), 10);
    await page.locator('.qa-query-error').getByRole('button').click();
    await page.locator('.qa-conversation[data-state="success"]').waitFor();
    assert.deepEqual(requests.at(-1), failedRequest);
    await page.unroute('**/api/query');
    pass('500 error and retry preserve committed history and request');
    await choose('empty-workspace');
    await input.fill('空库问题');
    await page.getByRole('button', { name: '发送问题' }).click();
    await page.getByText('知识库暂时无法回答', { exact: true }).waitFor();
    pass('empty KB warning and retry');

    await choose('product-handbook');
    let release;
    let entered;
    const routeEntered = new Promise(resolve => { entered = resolve; });
    const gate = new Promise(resolve => { release = resolve; });
    await page.route('**/api/query', async route => {
      entered(); await gate;
      await route.fulfill({ json: { answer: '旧知识库的延迟回答', sources: [], query: '竞态检查', collection_name: 'product-handbook' } });
    });
    await input.fill('竞态检查');
    await page.getByRole('button', { name: '发送问题' }).click();
    await routeEntered;
    await choose('engineering-notes');
    const response = page.waitForResponse('**/api/query');
    release(); await response;
    await page.evaluate(() => new Promise(requestAnimationFrame));
    assert.equal(await page.locator('.qa-message').count(), 0);
    await page.unroute('**/api/query');
    pass('late response after KB switch is ignored');

    const longFileName = '很长的参考文件名'.repeat(16) + '.md';
    await page.route('**/api/query', route => route.fulfill({ json: {
      answer: '## 长内容\n\n' + ('正文内容包含一个长链接 https://example.test/' + 'a'.repeat(200) + '\n\n').repeat(12)
        + '\n```text\n' + 'long_code_'.repeat(80) + '\n```',
      sources: [{ file_id: 'fixture-file', chunk_id: 'fixture-chunk', file_name: longFileName, relevance_score: 0.456 }],
      query: '长内容检查', collection_name: 'engineering-notes',
    } }));
    await send('长内容检查');
    await page.locator('.qa-sources .ant-collapse-header').last().click();
    assert.ok(await page.locator('.qa-conversation').evaluate(element => element.scrollHeight > element.clientHeight));
    await layout('long answer / URL / source name');
    await page.unroute('**/api/query');

    // Clear long-content fixture before capturing the normal responsive page.
    await choose('product-handbook');
    await send('总结资料的使用方法');
    await page.locator('.qa-sources .ant-collapse-header').last().click();
    for (const width of [768, 390]) {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 1024 });
      const toggle = page.getByRole('button', { name: '打开导航' });
      await toggle.waitFor();
      await page.locator('.app-sider.ant-layout-sider-collapsed').waitFor({ state: 'attached' });
      await layout(width + 'px answer');
      await toggle.click();
      await page.getByRole('dialog').waitFor();
      await page.keyboard.press('Escape');
      await page.getByRole('dialog').waitFor({ state: 'hidden' });
      await toggle.click();
      await page.getByRole('dialog').getByRole('menuitem', { name: '文件管理', exact: true }).click();
      await page.locator('#panel-title').filter({ hasText: '文件管理' }).waitFor();
      await page.getByRole('dialog').waitFor({ state: 'hidden' });
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth));
      await toggle.click();
      await page.getByRole('dialog').getByRole('menuitem', { name: '知识问答', exact: true }).click();
      await page.getByRole('dialog').waitFor({ state: 'hidden' });
      await screenshot(width + 'px-qa-answer');
      pass(width + 'px drawer navigation and Escape');
    }

    await page.route('**/api/collections', route => route.fulfill({ status: 500,
      json: { error: { code: 'INTERNAL_ERROR', message: 'Controlled list failure', details: {} } } }));
    await page.reload(); await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: '打开导航' }).click();
    await page.getByRole('dialog').getByRole('menuitem', { name: '知识问答', exact: true }).click();
    await page.locator('.qa-collection-error').waitFor();
    assert.ok(await input.isDisabled());
    await page.unroute('**/api/collections');
    await page.locator('.qa-collection-error').getByRole('button', { name: '重新加载' }).click();
    await input.waitFor({ state: 'visible' });
    await page.locator('.qa-panel .ant-select').waitFor();
    assert.ok(await input.isEnabled());
    pass('collection list failure, disabled input and reload recovery');
    await page.route('**/api/collections', route => route.fulfill({ json: { collections: [] } }));
    await page.reload(); await page.waitForLoadState('networkidle');
    await page.getByRole('button', { name: '打开导航' }).click();
    await page.getByRole('dialog').getByRole('menuitem', { name: '知识问答', exact: true }).click();
    await page.getByRole('heading', { name: '先创建一个知识库' }).waitFor();
    assert.ok(await input.isDisabled());
    await layout('390px no collections');
    pass('no collections: guide and disabled input');
    assert.deepEqual(pageErrors, []);
    pass('no unhandled browser exceptions');
    fs.writeFileSync(path.join(out, 'report.json'), JSON.stringify({
      status: 'PASS', evidence: 'BROWSER UI with isolated demo API and controlled error/long-content fixtures; no real retrieval/model claims',
      checks: passed, queryRequests: requests.length, pageErrors, consoleMessages,
    }, null, 2));
    console.log(`SUMMARY ${passed.length}/${passed.length} PASS; artifacts: ${out}`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
