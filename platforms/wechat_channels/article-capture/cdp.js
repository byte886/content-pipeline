#!/usr/bin/env node
/**
 * cdp.js — 通用 Chrome DevTools Protocol 客户端
 *
 * 用 Node 22 内置全局 WebSocket 直连 CDP，零第三方依赖。
 * 典型用途：在微信 XWeb（安卓，经 adb forward）或 WeChatAppEx（Mac）
 * 的可调试 webview 里执行 JS，做同源接口调用 / 读 DOM / 自动翻页。
 *
 * 用法:
 *   node cdp.js --endpoint http://127.0.0.1:9224 --match "/s/" --eval "location.href"
 *   node cdp.js --endpoint http://127.0.0.1:9224 --match "mp.weixin" --file probe.js
 *
 * 参数:
 *   --endpoint <url>   CDP HTTP 入口；默认读环境变量 CDP_ENDPOINT，再默认 http://127.0.0.1:9224
 *   --match <substr>    选择 URL 含该子串的 page target；可重复传入，按顺序匹配任一
 *   --eval <js>         直接执行一段 JS 表达式
 *   --file <path>       从文件读取 JS 执行（与 --eval 二选一）
 *   --no-await          不 await Promise（默认会 await 并取 resolve 值）
 *   --timeout <ms>      执行超时，默认 30000
 *
 * 输出: 打印 Runtime.evaluate 的结果值（JSON）。失败时进程退出码非 0。
 */

'use strict';

function parseArgs(argv) {
  const args = { endpoint: process.env.CDP_ENDPOINT || 'http://127.0.0.1:9224',
                 matches: [], eval: null, file: null,
                 awaitPromise: true, timeout: 30000 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--endpoint') args.endpoint = argv[++i];
    else if (a === '--match') args.matches.push(argv[++i]);
    else if (a === '--eval') args.eval = argv[++i];
    else if (a === '--file') args.file = argv[++i];
    else if (a === '--no-await') args.awaitPromise = false;
    else if (a === '--timeout') args.timeout = parseInt(argv[++i], 10);
  }
  return args;
}

async function listPages(endpoint) {
  const res = await fetch(endpoint.replace(/\/$/, '') + '/json', { method: 'GET' });
  if (!res.ok) throw new Error('GET /json failed: HTTP ' + res.status);
  const list = await res.json();
  return list.filter(t => t.type === 'page' && t.webSocketDebuggerUrl);
}

function pickTarget(pages, matches) {
  if (!matches.length) return pages[0];
  for (const m of matches) {
    const hit = pages.find(p => (p.url || '').includes(m));
    if (hit) return hit;
  }
  return null;
}

function cdpEvaluate(wsUrl, expression, awaitPromise, timeoutMs) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(wsUrl);
    let nextId = 1;
    const timer = setTimeout(() => { try { ws.close(); } catch (e) {}
      reject(new Error('CDP evaluate timeout after ' + timeoutMs + 'ms')); }, timeoutMs);

    ws.addEventListener('open', () => {
      ws.send(JSON.stringify({ id: nextId, method: 'Runtime.enable' }));
      nextId++;
      ws.send(JSON.stringify({
        id: nextId,
        method: 'Runtime.evaluate',
        params: { expression, awaitPromise, returnByValue: true, userGesture: true },
      }));
    });

    ws.addEventListener('message', (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch (e) { return; }
      // Runtime.evaluate 的 id 是 2（enable 是 1）；用 >=2 且有 result 判定
      if (msg.id && msg.result && msg.result.result !== undefined) {
        clearTimeout(timer);
        try { ws.close(); } catch (e) {}
        const r = msg.result;
        if (r.exceptionDetails) {
          reject(new Error('JS exception: ' + JSON.stringify(r.exceptionDetails.exception
            ? r.exceptionDetails.exception.description : r.exceptionDetails.text)));
          return;
        }
        resolve(r.result.value);
      }
    });

    ws.addEventListener('error', (e) => {
      clearTimeout(timer);
      reject(new Error('WebSocket error (CDP endpoint 可达吗？)'));
    });
  });
}

(async () => {
  const args = parseArgs(process.argv.slice(2));
  let expression = args.eval;
  if (args.file) {
    const fs = await import('node:fs');
    expression = fs.readFileSync(args.file, 'utf8');
  }
  if (expression == null) {
    console.error('需要 --eval "<js>" 或 --file <path>');
    process.exit(2);
  }

  const pages = await listPages(args.endpoint);
  if (!pages.length) throw new Error('该 endpoint 下没有可调试的 page target（微信里是否已打开网页？）');
  const target = pickTarget(pages, args.matches);
  if (!target) {
    console.error('未找到 URL 匹配 ' + JSON.stringify(args.matches) + ' 的 target。当前 page targets:');
    pages.forEach(p => console.error('  - ' + p.url));
    process.exit(3);
  }
  process.stderr.write('选中 target: ' + target.url + '\n');

  const value = await cdpEvaluate(target.webSocketDebuggerUrl, expression,
                                   args.awaitPromise, args.timeout);
  if (typeof value === 'string') console.log(value);
  else console.log(JSON.stringify(value, null, 2));
})().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
