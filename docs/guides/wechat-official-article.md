# 公众号文章采集SOP

> **文档类型**：场景SOP
> **前置依赖**：[wechat-basic-operations.md](wechat-basic-operations.md)，必读：§0工具选型、§1操作前准备、§2主窗口搜索流程、§3浏览器窗口通用规则；常见问题遇到再查

---

## 快速参考
| 任务 | 方案 | 命令/方法 |
|------|------|----------|
| 增量发现最新文章 | 方案A（推荐） | `wx biz-articles --account "<公众号名>" --limit 500 --json` |
| 下载单篇文章正文 | 方案C（通用） | UA伪装为微信客户端curl下载HTML |
| 新公众号全量历史文章 | 方案B | ❌ 当前不可用（appmsg_token无法通过代理捕获） |

---

## 1. 当前可用方案
### 1.1 方案A：增量发现新文章（推荐）
微信本地数据库缓存了最近推送的公众号文章，用wechat-control技能的`wx`工具直接读取：
```bash
wx biz-articles --account "<公众号名>" --limit 500 --json
```
对比已有manifest中的URL集合（去掉chksm参数比较）即可找出新文章。
> 限制：只能获取最近推送的1-5篇，无法获取全量历史，适合日常增量跟踪。

### 1.2 方案C：下载单篇文章正文（通用）
微信公众号文章反爬只检查User-Agent是否包含`MicroMessenger`，不需要Cookie/登录/代理：
```bash
curl -L \
  -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 MicroMessenger/8.0.34" \
  -o article.html "<文章URL>"
```
HTML解析要点：
- 标题：`<h1 class="rich_media_title">`
- 正文：`<div id="js_content">`
- 正文图片：使用`data-src`属性（不是普通`src`）

---

## 2. 已验证死路（禁止重试）
| 方案 | 失败原因 |
|------|------|
| mitmproxy/系统代理抓全量列表 | 微信4.x主进程文章列表API不走系统代理 |
| 读微信本地数据库拿全量列表 | 数据库只缓存最近1-5篇推送，不存完整历史列表 |
| res-downloader抓文章列表 | 文章列表API不走系统代理，捕获不到 |
| 搜狗微信搜索 | 只能找到少量旧文章，拿不到全量 |
| pfctl/tcpdump网卡抓包 | 长连接无新TLS握手，无法解密 |
| 捕获appmsg_token调官方API | 微信4.x中token由内部xweb.worker生成，不走HTTP，代理捕获不到 |

---

## 3. 参考
- 微信基础操作：[wechat-basic-operations.md](wechat-basic-operations.md)
- 视频号采集：[wechat-channels-capture.md](wechat-channels-capture.md)
- wechat-control技能：`~/Doubao/skills/wechat-control/SKILL.md`
