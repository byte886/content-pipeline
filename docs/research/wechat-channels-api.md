# 视频号API研究记录

> **文档类型**：技术研究
> **创建时间**：2026-09-15
> **状态**：研究中
> **目标**：找到可直接调用的视频号列表API，替代滚动页面采集

---

## 一、已发现的API端点

### 1.1 Web API（channels.weixin.qq.com）

| 端点 | 功能 | 来源 |
|------|------|------|
| `/web/api/feed/detail` | 获取视频详情 | CSDN博客（抓包分析） |
| `/web/api/feed/list` | 可能的视频列表 | 推测，待验证 |
| `/web/api/profile/feed` | 可能的主页视频列表 | 推测，待验证 |
| `/web/api/profile/info` | 可能的账号信息 | 推测，待验证 |

### 1.2 微信开放平台API（api.weixin.qq.com）

| 端点 | 功能 | 说明 |
|------|------|------|
| `/channels/ec/finderlive/getfinderliverecordlist` | 获取直播记录 | 官方API，需视频号助手权限 |
| `/channels/ec/promoter/get_feed_list` | 获取推广视频列表 | 电商带货相关 |

### 1.3 第三方API服务（付费）

| 服务 | 端点 | 价格 |
|------|------|------|
| TikHub.io | `/api/v2/wechat-channels/fetch_user_video_list` | 付费 |
| OneAPI | `/api/wechat-channels-v2/fetch_user_video_list` | 0.15元/次 |
| Apify | socialdatax-wechat-data-api | 付费 |

---

## 二、技术分析

### 2.1 视频号页面结构

视频号主页URL格式：
```
https://channels.weixin.qq.com/web/pages/profile?username=v2_xxx@finder
```

页面包含两个标签：
- **视频**：短视频列表
- **直播回放**：直播回放列表

### 2.2 可能的鉴权方式

视频号Web API很可能需要：
1. **Cookie**：微信登录态（`wxuin`、`wxsid`、`wxsticket`等）
2. **请求头签名**：可能有`x-sign`或类似签名头
3. **Token**：页面加载时生成的临时token

### 2.3 视频URL格式

```
https://finder.video.qq.com/251/20302/stodownload?encfilekey=<...>&token=<...>
```

- `encfilekey`：加密文件密钥
- `token`：访问令牌（有时效性）
- `DecodeKey`：视频解密密钥（9-10位数字，在视频详情数据中）

---

## 三、研究计划

### 阶段1：捕获API请求（当前）
- [ ] 启动MITM代理，访问视频号主页
- [ ] 记录所有`/web/api/`请求
- [ ] 分析返回数据结构
- [ ] 识别列表API和详情API

### 阶段2：分析鉴权机制
- [ ] 提取请求头和Cookie
- [ ] 分析签名算法（如有）
- [ ] 测试Cookie时效性

### 阶段3：直接调用API
- [ ] 用提取的Cookie直接调用列表API
- [ ] 测试分页参数
- [ ] 验证返回数据完整性

### 阶段4：集成到采集工具
- [ ] 如果API可行，替代滚动采集方案
- [ ] 实现纯API采集脚本
- [ ] 更新SOP文档

---

## 四、已知限制

1. **微信登录态**：API需要微信登录态，Cookie可能有时效性
2. **风控限制**：频繁调用可能触发微信风控
3. **接口变更**：微信可能随时变更API接口
4. **法律风险**：批量采集需注意微信服务条款

---

## 五、参考资料

- [微信视频号下载器API完全参考手册](https://blog.csdn.net/gitblog_00104/article/details/151919958)
- [抓包ck实现微信视频号视频下载](https://blog.csdn.net/m0_68138958/article/details/132333774)
- [微信开放社区 - 视频号API](https://developers.weixin.qq.com/doc/channels/api/)
- [RES Downloader GitHub](https://github.com/putyy/res-downloader)

---

*本文档随研究进展持续更新。*

---

## 六、深挖结论（2026-09-21，方案A逆向 B方案源头）

### 6.1 列表数据根本不走 HTTP
抓包日志（capture_full3_api.log）里**没有任何** `/web/api/feed/list` 类列表请求。视频号列表数据走两条非 HTTP 通道：
1. **XWEB 原生桥**：页面 `window.xweb.worker.port.postMessage({apiName:'...'})`，列表 RPC 由微信客户端原生层完成，MITM 抓不到 body。
2. **Vue3 / Pinia 状态树**：profile 页是 Vue3（`#app.__vue_app__`，globalProperties 有 `$store`/`$pinia`/`$router`），**列表 feed 数组最终落在 Pinia state 里**。

→ 这解释了"纯 HTTP API（appmsg_token）不可行"：列表不在网络层，拿 cookie curl 后端也没用。

### 6.2 已验证可行的"准 B 方案"（不滚 DOM，直接读状态树）
`replay_list_hook.go` 已实现：注入 JS 滚动加载卡片后，**深读 `$pinia.state` / `$store.state`**，用封面 encfilekey/时长作锚点定位 feed 数组，整块 JSON 上报（RLIST_FEEDARR）。这就是当前 339 短视频 + 27 回放的来源。比"读渲染好的 DOM"干净，但仍需滚动触发懒加载。

### 6.3 凭证（"刷新=换 token"）
视频号主页 URL：`channels.weixin.qq.com/web/pages/profile?username=v2_...@finder&exportkey=<...>&pass_ticket=<...>&wx_header=0`，Cookie 带 `sessionInfo=<...>`。
→ exportkey + pass_ticket + sessionInfo 就是进入凭证；刷新/重新点进视频号就是换这组凭证。

### 6.4 视频文件
- 下载地址：`finder.video.qq.com/251/2030x/stodownload?encfilekey=<...>&token=<...>`
- **短视频**：Isaac64 流加密，仅前 128KB 加密，decode_key(9-10位数字) 作 seed 经官方 wasm `WxIsaac64.generate(131072)` 生成密钥流异或解密。
- **直播回放**：明文 MP4，无需解密。

### 6.5 下一步（未完成）
- 找 Pinia 里的**翻页 action / cursor**，实现"不滚动、调 action 主动拉下一页"——这是 B 方案的终极简化。
- 需在微信里打开视频号、hook 翻页一次，录下列表 apiName 与 cursor 参数。

---

## 七、公众号文章 HTTP API（2026-09-21，与视频号区分）

> 关键区分：**公众号文章走 HTTP API，视频号不走 HTTP**。别混。

### 7.1 激活链接
```
https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=<BIZ>&scene=124#wechat_redirect
```
- `__biz` = 公众号唯一 ID（固定）。
- 把此链接发到文件传输助手 → 微信里打开激活 → 拿到 `appmsg_token` + `pass_ticket`。

### 7.2 文章列表接口（真 HTTP，不用滚页面）
```
GET https://mp.weixin.qq.com/mp/profile_ext?action=getmsg
  &__biz=<BIZ>
  &f=json
  &offset=<0开始，用返回里的下一页offset，非递增>
  &count=10
  &appmsg_token=<从激活页抓>
  &pass_ticket=<从激活页抓，几小时过期>
```
- 返回 json 含文章列表 + 下一页 offset。
- 循环到 offset 不再变化即到底。
- 另有公众号后台素材接口 `cgi-bin/appmsgpublish?sub=list&begin=&count=20`（需公众号自身登录态）。

### 7.3 与视频号的边界
- 公众号文章 = HTTP，可纯 API 翻页（本方案）。
- 视频号 = XWEB/Pinia，必须注入脚本（见 6.2）。
- 待实测：在微信里激活一次，抓 appmsg_token，跑 getmsg 翻页验证全量。
