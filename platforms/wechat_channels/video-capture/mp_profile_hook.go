package main

import (
	"bytes"
	"compress/gzip"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
)

// injectMpProfileReconHook 向公众号资料页 channels.weixin.qq.com/web/pages/mp_profile?bizusername=gh_xxx
// 注入"只读侦察探针"（公众号全量文章 B 方案的第一步）。
//
// 背景：mp_profile 与视频号 profile 同属 finder 前端（FinderMpProfile.js + vuexStores.js），
// 但文章列表数据不走可抓的标准 HTTPS（页面壳仅 4KB，数据经 XWEB 私有 xweb.worker 通道下发），
// 旧 injectArticleListHook 只抓 outerHTML + a[href=/s/] 必然为空。
// 本探针零副作用（不点击、不发布、不修改状态），只做：
//   - 枚举 Vuex($store.state/_actions/getters) 与 Pinia(store state/methods) 结构；
//   - hook fetch / XMLHttpRequest / MessagePort(worker)，捕获含文章特征的报文；
//   - 深度遍历状态树定位"文章数组"的 module 路径、字段、样例；
//   - dump 文章卡片 DOM（class/data-*/outerHTML）、tab、滚动容器。
//
// 上报复用 type=3 的 page_html 通道，URL 以 '#mprecon__<tag>__<rid>__<i>__<n>' 分片编码，
// 落盘后按 mprecon__ 前缀 grep + 重组即可，不改 Go 侧分流。
func (c *Captor) injectMpProfileReconHook(resp *http.Response) *http.Response {
	log.Printf("[MpRecon] inject mp_profile recon, URL: %s", resp.Request.URL.String())

	var reader io.Reader = resp.Body
	if strings.EqualFold(resp.Header.Get("Content-Encoding"), "gzip") {
		gz, err := gzip.NewReader(resp.Body)
		if err != nil {
			log.Printf("[MpRecon] gzip 解压失败: %v", err)
			return resp
		}
		defer gz.Close()
		reader = gz
		resp.Header.Del("Content-Encoding")
	}

	body, err := io.ReadAll(reader)
	if err != nil {
		log.Printf("[MpRecon] 读取响应体失败: %v", err)
		return resp
	}
	resp.Body.Close()

	js := mpReconJS
	modified := bytes.Replace(body, []byte("</head>"), []byte(js+"</head>"), 1)
	if len(modified) == len(body) {
		modified = bytes.Replace(body, []byte("<body>"), []byte("<body>"+js), 1)
	}
	if len(modified) > len(body) {
		log.Printf("[MpRecon] JS 注入成功 %d -> %d", len(body), len(modified))
	} else {
		log.Printf("[MpRecon] JS 注入失败，长度未变化")
	}

	resp.Body = io.NopCloser(bytes.NewReader(modified))
	resp.ContentLength = int64(len(modified))
	resp.Header.Set("Content-Length", fmt.Sprintf("%d", len(modified)))
	resp.Header.Set("Cache-Control", "no-cache, no-store, must-revalidate")
	resp.Header.Set("Pragma", "no-cache")
	return resp
}

// mpReconJS 注意：Go 反引号原始字符串，JS 内部禁止再出现反引号，字符串一律用单/双引号。
const mpReconJS = `
<script>
(function(){
  if(window.__mprecon)return; window.__mprecon=1;
  var EP='https://wxapp.tc.qq.com/res-downloader/wechat?type=3';
  var CH=11000;
  function raw(tag,str){try{str=String(str);
    var rid=Date.now()+''+Math.floor(Math.random()*1e6),n=Math.max(1,Math.ceil(str.length/CH));
    for(var i=0;i<n;i++){(function(i){setTimeout(function(){
      fetch(EP,{method:'POST',mode:'no-cors',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({type:'page_html',url:location.href+'#mprecon__'+tag+'__'+rid+'__'+i+'__'+n,html:str.slice(i*CH,(i+1)*CH)})});
    },i*40);})(i);}
  }catch(e){}}
  function send(tag,o){raw(tag,(typeof o==='string')?o:JSON.stringify(o));}
  function looksArticle(s){if(!s||typeof s!=='string')return false;
    return /__biz|appmsg|general_msg|msgList|publish_info|appmsg_type|appmsg_id|ori_head_img|content_url|mp_profile|getappmsgext|\/s\?|appmsgalbum|article_url|news_show/i.test(s);}

  // ===== 网络 / worker hook（文章数据若经 worker 下发，在此捕获原文）=====
  try{var OF=window.fetch;window.fetch=function(){var a=arguments,u=(a[0]&&a[0].url)||a[0];var p=OF.apply(this,a);
    try{p.then(function(r){var ct=r.headers.get('content-type')||'';if(/json|text|html/.test(ct)){r.clone().text().then(function(t){if(t&&t.length>40&&looksArticle(t))raw('NET__'+encodeURIComponent(String(u)).slice(0,80),t.slice(0,120000));}).catch(function(){});}});}catch(e){}
    return p;};}catch(e){send('ERR',{where:'fetch',e:''+e});}
  try{var OX=XMLHttpRequest.prototype.open,OS=XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open=function(m,u){this.__u=u;return OX.apply(this,arguments);};
    XMLHttpRequest.prototype.send=function(){var self=this;this.addEventListener('load',function(){try{var t=self.responseText;if(t&&t.length>40&&looksArticle(t))raw('NET__'+encodeURIComponent(String(self.__u)).slice(0,80),t.slice(0,120000));}catch(e){}});return OS.apply(this,arguments);};}catch(e){send('ERR',{where:'xhr',e:''+e});}
  try{if(window.MessagePort){function wk(d,src){try{var s=typeof d==='string'?d:JSON.stringify(d);if(s&&s.length>40&&looksArticle(s))raw('WK__'+src,s.slice(0,120000));}catch(e){}}
    var OP=MessagePort.prototype.postMessage;MessagePort.prototype.postMessage=function(m){try{wk(m,'post');}catch(e){}return OP.apply(this,arguments);};
    var OA=MessagePort.prototype.addEventListener;MessagePort.prototype.addEventListener=function(t,fn){if(t==='message'&&typeof fn==='function'&&!fn.__mpw){var w=function(e){try{wk(e.data,'msg');}catch(x){}return fn.apply(this,arguments);};w.__mpw=1;arguments[1]=w;}return OA.apply(this,arguments);};
    var od=Object.getOwnPropertyDescriptor(MessagePort.prototype,'onmessage');
    Object.defineProperty(MessagePort.prototype,'onmessage',{configurable:true,enumerable:true,get:function(){return od&&od.get?od.get.call(this):this.__mp_om;},set:function(fn){if(typeof fn==='function'&&!fn.__mpom){var wf=function(e){try{wk(e.data,'onmsg');}catch(x){}return fn.apply(this,arguments);};wf.__mpom=1;if(od&&od.set)od.set.call(this,wf);else this.__mp_om=wf;}else{if(od&&od.set)od.set.call(this,fn);else this.__mp_om=fn;}}});}
  }catch(e){send('ERR',{where:'worker',e:''+e});}

  // ===== Vuex / Pinia 结构枚举 =====
  function gp(){try{return document.querySelector('#app').__vue_app__.config.globalProperties;}catch(e){return null;}}
  function shallow(o,depth){var out={};if(!o||typeof o!=='object')return typeof o;
    Object.keys(o).slice(0,60).forEach(function(k){try{var v=o[k];if(v==null){out[k]=v;}else if(Array.isArray(v)){out[k]='['+v.length+']';}else if(typeof v==='object'){out[k]=depth>0?shallow(v,depth-1):'{'+Object.keys(v).slice(0,15).join(',')+'}';}else{out[k]=typeof v==='string'?v.slice(0,50):v;}}catch(e){}});return out;}
  function dumpStructure(){var g=gp();if(!g){send('ERR',{where:'gp-no-vue'});return;}var rep={vuex:null,vuexActions:[],vuexGetters:[],pinia:[]};
    try{if(g.$store){rep.vuex=shallow(g.$store.state,1);
      rep.vuexActions=Object.keys(g.$store._actions||{}).sort();
      rep.vuexGetters=Object.keys(g.$store.getters||{}).slice(0,200);}}catch(e){rep.vuexErr=''+e;}
    try{if(g.$pinia&&g.$pinia._s){g.$pinia._s.forEach(function(st,id){rep.pinia.push({id:id,stateKeys:Object.keys(st.$state||{}),methods:Object.getOwnPropertyNames(st).filter(function(k){return typeof st[k]==='function';}).slice(0,90)});});}}catch(e){rep.piniaErr=''+e;}
    send('STRUCT',rep);}

  // ===== 深度遍历定位"文章数组" =====
  function articleLike(x){if(!x||typeof x!=='object'||Array.isArray(x))return false;var ks=Object.keys(x);
    var hasT=ks.some(function(k){return /title|heading|digest|summary|appmsg|content$/i.test(k);});
    var hasL=ks.some(function(k){return /link|^url$|content_url|__biz|url$/i.test(k);});
    return hasT&&hasL;}
  function walkArrays(o,path,depth,cb){if(depth>9||!o||typeof o!=='object')return;
    if(Array.isArray(o)){if(o.length>=1&&typeof o[0]==='object'&&articleLike(o[0]))cb(o,path);
      for(var i=0;i<o.length&&i<3;i++)walkArrays(o[i],path+'['+i+']',depth+1,cb);return;}
    var ks=Object.keys(o);for(var k=0;k<ks.length&&k<80;k++){var v;try{v=o[ks[k]];}catch(e){continue;}if(v&&typeof v==='object')walkArrays(v,path+'.'+ks[k],depth+1,cb);}}
  function dumpArticleArrays(){var g=gp();if(!g)return;var found=[];
    var roots=[['vuex',g.$store?g.$store.state:null],['pinia',g.$pinia&&g.$pinia.state?(g.$pinia.state.value||g.$pinia.state):null]];
    roots.forEach(function(pair){if(!pair[1])return;walkArrays(pair[1],pair[0],0,function(arr,path){if(found.length<12){found.push({path:path,len:arr.length,firstKeys:Object.keys(arr[0]).slice(0,50),sample:shallow(arr[0],2)});}});});
    if(found.length)send('ARR',found);}

  // ===== DOM 卡片 / 链接 / tab / 滚动容器 =====
  function dumpDOM(){var rep={tabs:[],links:[],cards:[],scrollBoxes:[]};
    try{var tt={};document.querySelectorAll('.tab,[role=tab],[class*=tab]').forEach(function(e){var t=(e.textContent||'').trim();if(t&&t.length<16)tt[t]=1;});rep.tabs=Object.keys(tt);}catch(e){}
    try{var ls={};document.querySelectorAll('a[href]').forEach(function(a){var h=a.href||'';if(/mp\.weixin|\/s\?|__biz|weixin|qq\.com/.test(h))ls[h]=(a.textContent||'').trim().slice(0,40);});rep.links=Object.keys(ls).slice(0,40).map(function(h){return {href:h.slice(0,220),text:ls[h]};});}catch(e){}
    try{var seen={};document.querySelectorAll('[class*=article],[class*=item],[class*=card],[class*=feed],[class*=news],[class*=post],[class*=history]').forEach(function(e){var c=''+(e.className||'');if(seen[c]||typeof c!=='string')return;var r=e.getBoundingClientRect();if(r.width<80||r.height<28)return;seen[c]=1;if(rep.cards.length<8)rep.cards.push({cls:c.slice(0,100),tag:e.tagName,text:(e.innerText||'').slice(0,150),data:Array.prototype.slice.call(e.attributes).filter(function(a){return a.name.indexOf('data-')===0;}).map(function(a){return a.name+'='+a.value;}).slice(0,24),html:e.outerHTML.slice(0,1000)});});}catch(e){rep.cardErr=''+e;}
    try{document.querySelectorAll('div').forEach(function(d){var s=getComputedStyle(d);if((s.overflowY==='auto'||s.overflowY==='scroll')&&d.scrollHeight>d.clientHeight+100){if(rep.scrollBoxes.length<6)rep.scrollBoxes.push({cls:(''+d.className).slice(0,60),sh:d.scrollHeight,ch:d.clientHeight});}});}catch(e){}
    send('DOM',rep);}

  var n=0;
  function tick(){n++;
    if(n===1)dumpStructure();
    dumpArticleArrays();
    if(n===1||n%5===0)dumpDOM();
    try{send('TICK',{tick:n,href:location.href,title:document.title,bodyLen:(document.body&&document.body.innerText||'').length});}catch(e){}
  }
  setTimeout(function(){tick();setInterval(tick,2000);},1500);
  console.log('[MpRecon] probe started');
})();
</script>
`
