# 公众号文章采集SOP

> **文档类型**：SOP
> **更新时间**：2026-09-18
> **前置依赖**：[SOP-wechat-basic-operations.md](SOP-wechat-basic-operations.md)
> **目标公众号**：顶底之王（`__biz=MzUxODM4ODM5Mg==`），已有278篇URL在manifest中

---

## 快速参考

| 任务 | 方案 | 命令/方法 |
|------|------|----------|
| 增量发现新文章 | 方案A | `wx biz-articles --account "顶底之王" --limit 500 --json` |
| 下载文章正文 | 方案C | `curl -L -H "User-Agent: ...MicroMessenger..." -o article.html "URL"` |
| 全量采集新公众号 | 方案B | ⚠️ 当前不可用（appmsg_token代理捕获不到） |

---

## 1. 方案选择

| 方案 | 用途 | 状态 |
|------|------|------|
| **A: wx biz-articles** | 增量发现新文章（读本地缓存） | ✅ 推荐 |
| **B: video-capture全量** | 首次全量采集新公众号 | ❌ 当前不可用 |
| **C: UA伪装下载正文** | 获取单篇文章正文 | ✅ 通用 |

---

## 2. 方案A：增量发现（推荐）

微信本地数据库缓存了最近推送的公众号文章，用 `wx` 工具直接读取。

```bash
# 查询指定公众号最新文章
wx biz-articles --account "顶底之王" --limit 500 --json

# 对比manifest找新文章
# 现有URL集合 vs 最新文章列表，去掉chksm参数比较
```

**限制**：只能获取最近推送的1-5篇，无法全量历史。适合日常增量跟踪。

---

## 3. 方案C：下载文章正文（通用）

微信公众号文章反爬只检查UA是否含 `MicroMessenger`，不需要Cookie/登录/代理。

```bash
curl -L \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 MicroMessenger/8.0.34" \
  -o article.html "文章URL"
```

**解析要点**：
- 标题：`<h1 class="rich_media_title">`
- 正文：`<div id="js_content">`
- 图片：`data-src` 属性（不是 `src`）

---

## 4. 方案B：全量采集（当前不可用）

> ⚠️ **状态**：2026-09-17验证，微信4.x中 `appmsg_token` 通过内部API（xweb.worker）生成，不走HTTP，代理捕获不到，API返回 `msg_count=0`。

**原理**：用video-capture捕获文章列表API的参数（uin/key/pass_ticket/appmsg_token），再调 `profile_ext?action=getmsg` API翻页。

**流程概要**：
1. 启动video-capture（见 [channels-capture SOP](SOP-wechat-channels-capture.md)）
2. 在微信中打开公众号主页 → 点文章详情页 → 下拉刷新
3. 从日志中提取API参数
4. 调用 `profile_ext?action=getmsg` API翻页获取全部文章URL

**待解决**：appmsg_token无法通过代理捕获，需另寻方案。

---

## 5. 已验证死路（不要重试）

| 方案 | 原因 |
|------|------|
| mitmproxy系统代理 | 微信4.x主进程不走系统代理 |
| 微信数据库读文章列表 | 不缓存完整列表（biz-articles只读最近推送） |
| res-downloader抓文章列表 | 文章列表API不走系统代理 |
| 搜狗微信搜索 | 只能找到少量旧文章 |
| pfctl/tcpdump | 长连接无新TLS握手，无法解密 |
| appmsg_token代理捕获 | 微信4.x内部生成，不走HTTP |

---

## 6. 参考文档

- 微信基本操作：[SOP-wechat-basic-operations.md](SOP-wechat-basic-operations.md)
- 视频号采集：[SOP-wechat-channels-capture.md](SOP-wechat-channels-capture.md)
- wechat-control技能：`~/Doubao/skills/wechat-control/SKILL.md`
