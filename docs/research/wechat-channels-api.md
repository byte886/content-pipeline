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

### 6.2 B 方案已验证成功：直接调 Pinia action 翻页（不滚 DOM）

profile 页 Pinia 有 11 个 store，负责列表的是 **`profile` store**（经 `document.querySelector('#app').__vue_app__.config.globalProperties.$pinia._s.get('profile')` 获取）。

**state（列表与翻页游标/标志）**：
- 短视频：`cardObjects`（列表）、`noMore`（到底）、`isFetchingMore`（加载锁）、`refSessionBuffer`/`refObjectId`（翻页游标，action 内部自更新，无需手传）。
- 直播回放：`liveCardObjects`（列表）、`liveNoMore`、`isLiveFetchingMore`、`liveLastBuffer`。

**action（返回 Promise）**：
- 短视频翻页：**`fetchMoreData({username})`** —— 参数必须带 `{username}`（= `$state.username`，finder username）。
  - ⚠️ 空参 `fetchMoreData({})` 会**误把 `noMore` 置为 true 污染状态**，导致只拉一页就停；无参 `fetchMoreData()` 直接抛 `Cannot read properties of undefined (reading 'username')`。
  - 循环调用直到 `$state.noMore===true`，每次 await `isFetchingMore` 回 false。
- 直播回放：切到"直播回放"tab（点 `.tab` 中文案为"直播回放"的元素）后，**`liveCardObjects` 首屏即全量、`liveNoMore===true`**，通常无需翻页；如需补拉用 `getLiveUserPage()`。

实现见 `replay_list_hook.go` 的 `actionDrive()`（`-replay-list` 注入，进 profile 页自动执行）：先切"视频"tab → 循环 `fetchMoreData({username})` → 切"直播回放" → 读 `liveCardObjects`；进度经 `RLIST_DRIVE__` 上报，全量经 `RLIST_FEED__`（slim 映射，与旧滚动方案同格式，**下游解析/下载/解密管道不变**）。

**mediaType 口径**：`4`=视频，`2`=图文（采集视频时过滤图文）。

### 6.3 凭证（"刷新=换 token"）
视频号主页 URL：`channels.weixin.qq.com/web/pages/profile?username=v2_...@finder&exportkey=<...>&pass_ticket=<...>&wx_header=0`，Cookie 带 `sessionInfo=<...>`。
→ exportkey + pass_ticket + sessionInfo 就是进入凭证；刷新/重新点进视频号就是换这组凭证。**人工只需"搜博主→点进主页/刷新"这一下触发拿凭证，之后 action 翻页、下载、解密、转写全自动。**

### 6.4 视频文件
- 下载地址：`finder.video.qq.com/251/2030x/stodownload?encfilekey=<...>&token=<...>`
- **短视频**：Isaac64 流加密，仅前 128KB 加密，decode_key(9-10位数字) 作 seed 经官方 wasm `WxIsaac64.generate(131072)` 生成密钥流异或解密。
- **直播回放**：明文 MP4，无需解密。

### 6.5 全量对账（2026-09-21，交易的游戏，B 方案首次跑通）
| 列表 | action 驱动结果 | 构成 | 旧滚动 manifest | 结论 |
|---|---|---|---|---|
| 短视频 cardObjects | 340 | 339 视频(mediaType=4) + 1 图文(mediaType=2) | 339 shorts | 纯视频 **339 精确一致**，另识别出 1 条图文 |
| 直播回放 liveCardObjects | 28 | 28 全视频 | 27 replays | 多 1 场（新增回放） |

- 340 条 oid/nid 双唯一、零重复，`noMore` 由服务端置位 → **无遗漏、无重复，且天然可按 mediaType 过滤图文**。
- 台账 inventory 的 `short_total=410` 是**落库 mp4 文件口径**（含历史累积/重复/低清版本），非服务端列表全量，需以 action 全量（339 视频）为准重新对账；`live_total=25` 同样落后，应为 28。
- B 方案相比滚动：更快（短视频 22 次 action 调用、约 20–30s 拉完）、不依赖 DOM 滚动、不受懒加载/虚拟列表影响、数量由服务端 noMore 权威终止。

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
