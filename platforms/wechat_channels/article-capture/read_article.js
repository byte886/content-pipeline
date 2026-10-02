// read_article.js — 读取当前文章 webview 的真实 URL 与正文
(() => {
  const content = document.querySelector('#js_content')
    || document.querySelector('.rich_media_content') || document.body;
  const sp = new URLSearchParams(location.search);
  const txt = content.innerText || '';
  const q = (s) => document.querySelector(s);
  return {
    url: location.href,
    biz: sp.get('__biz'),
    mid: sp.get('mid'),
    idx: sp.get('idx'),
    sn: sp.get('sn'),
    title: document.title,
    author: (q('#js_name') || {}).innerText || '',
    account: (q('#js_profile_qrcode') ? '' : '') ,
    contentLength: txt.length,
    contentHead: txt.slice(0, 1500),
  };
})()
