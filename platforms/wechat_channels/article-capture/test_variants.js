// test_variants.js — 探查 getmsg no session 的原因：试 home / 不同 scene / 不同凭证组合
(async () => {
  const getCookie = (name) => {
    const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  };
  const sp = new URLSearchParams(location.search);
  const biz = sp.get('__biz');
  const passTicket = sp.get('pass_ticket') || '';
  const token = getCookie('appmsg_token');
  const uin = window.user_uin || '';
  const results = {};

  const doFetch = async (name, url) => {
    try {
      const r = await fetch(url, {
        credentials: 'include',
        headers: { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      });
      const t = await r.text();
      results[name] = { status: r.status, head: t.slice(0, 280) };
    } catch (e) { results[name] = { err: e.message }; }
  };

  // 1) action=home（尝试建立会话 / 看是否下发 key）
  const p1 = new URLSearchParams({ action: 'home', __biz: biz, uin, key: '',
    pass_ticket: passTicket, scene: '124', appmsg_token: token, wxtoken: '', f: 'json' });
  await doFetch('home', '/mp/profile_ext?' + p1.toString());

  // 2) getmsg，scene 与当前页一致(126)
  const p2 = new URLSearchParams({ action: 'getmsg', __biz: biz, f: 'json', offset: '0',
    count: '10', is_ok: '1', scene: '126', appmsg_token: token, uin, key: '',
    pass_ticket: passTicket, wxtoken: '' });
  await doFetch('getmsg_scene126', '/mp/profile_ext?' + p2.toString());

  // 3) getmsg，URL 不带 appmsg_token（只靠 cookie）
  const p3 = new URLSearchParams({ action: 'getmsg', __biz: biz, f: 'json', offset: '0',
    count: '10', is_ok: '1', scene: '124', uin, key: '',
    pass_ticket: passTicket, wxtoken: '' });
  await doFetch('getmsg_tokenViaCookieOnly', '/mp/profile_ext?' + p3.toString());

  // 4) getmsg，common/friendrel 场景号（部分实现用 scene=124 之外的 125/179）
  const p4 = new URLSearchParams({ action: 'getmsg', __biz: biz, f: 'json', offset: '0',
    count: '10', is_ok: '1', scene: '179', appmsg_token: token, uin, key: '',
    pass_ticket: passTicket, wxtoken: '' });
  await doFetch('getmsg_scene179', '/mp/profile_ext?' + p4.toString());

  return results;
})()
