// probe.js — 在「文章正文 webview」里探测可用凭证与全局变量
// 由 cdp.js 注入执行；返回结构化对象（不要在页面里直接运行依赖外部的东西）。
(() => {
  const out = { href: location.href };

  // 1) cookie
  try { out.cookie = document.cookie || '(空)'; }
  catch (e) { out.cookie = 'ERR ' + e.message; }

  // 2) window 上与凭证相关的属性名（只取名，避免直接取值导致爆炸/抛错）
  try {
    out.matchedWindowKeys = Object.getOwnPropertyNames(window)
      .filter(k => /token|__biz|biz|uin|ticket|cgi|appmsg|profile|user|^key/i.test(k))
      .slice(0, 100);
  } catch (e) { out.matchedWindowKeys = 'ERR ' + e.message; }

  // 3) 常见全局变量逐个安全取值
  const pick = (expr) => {
    try {
      const v = eval(expr);
      if (v === undefined || v === null) return String(v);
      if (typeof v === 'object') {
        const s = JSON.stringify(v);
        return s.length > 600 ? s.slice(0, 600) + '…(截断)' : s;
      }
      return String(v);
    } catch (e) { return 'ERR ' + e.message; }
  };
  out.vars = {
    appmsg_token: pick('window.appmsg_token'),
    __biz: pick('window.__biz'),
    uin: pick('window.uin'),
    pass_ticket: pick('window.pass_ticket'),
    key: pick('window.key'),
    cgiData: pick('window.cgiData'),
    'wx.cgiData': pick('window.wx && window.wx.cgiData'),
    'wx.commonData': pick('window.wx && window.wx.commonData'),
  };

  return out;
})()
