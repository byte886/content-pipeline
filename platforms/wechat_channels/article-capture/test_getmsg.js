// test_getmsg.js — 在文章正文 webview 同源上下文调用 profile_ext?action=getmsg
// 凭证全部从当前页面自动提取（cookie 的 appmsg_token、URL 的 __biz/pass_ticket、window.user_uin）
(async () => {
  const getCookie = (name) => {
    const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  };
  const sp = new URLSearchParams(location.search);
  const biz = sp.get('__biz') || window.biz || '';
  const passTicket = sp.get('pass_ticket') || '';
  const appmsgToken = getCookie('appmsg_token');
  const uin = window.user_uin || '';

  const params = new URLSearchParams({
    action: 'getmsg',
    __biz: biz,
    f: 'json',
    offset: '0',
    count: '10',
    is_ok: '1',
    scene: '124',
    appmsg_token: appmsgToken,
    uin: uin,
    key: '',
    pass_ticket: passTicket,
    wxtoken: '',
  });
  const url = '/mp/profile_ext?' + params.toString();

  const r = await fetch(url, { credentials: 'include', headers: { Accept: 'application/json' } });
  const text = await r.text();
  const out = { httpStatus: r.status, used: { biz, uin, hasToken: !!appmsgToken, hasTicket: !!passTicket },
                rawHead: text.slice(0, 300) };

  let parsed = null;
  try { parsed = JSON.parse(text); } catch (e) {}
  if (parsed) {
    out.ret = parsed.ret;
    out.errmsg = parsed.errmsg;
    out.msg_count = parsed.msg_count;
    out.can_msg_continue = parsed.can_msg_continue;
    out.next_offset = parsed.next_offset;
    try {
      const list = JSON.parse(parsed.general_msg_list).list || [];
      out.pageTitles = list.map(it => {
        const a = it.app_msg_ext_info || {};
        const multi = (a.multi_app_msg_item_list || []).map(m => m.title);
        return { datetime: (it.comm_msg_list || {}).datetime,
                 title: a.title, multi,
                 content_url: (a.content_url || '').slice(0, 90) };
      });
    } catch (e) { out.parseListErr = e.message; }
  }
  return out;
})()
