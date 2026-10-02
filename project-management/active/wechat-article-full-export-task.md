# 公众号「顶底之王」全量历史文章导出 · Xcode 智能体交接任务书

> 更新：2026-10-02 ｜ 状态：**已完成：全量 278 篇确认已在本地存档，927 张配图全离线；方案 B（坐标视觉 RPA）最小闭环已验证（见 §3.3、§6）**
> 仓库根：`~/Desktop/multiplatform-content-pipeline/`（多机用 `$HOME` 派生，勿硬编码）
> Remote：`git@github.com:byte88/multiplatform-content-pipeline.git`（public）｜ HEAD：`e5da786`（已推送）

---

## 0. 给接手智能体的提示词（可直接粘贴到 Xcode 智能体对话）

> 你在本仓 `multiplatform-content-pipeline` 中工作。先完整阅读
> `project-management/active/wechat-article-full-export-task.md`（本文件）与
> `docs/guides/wechat-official-article.md`。目标：用**自研、不付费**方式，导出微信公众号
> 「顶底之王」（`__biz=MzUxODM4ODM5Mg==`）的**全量历史文章 `/s/` 链接清单（期望 278+ 篇）**。
> 正文逐篇抓取已验证可行，唯一未解决的是"如何枚举全量链接"。第 4 节列出的所有死路**禁止重试**；
> 请按第 6 节主攻 **CDP 远程调试 WeChatAppEx**（这是同类工具 wechatDownload「无需证书」的原理），
> 先做最小验证再落地，全过程保留证据、按里程碑 commit/push。允许我做轻量人工配合（重启微信、登录、
> 打开公众号窗口）。涉及微信客户端只做**只读观察与标准调试接口**，不反编译、不重签、不持续注入。

---

## 1. 项目总目标与本任务定位

- 总目标：自动化采集**各平台**（微信公众号 / 视频号，后续 B站 / 抖音 / YouTube 等）的视频与图文，
  转码转写，按行业组织成可复用知识库，并支撑量化系统与自有公众号/视频号文案生成。
- 平台采集层与后续处理（转写 / OCR / 知识库 / 撰稿）**解耦**；各平台采集个性、公共流程复用。
- **本任务＝一个点**：打通公众号全量历史文章导出。视频号采集已闭环（见 3.1），本任务独立推进。

## 2. 硬约束（不可违反）

1. **不付费、纯自研**；第三方工具（wechatDownload / wechat-article-exporter / 公号三刀 / JustOneAPI）
   只作**原理参考**，不依赖其付费服务。
2. 允许**轻量人工配合**（取 token / 重启微信 / 登录 / 打开窗口），但追求可脚本化、可复用。
3. 对微信客户端：**只读观察 + Chromium 标准调试接口**；**禁止**反编译、重签、Frida/LLDB 持续注入
   （曾触发风控，用户明确否决）。
4. ClashX、Tailscale **不得为采集而关闭**（双开是常态）；代码须**多机通用、配置化**，
   禁止硬编码 `/Users/<用户名>`，统一用 `$HOME` / `Path.home()`。
5. 视频默认**最低清晰度**；清晰度 / 目录 / 上游代理全部参数化；图文（mediaType=2）自动过滤；
   短视频 / 回放 / 图文必须**去重**。
6. 暂**不同步百度网盘**，等本地结构全部修正后再统一同步。
7. 中文回复；不确定明说；数字与结论须有来源或可复现计算。

## 3. 已验证闭环（直接复用，勿重做）

### 3.1 视频号「交易的游戏」采集（已完成）
- catalog / 磁盘 / inventory 三处对齐：**340 短视频 / 29 直播回放 / 1 图文**（图文已过滤），
  转写全齐，台账在 `library/00_manifest/`，HEAD `e5da786`。
- 靠自研 captor（Go MITM 代理）拦截微信 webview HTTPS 拿下，证明 **MITM + 已信任 CA 对微信 webview 有效**。

### 3.2 公众号单篇文章正文（始终可用）
- 拿到 `/s/xxx` URL 后，UA 伪装为 `MicroMessenger`（WindowsWechat 口径）直接 GET，
  即可取完整 HTML（含正文、图、视频），**无需凭证、不受频率限制**。
- 因此**只要有全量链接清单，正文导出立即打通**——链接清单是唯一卡点。

### 3.3 全量已在本地 + 方案 B 坐标视觉 RPA 闭环（2026-10 验证）
- **决定性结论**：`library/06_articles/stock/顶底之王/` 已有 **278 篇完整存档**（manifest 278 条、URL 唯一，含 article.html/article.json），链接枚举与正文采集**早已完成，无需重新采集**。
- 图片已全量离线：**927 张，0 在线、0 缺失**；276 篇有文字正文，1 篇纯图帖（image_ocr 齐全）、1 篇作者已清空的空帖。
- **方案 B（坐标视觉 RPA）最小闭环已验证**（用于新公众号 / 增量）：Android（免 root）上
  ① 坐标 `adb input tap` 可点开 native 自绘列表卡片；② 文章以标准 WebView 打开，CDP 可读完整 URL 与 `#js_content`；
  ③ `KEYCODE_BACK` 返回且位置保持；④ RapidOCR 以「阅读…赞…」为锚点定位标题。详见 SOP §3.2。

## 4. 已验证死路（禁止重试，附证据）

| # | 方向 | 结论 / 证据 |
|---|---|---|
| 1 | 自己公众号后台跨号 `searchbiz`/`appmsgpublish`（写文章→插超链接→搜别人号） | 微信 **2026-07-30 关闭**该接口，入口变灰；开源 wechat-article-exporter 因此**停止维护**，公告称"大概率不再开放、无法改代码绕过" |
| 2 | 外部 curl 带文章凭证（`__biz/key/uin/pass_ticket/appmsg_token`）调 `profile_ext?action=getmsg` | `ret=0 errmsg=ok` 但 **`msg_count=0`（空）**，服务端"礼貌置空"；证据 `video-capture/mp_articles_MzUxODM4ODM5Mg/page_000.json`（78 字节） |
| 3 | 直接把 `profile_ext?action=home&__biz=...` 发聊天框点开 | 微信 4.1.8 客户端识别为 deep link，**重定向成 native 公众号窗口**；webview 只请求 `channels.weixin.qq.com/web/pages/mp_profile?bizusername=...`（Vue/Vite SPA 空壳），**不发 getmsg** |
| 4 | 从文章 webview 内部点顶部公众号名进历史页 | 2026-09-25 实测：**仍重定向 native 窗口**（假设证伪） |
| 5 | MITM native「公众号」窗口 | 列表数据走 **native MMTLS 私有通道**，webview 仅空壳，HTTP 代理看不到列表 |
| 6 | 直读本地加密 SQLite 求全量 | biz/推送表**每号仅 1–2 篇**；2026-01 微信依法要求 GitHub 下架此类项目（chatlog 删库、连带 forks 清约 **4195 仓**）；且本地库只给标题/链接、**不给正文** |
| 7 | 搜狗微信搜索 | 仅少量旧文，非全量 |
| 8 | 反编译 / 重签微信 / Frida / LLDB 持续注入 | 触发风控，用户否决（见约束 3） |
| 9 | res-downloader / mitmproxy / tcpdump 当主依赖 | 视频流可捕获，**公众号历史列表不可**；且全局代理会干扰其他程序 |
| 10 | 追求完全无人值守 | 不现实：取短期 token 必须有一次轻量人工触发 |
| 11 | 只读扫描微信本地缓存 URL 提取 `uin/key/pass_ticket` 再调 getmsg（tingaidehua/wechat-article-downloader-skill 方法，Windows 2026-07 仍通） | **Mac 4.1.8 不成立**：受控实验（微信内打开 profile home 并滚动）后全盘扫描 `app_data`＋活跃账号 `xwechat_files`，**无任何 `action=getmsg` URL、无 appmsg_token/poc_token/poc_sid**；cgi-mapping 显示该类接口 `netproto=2`（native 私有长连接），URL/key 不落盘浏览器或 HTTP 缓存 |
| 12 | Android 外部存储 `bizcache/profile_resp_*`（滚到底后） | **只存第一页/概览**：顶底之王文件滚到底仅 42433→42640B（+207），归一化后仅 **12 篇唯一**；全量分页不落任何无 root 可读位置 |
| 13 | `uiautomator dump` 读历史列表 | 列表为**自绘 UI（非标准 View）**，dump 只得 1 个空 bounds 节点 |

## 5. 关键技术资产与 ID

**目标公众号「顶底之王」**
- 永久标识 `__biz=MzUxODM4ODM5Mg==`（＝后台 fakeid）
- bizusername `gh_896d89c7a603` ｜ 当前 uin `MjEzMDQ0MTk2MQ==`（数字 wxuin `2130441961`）
- 绑定视频号 finder username `v2_060000231003b20faec8c5ea881fcbd5cb04e83cb077320fa16b1f56ddc1a78ea74049b59102@finder`（视频号名「交易的游戏」）
- 仿名号（注意排除）：`MzkyODIxMjk5Ng==`（顶底之王策略）、`MzkyNTYwNDAyNw==`（顶底交割之王）
- 触发用主页链接（verbatim）：
  `https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=MzUxODM4ODM5Mg==&scene=124#wechat_redirect`
- native 窗口加载的 web 空壳：
  `https://channels.weixin.qq.com/web/pages/mp_profile?bizusername=gh_896d89c7a603`（约 4.1KB SPA 空壳）

**自研 captor（Go）**
- 目录 `platforms/wechat_channels/video-capture/`；CA `ca.crt/ca.key`（已加入系统信任）
- 源码：`main.go` / `captor.go` / `mp_article_export.go`（已实现 home→提取凭证→循环 getmsg 完整逻辑，
  **凭证提取可参考，但外部 getmsg 已证空**）/ `mp_profile_hook.go` / `proxy_darwin.go`（系统代理快照恢复）
- 启动示例：`./video-capture -port 8899 -output out.json -upstream http://127.0.0.1:7890`
  （`-upstream ""` 全直连）；停止用 `pkill -TERM -x video-capture`，**勿 SIGKILL**（防代理不恢复断网）
- 代理快照：`/tmp/captor_proxy_restore_<port>.json`，退出自动还原；只改物理网卡，Tailscale 等虚拟服务排除

**日志坑（重要）**
- captor api 日志含非 UTF8 字节，**Grep/ripgrep 会当二进制漏报 → 必须 Bash `grep -a`**
- 格式：`[time] GET host/path` → 下一行 Headers → `RESPONSE ... (status,len)` → `Body:`

**微信 webview 真实 UA（verbatim）**
`Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) MacWechat/3.8.7(0x13080712) UnifiedPCMacWechat(0xf264186b) XWEB/19708`
- 微信 App 版本 **4.1.8.107**；webview 进程名 **`WeChatAppEx`**（Chromium 内核，含 NetworkService/GPU/mojo 子进程）

**网络拓扑（本机＝wj，黑苹果 x86_64）**
- 物理网卡 `en0`（Ethernet）；ClashX 端口 `7890`（翻墙 / 系统代理）；Tailscale 为 utun（`100.109.91.22`）
- 预检脚本 `scripts/net_preflight.py`、配置 `config/network.json`；断网恢复＝还原系统代理，勿 SIGKILL captor

## 6. 下一步主攻：CDP 远程调试 WeChatAppEx

### 6.1 原理
- wechatDownload 号称「**无需安装证书，支持 macOS**」即可自动获取密钥——最合理的解释是它**不走 MITM**，
  而是用 Chromium 标准参数 `--remote-debugging-port` 启动微信 webview，再通过 **CDP（Chrome DevTools
  Protocol）** 直接读页面 DOM、网络请求、执行 JS。
- 现状（2026-09-25 探测）：当前 `WeChatAppEx` 启动**未带**该参数，无监听端口；9222/9229 等均无响应。
- 合规性：`--remote-debugging-port` 是 Chromium **官方标准调试接口**，非 hook / 反编译 / 重签，符合约束 3。
  旧教程多为 Windows/旧版微信，**Mac 微信 4.1.8 是否仍接受该参数需实测**（这是第一步）。

### 6.2 步骤（先最小验证，再落地）
1. **完全退出微信**（`Cmd+Q`）。
2. 带参重启，先验证参数是否透传到 WeChatAppEx：
   `open -a "微信" --args --remote-debugging-port=9222`
   - 登录后 `curl -s http://127.0.0.1:9222/json/version` 与 `/json`；
   - 若主进程**不透传**给 WeChatAppEx（无响应）：研究直接以该参数启动
     `WeChatAppEx`（`Contents/MacOS/WeChatAppEx.app/Contents/MacOS/WeChatAppEx`）的可行方式，
     或写一个启动 wrapper；记录可行做法。
3. 登录后打开「顶底之王」公众号历史窗口（即平时的 native 窗口）。
4. `curl http://127.0.0.1:9222/json` 枚举所有 targets：
   - **若公众号历史窗口在列**：用 CDP `Network` 域抓 `profile_ext/getmsg` 请求与响应；
     或 `Runtime.evaluate` 直接读取页面已渲染的全部列表项 / 在页面上下文调用历史分页接口。
   - **若 native 窗口不在列（纯原生 UI）**：在任一可达 webview target 上用 `Runtime.evaluate`
     执行 `fetch()`（携带该 webview 的微信 Cookie / 凭证）调 `profile_ext?action=getmsg`，
     观察是否能绕开第 4 节死路 2 的"外部 curl 空返回"（页面内同源 fetch 与外部 curl 口径可能不同）。
5. 将全量 `/s/` 链接、标题、发布时间落盘为 manifest（结构对齐 `library/00_manifest/` 现有口径）。

### 6.3 验证标准
- 能枚举并落盘 **278+ 条** `/s/` 链接，**去重后**数量与公众号实际群发文章数一致；
- 抽 3~5 条用 3.2 方法下载正文，确认链接有效、图文完整；
- 形成可复用、参数化（传入公众号名 / `__biz`）的采集模块，归位到对应平台插件目录；
- 若三种 CDP 路径（参数透传 / 直启 WeChatAppEx / 页面内 fetch）均失败，**记录硬证据与失败口径**，
  回到讨论再选方向（如微信读书收录、Windows 虚拟机等），不要静默宣称完成。

## 7. 落盘与目录规范（要点）

- 区分**原始资源**与**知识详解（知识库）**两层；现有 `library/` 已按 `01_video / 04_transcript /
  05_knowledge / 07_books` 等分层，新增内容沿用，勿另起散乱目录。
- 电子书籍 / 外部电子资料：统一原始目录后，再梳理进知识详解（珠宝同理，形成 SOP）。
- 过程性 / 临时文件不污染主目录；实验产物（当前工作区未跟踪的 `mp_articles*.json`、
  `mp_profile_clean.json`、`test_getmsg.py` 及 4 个改动的 `.go` 文件）由你判断：
  方案定稿后**有价值的整理提交、纯失败实验清理**，清理前列清单、不删用户原始数据。

## 8. 参考资料（URL）

- wechatDownload（支持 macOS、无需证书；重点参考其触发方式）：https://github.com/qiye45/wechatDownload
  - 其 skill 说明：https://raw.githubusercontent.com/qiye45/wechatDownload/main/skills/wechat-article-downloader/SKILL.md
- wechat-article-exporter（停维护公告）：https://github.com/wechat-article/wechat-article-exporter
- 公号三刀付费版取凭证教程（仅参考流程，不付费）：https://wechat.zoro.build/guide/first-sync
- 方案变更说明（2026-08-04）：https://mp.weixin.qq.com/s/pD-QXw7kGgDzBW19SAEzNQ
- 4195 仓下架报道：https://m.jiemian.com/article/13918617.html
- Xcode agentic coding（Claude Agent / Codex）：https://developer.apple.com/documentation/Xcode/setting-up-coding-intelligence

## 9. 验收清单

- [x] 全量链接清单：本地确认 **278 篇**（manifest 278、URL 唯一）
- [x] 抽样正文验证通过（图文完整）
- [x] 方案 B 最小闭环 + SOP/工具已参数化（`article-capture/`），支持新公众号；完整"一键采集器"可后续工程化
- [x] `docs/guides/wechat-official-article.md` 同步更新：死路标死路、新方案为标准流程
- [x] 已 git commit / push 到 public 仓（HEAD `6f88095`）
- [x] 汇报验证方式、覆盖范围、实际数量、遗留问题
