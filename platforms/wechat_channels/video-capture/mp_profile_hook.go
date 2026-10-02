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
  try{if(window.MessagePort){
    var wkN=0;
    function wkdump(d,src){try{var s=typeof d==='string'?d:JSON.stringify(d);if(!s)return;
      wkN++;
      if(wkN<=60){raw('WKDMP__'+src+'__'+wkN,s.slice(0,80000));}
      else if(s.length>40&&looksArticle(s)){raw('WK__'+src,s.slice(0,80000));}
    }catch(e){}}
    var OP=MessagePort.prototype.postMessage;MessagePort.prototype.postMessage=function(m){try{wkdump(m,'post');}catch(e){}return OP.apply(this,arguments);};
    var OA=MessagePort.prototype.addEventListener;MessagePort.prototype.addEventListener=function(t,fn){if(t==='message'&&typeof fn==='function'&&!fn.__mpw){var w=function(e){try{wkdump(e.data,'msg');}catch(x){}return fn.apply(this,arguments);};w.__mpw=1;arguments[1]=w;}return OA.apply(this,arguments);};
    var od=Object.getOwnPropertyDescriptor(MessagePort.prototype,'onmessage');
    Object.defineProperty(MessagePort.prototype,'onmessage',{configurable:true,enumerable:true,get:function(){return od&&od.get?od.get.call(this):this.__mp_om;},set:function(fn){if(typeof fn==='function'&&!fn.__mpom){var wf=function(e){try{wkdump(e.data,'onmsg');}catch(x){}return fn.apply(this,arguments);};wf.__mpom=1;if(od&&od.set)od.set.call(this,wf);else this.__mp_om=wf;}else{if(od&&od.set)od.set.call(this,fn);else this.__mp_om=fn;}}});}
  }catch(e){send('ERR',{where:'worker',e:''+e});}

  // ===== 直接定位微信注入的 xweb.worker.port（自定义 shim，可能不继承标准 MessagePort）=====
  if(typeof wkdump!=='function'){
    var wkN2=0;
    function wkdump(d,src){try{var s=typeof d==='string'?d:JSON.stringify(d);if(!s)return;
      wkN2++; if(wkN2<=80){raw('WKDMP__'+src+'__'+wkN2,s.slice(0,80000));}
      else if(s.length>40&&looksArticle(s)){raw('WK__'+src,s.slice(0,80000));}
    }catch(e){}}
  }
  function hookWorkerLike(w,label,url){
    try{
      if(!w||w.__wHooked) return;
      w.__wHooked=1;
      raw('WORKERNEW__'+label,JSON.stringify({url:String(url),hasPost:typeof w.postMessage,hasAEL:typeof w.addEventListener}));
      if(typeof w.postMessage==='function'&&!w.__pmW){
        var opm=w.postMessage;w.__pmW=1;
        w.postMessage=function(){try{wkdump(arguments[0],label+'.POST');}catch(e){}return opm.apply(this,arguments);};
      }
      if(typeof w.addEventListener==='function'){
        w.addEventListener('message',function(e){try{wkdump(e.data,label+'.MSG');}catch(x){}});
      }
    }catch(e){raw('WORKERHOOKERR__'+label,''+e);}
  }
  try{
    var OrigWorker=window.Worker;
    if(OrigWorker){
      var NW=function(url,opts){var w=new OrigWorker(url,opts);try{hookWorkerLike(w,'WKR',url);}catch(e){}return w;};
      NW.prototype=OrigWorker.prototype;
      window.Worker=NW;
    }
  }catch(e){raw('WORKERCONSERR',''+e);}
  try{
    var OrigSW=window.SharedWorker;
    if(OrigSW){
      var NSW=function(url,opts){var sw=new OrigSW(url,opts);try{hookWorkerLike(sw.port,'SHW',url);}catch(e){}return sw;};
      NSW.prototype=OrigSW.prototype;
      window.SharedWorker=NSW;
    }
  }catch(e){raw('SHAREDCONSERR',''+e);}

  // ===== Hook Blob 构造器：截获 blob Worker 的脚本文本（同步可得）=====
  try{
    var OrigBlob=window.Blob;
    var blobSeq=0;
    var NB=function(parts,opts){
      try{
        if(parts&&parts.length){
          for(var bi=0;bi<parts.length;bi++){
            var bp=parts[bi];
            if(typeof bp==='string'&&bp.length>60&&/onmessage|WebAssembly|postMessage|importScripts|self\./.test(bp)){
              blobSeq++;
              (function(text,seq){
                raw('WORKERMETA__'+seq,JSON.stringify({len:text.length,opts:opts&&opts.type,
                  hasWA:/WebAssembly/.test(text),hasMsg:/onmessage/.test(text),
                  hasXWS:/XWebSocket|XWebXMLHttpRequest/.test(text)}));
                for(var k=0,fi=0;k<text.length;k+=11000,fi++){
                  raw('WORKERSRC__'+seq+'__'+fi,text.slice(k,k+11000));
                }
              })(bp,blobSeq);
            }
          }
        }
      }catch(e){raw('BLOBHOOKERR',''+e);}
      return new OrigBlob(parts,opts);
    };
    NB.prototype=OrigBlob.prototype;
    window.Blob=NB;
  }catch(e){raw('BLOBCONSERR',''+e);}

  // ===== Hook XWeb native 桥：XWebXMLHttpRequest / XWebSocket（底层走 native，HTTP 代理抓不到）=====
  function describeXObj(name){
    try{
      var X=window[name],info={type:typeof X};
      if(X){
        try{info.proto=Object.getOwnPropertyNames(X.prototype);}catch(e){info.protoErr=''+e;}
        try{info.own=Object.getOwnPropertyNames(X);}catch(e){}
        try{info.str=Function.prototype.toString.call(X).slice(0,160);}catch(e){}
      }
      raw('XDESC__'+name,JSON.stringify(info));
    }catch(e){raw('XDESCERR__'+name,''+e);}
  }
  describeXObj('XWebXMLHttpRequest');
  describeXObj('XWebSocket');

  var xhrSeq=0;
  function hookXhrCtor(ctorName,tag){
    try{
      var Orig=window[ctorName];
      if(typeof Orig!=='function'){raw(tag+'NOTFUNC',typeof Orig);return;}
      var NC=function(){
        var x=new Orig(),murl='',mm='',seq=0;
        try{
          x.open=function(m,u){mm=m;murl=u;return Orig.prototype.open.apply(x,arguments);};
          x.send=function(body){
            seq=++xhrSeq;
            try{
              var pre=mm+' '+murl+'\n';
              raw(tag+'REQ__'+seq,pre+(body&&typeof body==='string'?body.slice(0,30000):(body?'[bin '+(body.byteLength||body.length)+']':'')));
            }catch(e){}
            try{
              x.addEventListener('load',function(){
                try{
                  var rt=x.responseText;
                  if(typeof rt==='string'&&rt.length)raw(tag+'RESP__'+seq,murl+'\n'+rt.slice(0,120000));
                  else if(x.response)raw(tag+'RESPBIN__'+seq,murl+' [bin '+(x.response.byteLength||x.response.length)+']');
                }catch(e){raw(tag+'RESPERR__'+seq,''+e);}
              });
              x.addEventListener('error',function(){raw(tag+'XERR__'+seq,murl);});
            }catch(e){}
            return Orig.prototype.send.apply(x,arguments);
          };
        }catch(e){raw(tag+'WRAPERR',''+e);}
        return x;
      };
      NC.prototype=Orig.prototype;
      window[ctorName]=NC;
      raw(tag+'HOOKED','ok');
    }catch(e){raw(tag+'CONSERR',''+e);}
  }
  hookXhrCtor('XWebXMLHttpRequest','XHR_');

  var wsSeq=0;
  function hookWsCtor(ctorName,tag){
    try{
      var Orig=window[ctorName];
      if(typeof Orig!=='function'){raw(tag+'NOTFUNC',typeof Orig);return;}
      var NC=function(url,protocols){
        var ws=protocols?new Orig(url,protocols):new Orig(url),seq=++wsSeq,sc=0,mc=0;
        raw(tag+'OPEN__'+seq,String(url));
        try{
          ws.send=function(d){
            sc++;
            try{raw(tag+'SEND__'+seq+'_'+sc,typeof d==='string'?d.slice(0,30000):'[bin '+(d.byteLength||d.length)+']');}catch(e){}
            return Orig.prototype.send.apply(ws,arguments);
          };
          ws.addEventListener('message',function(ev){
            mc++;
            try{var d=ev.data;raw(tag+'MSG__'+seq+'_'+mc,typeof d==='string'?d.slice(0,120000):'[bin '+(d.byteLength||d.length)+']');}catch(e){}
          });
        }catch(e){raw(tag+'WRAPERR__'+seq,''+e);}
        return ws;
      };
      NC.prototype=Orig.prototype;
      window[ctorName]=NC;
      raw(tag+'HOOKED','ok');
    }catch(e){raw(tag+'CONSERR',''+e);}
  }
  hookWsCtor('XWebSocket','XWS_');

  // ===== Pinia profile store 采集器：直接读 cardObjects + 自动 fetchMoreData 翻到底 =====
  function getProfileStore(){
    try{
      var el=document.querySelector('#app');
      var app=el&&(el.__vue_app__||el.__vueApp__);
      var pinia=app&&app.config.globalProperties.$pinia;
      if(pinia&&pinia._s&&pinia._s.get)return pinia._s.get('profile');
    }catch(e){}
    return null;
  }
  function dumpProfileCards(store,tag){
    var arr=store.cardObjects||[];
    try{
      raw(tag,JSON.stringify({n:arr.length,noMore:store.noMore,cards:arr,liveCards:store.liveCardObjects||[]}));
      return;
    }catch(e){raw(tag+'_FULLFAIL',''+e);}
    var ok=[];
    for(var i=0;i<arr.length;i++){
      try{ok.push(JSON.parse(JSON.stringify(arr[i])));}
      catch(e){try{ok.push({__idx:i,__err:String(e),keys:Object.keys(arr[i]||{})});}catch(_){}}
    }
    raw(tag+'_PARTIAL',JSON.stringify({n:arr.length,cards:ok}));
  }
  function sleep(ms){return new Promise(function(r){setTimeout(r,ms);});}
  async function profileDriver(){
    var store=null;
    for(var w=0;w<50;w++){store=getProfileStore();if(store)break;await sleep(500);}
    if(!store){raw('PROFILE_NOSTORE','pinia/profile not found');return;}
    raw('PROFILE_STOREFIND','ok');
    var lastSig='',guard=0,dumpedSig='';
    while(guard<400){
      guard++;
      var n=(store.cardObjects||[]).length;
      var sig=n+'|'+store.noMore+'|'+store.isFetchingMore;
      if(sig!==lastSig){raw('CARDSTATE__'+guard,JSON.stringify({n:n,noMore:store.noMore,fetching:store.isFetchingMore,liveN:(store.liveCardObjects||[]).length,liveNoMore:store.liveNoMore}));lastSig=sig;}
      try{
        if(n>0&&!store.noMore&&!store.isFetchingMore){
          var p=store.fetchMoreData();
          if(p&&typeof p.then==='function'){try{await p;}catch(e){raw('FETCHREJ__'+guard,''+e);}}
          await sleep(1400);
          continue;
        }
        if(store.noMore&&n>0){
          if(sig!==dumpedSig){dumpProfileCards(store,'PROFILE_CARDS__'+guard);dumpedSig=sig;}
          await sleep(2500);
          continue;
        }
      }catch(e){raw('DRIVERERR__'+guard,''+e);}
      await sleep(800);
    }
    raw('PROFILE_DRIVEREND','guard exhausted');
  }
  profileDriver();

  function hookPortInstance(p,label){
    try{
      if(!p) return 'null';
      if(p.__mpHooked) return 'already';
      p.__mpHooked=1;
      var pr=Object.getPrototypeOf(p);
      var info={label:label,
        ctor:p.constructor&&p.constructor.name,
        protoCtor:pr&&pr.constructor&&pr.constructor.name,
        ownKeys:Object.keys(p),
        hasPost:typeof p.postMessage,
        hasAEL:typeof p.addEventListener,
        onMsg:Object.getOwnPropertyDescriptor(p,'onmessage')?'own':'proto'};
      raw('PORTINFO__'+label,JSON.stringify(info));
      if(typeof p.postMessage==='function'&&!p.__pmW){
        var opm=p.postMessage;p.__pmW=1;
        p.postMessage=function(){try{wkdump(arguments[0],label+'.POST');}catch(e){}return opm.apply(this,arguments);};
      }
      if(typeof p.addEventListener==='function'){
        p.addEventListener('message',function(e){try{wkdump(e.data,label+'.MSG');}catch(x){}});
      }else if(typeof p.onmessage==='function'){
        var om=p.onmessage;
        var wom=function(e){try{wkdump(e.data,label+'.OM');}catch(_){}return om.apply(this,arguments);};
        p.onmessage=wom;
      }
      return 'ok';
    }catch(e){raw('PORTERR__'+label,''+e);return 'err';}
  }
  function describeXweb(){
    try{
      var xw=window.xweb;
      if(!xw){
        var wt={xweb:typeof window.xweb,
          global:typeof window.global,
          globalEqWin:window.global===window,
          wxjs:document.__wxjsjs__isLoaded,
          workerPre:typeof window.workerPre,
          WXJB:typeof window.WeixinJSBridge,
          wx:typeof window.wx,
          winMatch:Object.getOwnPropertyNames(window).filter(function(k){return /xweb|worker|^wx/i.test(k);}).slice(0,30)};
        raw('WORLDTEST',JSON.stringify(wt));
        raw('XWEBDESC','no window.xweb');
        return;
      }
      var o={xwKeys:Object.keys(xw)};
      if(xw.worker){
        o.workerKeys=Object.keys(xw.worker);
        try{o.connectSrc=(''+xw.worker.connect).slice(0,400);}catch(e){}
        var p=xw.worker.port;
        if(p){
          o.portKeys=Object.keys(p);
          o.portCtor=p.constructor&&p.constructor.name;
          var pr=Object.getPrototypeOf(p);
          o.portProto=pr&&pr.constructor&&pr.constructor.name;
        }
      }
      raw('XWEBDESC',JSON.stringify(o));
    }catch(e){raw('XWEBDESCERR',''+e);}
  }
  function findHookXweb(){
    try{
      describeXweb();
      var xw=window.xweb;
      if(xw&&xw.worker){
        if(xw.worker.port) hookPortInstance(xw.worker.port,'MAIN');
        Object.keys(xw.worker).forEach(function(k){
          var v;try{v=xw.worker[k];}catch(e){return;}
          if(v&&typeof v==='object'&&typeof v.postMessage==='function'&&k!=='port'){
            hookPortInstance(v,'WK_'+k);
          }
        });
      }
    }catch(e){}
  }
  findHookXweb();
  var xwTries=0;
  function xwStep(){
    xwTries++;
    try{
      var xw=window.xweb;
      if(xw&&xw.worker){
        if(xw.worker.port&&!xw.worker.port.__mpHooked) hookPortInstance(xw.worker.port,'MAIN');
        Object.keys(xw.worker).forEach(function(k){
          var v;try{v=xw.worker[k];}catch(e){return;}
          if(v&&typeof v==='object'&&typeof v.postMessage==='function'&&k!=='port'&&!v.__mpHooked) hookPortInstance(v,'WK_'+k);
        });
      }
      if(xwTries%4===0) describeXweb();
    }catch(e){}
    if(xwTries<150) setTimeout(xwStep,100);
  }
  setTimeout(xwStep,100);

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
