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

// injectShortProbeHook 注入"短视频播放换签探针"。
//
// 背景：视频号 profile 列表接口给出的 media.url 是缺 token 的 stodownload 直链（直接下载 403），
// 真正可播放的带 token/sign 直链只在用户点开短视频、播放器实际拉流时才生成。本探针全程静默：
// 不滚动、不点击、不导航、不发键盘事件，列表滚动与"点开播放"全部由人工控制。
//
// 多通道兜底（任一通道拿到带票据直链即可）：
//  1. HTMLMediaElement.src / currentSrc setter hook   —— 播放器直接挂 http 直链时
//  2. 轮询页面 <video> 的 src/currentSrc/readyState    —— 兜底属性赋值绕过 setter 的情况
//  3. URL.createObjectURL hook                         —— 判定是否 MSE(blob:) 拉流
//  4. performance.getEntriesByType('resource') 扫描     —— 拉流分片/直链即使走 MSE 也会留痕
//  5. fetch / XMLHttpRequest 响应 hook                 —— 播放接口 JSON(含 urlToken/media/decodeKey)
//  6. MessagePort(xweb.worker) 消息 hook                —— 网页版播放接口常走 worker port
//
// 注入范围覆盖 profile（列表与同页播放弹层）与 feed/home（独立播放 document）。
func (c *Captor) injectShortProbeHook(resp *http.Response) *http.Response {
	log.Printf("[ShortProbe] injectShortProbeHook被调用，URL: %s", resp.Request.URL.String())

	var reader io.Reader = resp.Body
	if strings.EqualFold(resp.Header.Get("Content-Encoding"), "gzip") {
		gz, err := gzip.NewReader(resp.Body)
		if err != nil {
			log.Printf("[ShortProbe] gzip解压失败: %v", err)
			return resp
		}
		defer gz.Close()
		reader = gz
		resp.Header.Del("Content-Encoding")
	}

	body, err := io.ReadAll(reader)
	if err != nil {
		log.Printf("[ShortProbe] 读取响应体失败: %v", err)
		return resp
	}
	resp.Body.Close()

	js := shortProbeJS
	modified := bytes.Replace(body, []byte("</head>"), []byte(js+"</head>"), 1)
	if len(modified) == len(body) {
		modified = bytes.Replace(body, []byte("<body>"), []byte("<body>"+js), 1)
	}
	if len(modified) > len(body) {
		log.Printf("[ShortProbe] JS注入成功，原长度: %d, 新长度: %d", len(body), len(modified))
	} else {
		log.Printf("[ShortProbe] JS注入失败，长度未变化")
	}

	resp.Body = io.NopCloser(bytes.NewReader(modified))
	resp.ContentLength = int64(len(modified))
	resp.Header.Set("Content-Length", fmt.Sprintf("%d", len(modified)))
	resp.Header.Set("Cache-Control", "no-cache, no-store, must-revalidate")
	resp.Header.Set("Pragma", "no-cache")
	return resp
}

// shortProbeJS 注意：Go 反引号原始字符串，JS 内部禁止再出现反引号，全部用单引号/字符串拼接。
const shortProbeJS = `
<script>
(function(){
  if(window.__sprobe)return; window.__sprobe=true;
  var ENDPOINT='https://wxapp.tc.qq.com/res-downloader/wechat?type=3';
  var CH=11000;
  function post(html){try{fetch(ENDPOINT,{method:'POST',mode:'no-cors',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:'page_html',url:location.href+'#sprobe',html:html})});}catch(e){}}
  function raw(tag,str){try{str=String(str);if(str.length<=CH){post(tag+'__0__'+str);return;}var rid=Date.now()+''+Math.floor(Math.random()*1e6),n=Math.ceil(str.length/CH);for(var i=0;i<n;i++)post('SPCHUNK__'+rid+'__'+i+'__'+n+'__'+str.slice(i*CH,(i+1)*CH));}catch(e){}}
  function j(tag,o){try{raw(tag,JSON.stringify(o));}catch(e){}}
  function hot(s){if(!s||typeof s!=='string')return false;return s.indexOf('stodownload')>=0||s.indexOf('urlToken')>=0||s.indexOf('decodeKey')>=0||/token=|sign=|videoUrl|playUrl|finder\.video\.qq\.com|findermp\.video\.qq\.com/.test(s);}

  raw('SP_INIT__',JSON.stringify({href:location.href,ua:navigator.userAgent.slice(0,120),t:Date.now(),videoCount:document.querySelectorAll('video').length,resCount:(performance.getEntriesByType('resource')||[]).length}));

  // 1) HTMLMediaElement.src / currentSrc setter
  try{
    var proto=window.HTMLMediaElement&&HTMLMediaElement.prototype;
    ['src'].forEach(function(prop){
      var d=Object.getOwnPropertyDescriptor(proto,prop);
      if(d&&d.set){var set=d.set,get=d.get;
        Object.defineProperty(proto,prop,{configurable:true,enumerable:true,get:function(){return get?get.call(this):this['__sp_'+prop];},
          set:function(v){try{if(typeof v==='string'&&v){j('SP_VSRC__',{url:v.slice(0,4000),isBlob:v.indexOf('blob:')===0,t:Date.now(),href:location.href});}}catch(e){}this['__sp_'+prop]=v;return set.call(this,v);}});}
    });
  }catch(e){raw('SP_HOOKERR__vsrc__',(''+e).slice(0,120));}

  // 2) 轮询 <video> 实际播放地址/就绪状态（去重）
  var vseen={};
  function pollVideo(){try{
    var vs=document.querySelectorAll('video');
    for(var i=0;i<vs.length;i++){var v=vs[i];var key=(v.currentSrc||v.src||'')+'|'+v.readyState+'|'+Math.round(v.currentTime||0);
      if(!v.currentSrc&&!v.src)continue;
      if(vseen[i]===key)continue;var prev=vseen[i];vseen[i]=key;
      j('SP_VPOLL__',{i:i,src:(v.src||'').slice(0,400),currentSrc:(v.currentSrc||'').slice(0,4000),isBlob:(v.currentSrc||v.src||'').indexOf('blob:')===0,readyState:v.readyState,duration:Math.round(v.duration||0),w:v.videoWidth,h:v.videoHeight,changed:!!prev,href:location.href});
    }}catch(e){}}
  setInterval(pollVideo,1000);

  // 3) URL.createObjectURL（MSE 判定）
  try{if(window.URL&&URL.createObjectURL){var OC=URL.createObjectURL.bind(URL);
    URL.createObjectURL=function(o){var u=OC(o);try{var mime=(o&&o.type)||'';var isMS=typeof window.MediaSource!=='undefined'&&(o instanceof MediaSource);j('SP_BLOB__',{url:(''+u).slice(0,80),mime:mime,isMediaSource:!!isMS,t:Date.now()});}catch(e){}return u;};}}catch(e){raw('SP_HOOKERR__blob__',(''+e).slice(0,120));}

  // 4) performance resource 扫描：真实拉流直链/分片（去重），区分视频(20302)与封面(20304)
  var rseen={};
  function scanRes(){try{performance.getEntriesByType('resource').forEach(function(en){var u=en.name||'';
    if(u.indexOf('video.qq.com')<0||u.indexOf('stodownload')<0)return;
    if(rseen[u])return;rseen[u]=1;
    var kind=u.indexOf('/20302/')>=0?'video':(u.indexOf('/20304/')>=0?'cover':'other');
    var hasTok=/token=/.test(u);
    j('SP_RES__',{kind:kind,hasToken:hasTok,url:u.slice(0,4000),initiatorType:en.initiatorType||'',dur:Math.round(en.duration||0),len:(en.transferSize||0),t:Date.now(),href:location.href});
  });}catch(e){}}
  setInterval(scanRes,1000);

  // 5) fetch hook
  try{var OF=window.fetch;window.fetch=function(){var args=arguments,u=(args[0]&&args[0].url)||args[0];var p=OF.apply(this,args);
    try{p.then(function(resp){var ct=resp.headers.get('content-type')||'';if(ct.indexOf('json')>=0||ct.indexOf('text')>=0){resp.clone().text().then(function(t){if(hot(t))raw('SP_API__'+u,t.slice(0,60000));}).catch(function(){});}}).catch(function(){});}catch(e){}
    return p;};}catch(e){raw('SP_HOOKERR__fetch__',(''+e).slice(0,120));}

  // 6) XHR hook
  try{var OX=XMLHttpRequest.prototype.open,OS=XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open=function(m,u){this.__su=u;return OX.apply(this,arguments);};
    XMLHttpRequest.prototype.send=function(){var self=this;this.addEventListener('load',function(){try{var t=self.responseText;if(t&&hot(t))raw('SP_XHR__'+self.__su,t.slice(0,60000));}catch(e){}});return OS.apply(this,arguments);};
  }catch(e){raw('SP_HOOKERR__xhr__',(''+e).slice(0,120));}

  // 7) MessagePort(xweb.worker) hook
  try{if(window.MessagePort){function wk(d,dir){try{var s=typeof d==='string'?d:JSON.stringify(d);if(hot(s))raw('SP_WK__'+dir+'__',s.slice(0,60000));}catch(e){}}
    var OP=MessagePort.prototype.postMessage;MessagePort.prototype.postMessage=function(m){try{wk(m,'REQ');}catch(e){}return OP.apply(this,arguments);};
    var OA=MessagePort.prototype.addEventListener;MessagePort.prototype.addEventListener=function(t,fn){if(t==='message'&&typeof fn==='function'&&!fn.__spw){var w=function(e){try{wk(e.data,'RSP_AE');}catch(x){}return fn.apply(this,arguments);};w.__spw=true;arguments[1]=w;}return OA.apply(this,arguments);};
    var od=Object.getOwnPropertyDescriptor(MessagePort.prototype,'onmessage');
    Object.defineProperty(MessagePort.prototype,'onmessage',{configurable:true,enumerable:true,get:function(){return od&&od.get?od.get.call(this):this.__sp_om;},
      set:function(fn){if(typeof fn==='function'&&!fn.__spom){var wf=function(e){try{wk(e.data,'RSP_OM');}catch(x){}return fn.apply(this,arguments);};wf.__spom=true;if(od&&od.set)od.set.call(this,wf);else this.__sp_om=wf;}else{if(od&&od.set)od.set.call(this,fn);else this.__sp_om=fn;}}});
  }}catch(e){raw('SP_HOOKERR__worker__',(''+e).slice(0,120));}

  // 8) 导航/hashchange（判断播放页 document）
  ['hashchange','popstate','pageshow'].forEach(function(ev){window.addEventListener(ev,function(){j('SP_NAV__',{ev:ev,href:location.href,t:Date.now()});});});

  console.log('[ShortProbe] 短视频播放换签探针已启动(静默,等待人工点开播放)');
})();
</script>
`
