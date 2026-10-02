// probe2.js — 取全构造 getmsg 所需的全局变量 / URL 参数 / cookie
(() => {
  const names = ['user_uin','biz','bizuin','uin','key','wxtoken','pass_ticket','appmsg_token',
    'appuin','appmsg_type','user_name','appmsgid','source_biz','source_username','source_encode_biz',
    'reprint_ticket','mp_profile','isprofileblock','new_appmsg'];
  const vars = {};
  for (const n of names) {
    try {
      let v = window[n];
      if (v && typeof v === 'object') {
        v = JSON.stringify(v);
        if (v.length > 800) v = v.slice(0, 800) + '…(截断)';
      }
      vars[n] = (v === undefined) ? 'undefined' : (v === null ? 'null' : String(v));
    } catch (e) { vars[n] = 'ERR ' + e.message; }
  }
  try { let s = JSON.stringify(window.cgiDataNew); vars.cgiDataNew = s && s.length > 800 ? s.slice(0,800)+'…' : s; }
  catch (e) { vars.cgiDataNew = 'ERR ' + e.message; }
  try { let s = JSON.stringify(window.__appmsgCgiData); vars.__appmsgCgiData = s && s.length > 800 ? s.slice(0,800)+'…' : s; }
  catch (e) { vars.__appmsgCgiData = 'ERR ' + e.message; }

  const sp = new URLSearchParams(location.search);
  const urlParams = {};
  for (const k of ['__biz','mid','idx','sn','pass_ticket','exportkey','scene','subscene','session_us','wx_header']) {
    urlParams[k] = sp.get(k);
  }

  const cookies = {};
  document.cookie.split(';').forEach(c => {
    const i = c.indexOf('=');
    if (i > 0) cookies[c.slice(0, i).trim()] = c.slice(i + 1).trim();
  });

  return {
    vars,
    urlParams,
    cookieKeys: Object.keys(cookies),
    appmsg_token_from_cookie: cookies['appmsg_token'] || '(无)',
  };
})()
