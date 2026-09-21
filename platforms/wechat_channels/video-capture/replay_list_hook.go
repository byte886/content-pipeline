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

// injectReplayListHook 注入"回放列表提取器"。
//
// 主通道：视频号 profile 页是 Vue3 应用（#app 暴露 __vue_app__，globalProperties 同时有
// $store / $pinia / $router / $route）。列表数据最终落在 Pinia/Vuex 的状态树里。
// 脚本滚动加载全部回放卡片后，深度遍历 $store.state 与 $pinia.state，用卡片封面
// encfilekey / 时长文本作为锚点定位 feed 数组，并按"元素同时含 id 类与 nonce 类字段"
// 识别列表，把整个数组 JSON 分块上报（RLIST_FEEDARR__）。
// 辅助：hook fetch/XHR/worker（RLIST_API__/RLIST_WK__）、上报状态树结构（RLIST_STATEMAP__）。
// 全程零副作用：不点击、不导航、不播放。
func (c *Captor) injectReplayListHook(resp *http.Response) *http.Response {
	log.Printf("[ReplayList] injectReplayListHook被调用，URL: %s", resp.Request.URL.String())

	var reader io.Reader = resp.Body
	if strings.EqualFold(resp.Header.Get("Content-Encoding"), "gzip") {
		gz, err := gzip.NewReader(resp.Body)
		if err != nil {
			log.Printf("[ReplayList] gzip解压失败: %v", err)
			return resp
		}
		defer gz.Close()
		reader = gz
		resp.Header.Del("Content-Encoding")
	}

	body, err := io.ReadAll(reader)
	if err != nil {
		log.Printf("[ReplayList] 读取响应体失败: %v", err)
		return resp
	}
	resp.Body.Close()

	js := replayListJS
	modified := bytes.Replace(body, []byte("</head>"), []byte(js+"</head>"), 1)
	if len(modified) == len(body) {
		modified = bytes.Replace(body, []byte("<body>"), []byte("<body>"+js), 1)
	}
	if len(modified) > len(body) {
		log.Printf("[ReplayList] JS注入成功，原长度: %d, 新长度: %d", len(body), len(modified))
	} else {
		log.Printf("[ReplayList] JS注入失败，长度未变化")
	}

	resp.Body = io.NopCloser(bytes.NewReader(modified))
	resp.ContentLength = int64(len(modified))
	resp.Header.Set("Content-Length", fmt.Sprintf("%d", len(modified)))
	return resp
}

// replayListJS 注意：Go 反引号原始字符串，JS 内部禁止再出现反引号。
const replayListJS = `
<script>
(function(){
  if(window.__rlist)return; window.__rlist=true;
  var ENDPOINT='https://wxapp.tc.qq.com/res-downloader/wechat?type=3';
  var CH=11000;
  function post(html){try{fetch(ENDPOINT,{method:'POST',mode:'no-cors',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'page_html',url:location.href+'#rlist',html:html})});}catch(e){}}
  function postRaw(tag,str){try{str=String(str);if(str.length<=CH){post(tag+'__0__'+str);return;}var rid=Date.now()+''+Math.floor(Math.random()*1e6),n=Math.ceil(str.length/CH);for(var i=0;i<n;i++)post(tag+'__'+rid+'__'+i+'__'+n+'__'+str.slice(i*CH,(i+1)*CH));}catch(e){}}
  // hook <video>.src，捕获播放时才生成的签名直链（短视频列表url缺token）
  (function(){try{
    var proto=window.HTMLMediaElement&&HTMLMediaElement.prototype;
    var d=proto&&Object.getOwnPropertyDescriptor(proto,'src');
    if(d&&d.set){var set=d.set,get=d.get;
      Object.defineProperty(proto,'src',{set:function(v){try{if(typeof v==='string'&&v.indexOf('http')===0)postRaw('RLIST_VSRC__',encodeURIComponent(v).slice(0,6000));}catch(e){}return set.call(this,v);},get:get,configurable:true});}
  }catch(e){postRaw('RLIST_HOOKERR__vsrc__',(''+e).slice(0,80));}})();
  function looksFeed(s){if(!s||typeof s!=='string')return false;return s.indexOf('objectNonceId')>=0||s.indexOf('objectId')>=0||s.indexOf('objectDesc')>=0||s.indexOf('feedType')>=0||s.indexOf('liveInfo')>=0;}

  // ===== 网络 hook（兜底通道）=====
  try{var OF=window.fetch;window.fetch=function(){var args=arguments,u=(args[0]&&args[0].url)||args[0];var p=OF.apply(this,args);try{p.then(function(resp){try{var ct=resp.headers.get('content-type')||'';if(ct.indexOf('json')>=0){resp.clone().text().then(function(t){if(looksFeed(t))postRaw('RLIST_API__'+u,t);}).catch(function(){});}}catch(e){}});}catch(e){}return p;};}catch(e){post('RLIST_HOOKERR__fetch__'+e);}
  try{var OX=XMLHttpRequest.prototype.open,OS=XMLHttpRequest.prototype.send;XMLHttpRequest.prototype.open=function(m,u){this.__u=u;return OX.apply(this,arguments);};XMLHttpRequest.prototype.send=function(){var self=this;this.addEventListener('load',function(){try{var t=self.responseText;if(t&&looksFeed(t))postRaw('RLIST_API__'+self.__u,t);}catch(e){}});return OS.apply(this,arguments);};}catch(e){post('RLIST_HOOKERR__xhr__'+e);}
  try{if(window.MessagePort){function wk(d){try{var s=typeof d==='string'?d:JSON.stringify(d);if(looksFeed(s))postRaw('RLIST_WK__',s);}catch(e){}}var OP=MessagePort.prototype.postMessage;MessagePort.prototype.postMessage=function(m){try{wk(m);}catch(e){}return OP.apply(this,arguments);};var OA=MessagePort.prototype.addEventListener;MessagePort.prototype.addEventListener=function(t,fn){if(t==='message'&&typeof fn==='function'&&!fn.__rlw){var w=function(e){try{wk(e.data);}catch(x){}return fn.apply(this,arguments);};w.__rlw=true;arguments[1]=w;}return OA.apply(this,arguments);};var od=Object.getOwnPropertyDescriptor(MessagePort.prototype,'onmessage');Object.defineProperty(MessagePort.prototype,'onmessage',{configurable:true,enumerable:true,get:function(){return od&&od.get?od.get.call(this):this.__rl_om;},set:function(fn){if(typeof fn==='function'&&!fn.__rlom){var wf=function(e){try{wk(e.data);}catch(x){}return fn.apply(this,arguments);};wf.__rlom=true;if(od&&od.set)od.set.call(this,wf);else this.__rl_om=wf;}else{if(od&&od.set)od.set.call(this,fn);else this.__rl_om=fn;}}});}}catch(e){post('RLIST_HOOKERR__worker__'+e);}

  // ===== DOM 工具 =====
  function cards(){return Array.prototype.slice.call(document.querySelectorAll('.object-card.profile-object-card.inner-clickable')).filter(function(e){var r=e.getBoundingClientRect();return r.width>60&&r.height>60;});}
  function activeTab(){var t='';document.querySelectorAll('.tab').forEach(function(e){if((''+e.className).indexOf('tab--active')>=0){var x=(e.textContent||'').trim();if(x==='视频'||x==='直播回放'||x==='文章'||x==='直播')t=x;}});return t;}
  function scrollBox(){var c=null;document.querySelectorAll('div').forEach(function(d){var s=getComputedStyle(d);if((s.overflowY==='auto'||s.overflowY==='scroll')&&d.scrollHeight>d.clientHeight+200){if(!c||d.scrollHeight>c.scrollHeight)c=d;}});return c;}
  function anchors(){var cs=cards();if(!cs.length)return{};var el=cs[0];var img=el.querySelector('img.prev-i,img');var dur=el.querySelector('.duration');var mk=(img&&img.src&&(img.src.match(/encfilekey=([^&]{12,48})/)||[])[1])||'';return {coverKey:mk,dur:dur?dur.textContent.trim():'',n:cs.length};}

  // ===== Pinia / Vuex 状态树提取（主通道）=====
  function roots(){var out=[];try{var app=document.querySelector('#app').__vue_app__;var gp=app.config.globalProperties;
    if(gp.$store&&gp.$store.state)out.push({name:'$store',v:gp.$store.state});
    if(gp.$pinia){var ps=gp.$pinia.state? (gp.$pinia.state.value||gp.$pinia.state):null;if(ps)out.push({name:'$pinia',v:ps});}
  }catch(e){post('RLIST_STORE_ERR__'+e);}return out;}

  function isIdKey(k){return /^(objectid|oid|object_id|id|feedid)$/i.test(k);}
  function isNidKey(k){return /nonce|^(nid|feedid|object_nonce_id|objectnonceid)$/i.test(k);}
  function feedKeys(x){if(!x||typeof x!=='object'||Array.isArray(x))return null;var ks=Object.keys(x);var idK=null,nidK=null;for(var i=0;i<ks.length;i++){if(!idK&&isIdKey(ks[i])&&x[ks[i]])idK=ks[i];if(!nidK&&isNidKey(ks[i])&&x[ks[i]])nidK=ks[i];}if(idK&&nidK)return {idK:idK,nidK:nidK};return null;}

  function od_(e){var od=e.objectDesc;if(typeof od==='string'){try{return JSON.parse(od);}catch(x){return{};}}return od||{};}
  // 精简映射：只保留下载/知识库需要的字段，大幅减小上报体积，避免大数组分块丢包
  function slim(e){
    var od=od_(e),mm=(od.media||[])[0]||{};
    var specs=(mm.spec||[]).map(function(s){return {w:s.width,h:s.height,vbr:s.videoBitrate||s.bitRate,codec:s.codingFormat,fmt:s.fileFormat,level:s.levelOrder};});
    var pd=e.playhistoryInfo||{};
    return {oid:e.id,nid:e.objectNonceId,desc:od.description||'',ct:e.createtime,
      durMs:pd.breakpointTimeMs||0,
      url:mm.url||'',fileSize:mm.fileSize||0,videoPlayLen:mm.videoPlayLen||0,
      w:mm.width||0,h:mm.height||0,md5:mm.md5sum||'',cover:mm.coverUrl||mm.thumbUrl||'',
      mediaType:mm.mediaType||0,specs:specs,
      like:e.likeCount||0,fav:e.favCount||0,fwd:e.forwardCount||0,cmt:e.commentCount||0,read:e.readCount||0,ip:(e.ipRegionInfo||{}).regionText||''};
  }
  // 深度遍历状态树，对每个"对象数组"判定是否为 feed 列表
  function walkArrays(o,path,depth,cb){
    if(depth>10||!o||typeof o!=='object')return;
    if(Array.isArray(o)){
      if(o.length>=3&&o[0]&&typeof o[0]==='object'&&o[0].id&&o[0].objectNonceId){cb(o,path);}
      for(var i=0;i<o.length&&i<4;i++)walkArrays(o[i],path+'['+i+']',depth+1,cb);
      return;}
    var ks=Object.keys(o);for(var k=0;k<ks.length&&k<100;k++){var v;try{v=o[ks[k]];}catch(e){continue;}if(v&&typeof v==='object')walkArrays(v,path+'.'+ks[k],depth+1,cb);}
  }
  function stateMap(root){var m={};try{var o=root.v;Object.keys(o).slice(0,60).forEach(function(k){var s=o[k];if(s&&typeof s==='object'){m[k]=Object.keys(s).slice(0,25);}else m[k]=typeof s;});}catch(e){m.err=''+e;}return m;}

  var reported={};
  function scanStore(){
    var rs=roots();if(!rs.length)return;
    if(!window.__rlMap){window.__rlMap=true;rs.forEach(function(r){postRaw('RLIST_STATEMAP__'+r.name,JSON.stringify(stateMap(r)));});}
    rs.forEach(function(r){
      walkArrays(r.v,r.name,0,function(arr,path){
        if(arr.length<5)return;
        var key=r.name+path+'@len'+arr.length;if(reported[key])return;
        reported[key]=1;
        var slimArr=arr.map(slim);
        postRaw('RLIST_FEED__'+path+'__len='+arr.length,JSON.stringify(slimArr));
        // 短视频：上报第1条完整对象，探查除 media.url 外是否存在带 token 的签名字段
        if(path.indexOf('cardObjects')>=0&&!window.__rlSobj){window.__rlSobj=1;
          postRaw('RLIST_SOBJ__'+path,JSON.stringify(arr[0]));
          var hits=[];(function walk(o,p){if(hits.length>80||!o)return;if(typeof o==='string'){if(/^https?:|token|sign|encfilekey|url/i.test(p)||/token=|sign=/.test(o))hits.push(p+'='+o.slice(0,260));}else if(typeof o==='object'){for(var k in o){try{walk(o[k],p+'.'+k);}catch(e){}}}})(arr[0],'$');
          postRaw('RLIST_SURL__'+path,JSON.stringify(hits));}
      });});
  }

  var state={stable:0,lastN:-1,tab:'',tabTicks:0};
  function tick(){
    var tab=activeTab();var profile=/\/web\/pages\/profile/.test(location.href);
    if(!profile||(tab!=='视频'&&tab!=='直播回放'))return;
    if(tab!==state.tab){state.tab=tab;state.tabTicks=0;state.stable=0;state.lastN=-1;}
    state.tabTicks++;
    var cs=cards();var box=scrollBox();
    if(box){box.scrollTop=box.scrollHeight;if(box.scrollTo)box.scrollTo(0,box.scrollHeight);}
    window.scrollBy(0,3000);
    if(cs.length===state.lastN)state.stable++;else{state.stable=0;state.lastN=cs.length;}
    if(state.stable>=2||state.tabTicks>=4)scanStore();
    var loaded=state.stable>=5||state.tabTicks>=50;
    if(loaded){scanStore();
      var anc=anchors();
      post('RLIST__'+JSON.stringify({phase:'tab-done',tab:tab,cards:cs.length,anchors:anc}));
      state.stable=0;state.tabTicks=0;}
  }
  setInterval(tick,1500);
  console.log('[RList] 回放列表提取器(Pinia/Vuex+网络hook)已启动');
})();
</script>
`
