# 公众号文章采集 SOP

> **文档类型**：场景 SOP
> **前置依赖**：[wechat-basic-operations.md](wechat-basic-operations.md)
> 必读 §0 工具选型、§1 操作前准备、§2 主窗口搜索流程、§3 浏览器窗口通用规则；其余遇到再查。

---

## 快速参考
| 任务 | 方案 | 方法 |
|------|------|------|
| 拿到某公众号全量历史文章 | **先查本地存档**；缺失再走方案 B（坐标视觉 RPA） | §1、§3 |
| 下载单篇文章正文 | UA 伪装微信直接 GET，无需凭证 | §2 |
| 正文图片离线化 | 下载 + HTML 改相对路径 + 更新元数据 | §4 |
| 日常增量跟踪新文章 | `wx biz-articles` 或方案 B 增量 | §3.3 |

---

## 1. 本地存档结构（动手前先查这里）

```
library/06_articles/<行业>/<公众号名>/
├── manifest.json                 # 全量文章台账（id/title/url/date/digest/cover/author）
└── articles/<YYYY-MM-DD>_<标题>/
    ├── article.html              # 完整原始 HTML（图片改为相对路径）
    ├── article.json              # 单篇元数据（content_length/image_count/image_remap/image_ocr）
    ├── content.md                # 提取的纯文字正文
    └── images/NN.ext             # 离线配图（01、02…，按正文出现顺序）
```

**「顶底之王」现状（2026-10 审计，已完整）**：278 篇文章、manifest 278 条、URL 唯一；
927 张配图全部离线（0 在线、0 缺失）；276 篇有文字正文；
1 篇纯图节日帖（图片 + image_ocr 齐全，无文字正文属正常）；
1 篇 `2021-12-02` 为作者已清空的真空帖（唯一）。

> 结论：**多数情况下全量早已采集，先核对本地，不要重复造全量采集器。**

---

## 2. 单篇正文（方案 C，通用）

公众号文章反爬只校验 UA 是否含 `MicroMessenger`，**不需要 Cookie / 登录 / 代理**：
```bash
curl -L -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) \
AppleWebKit/605.1.15 MicroMessenger/8.0.34" -o article.html "<文章URL>"
```
解析锚点：
- 标题：`<h1 class="rich_media_title">`
- 正文：`<div id="js_content">`
- 正文图片：用 `data-src`（不是 `src`）；`data:image/...` 是占位符，无需下载。

---

## 3. 全量历史文章

### 3.1 先查本地存档
按 §1 路径检查 `<公众号名>/manifest.json`，条目数与文章目录数一致即已全量。

### 3.2 方案 B：坐标视觉 RPA（已验证最小闭环）

历史列表是微信 **native 自绘界面（`ContactInfoUI`）**，不是标准 WebView，代理和 uiautomator 都拿不到；
但**屏幕坐标点击有效**。在一台开启 USB 调试的 Android（无需 root）上：

1. 微信内搜索并进入公众号 → 历史消息列表（native）；
2. **坐标 tap 卡片** → 文章以标准 WebView 打开；
3. 通过 **CDP** 读取该 WebView 的完整 URL（`mid/idx/sn/scene`）与 `#js_content` 正文；
4. `KEYCODE_BACK` 返回列表，**滚动位置保持**；
5. 用 **RapidOCR** 对列表截图定位卡片：以「阅读…赞…」元数据行为锚点，其上方紧邻长文本即标题，点标题中心；
6. 滚动加载下一页，循环 2–5，去重后落 `manifest.json`。

环境要点（具体值以现场为准）：
- 设备/屏幕：`adb devices` 取序列号；`adb shell wm size` 取分辨率；
- CDP：`adb forward tcp:<本地端口> localabstract:webview_devtools_remote_<微信主进程PID>`，访问 `http://127.0.0.1:<端口>/json`；
- OCR：RapidOCR（PP-OCRv6），需 Python 3.12（onnxruntime 不支持 3.14）；
- 参考实现：`platforms/wechat_channels/article-capture/`（`cdp.js`、`read_article.js`）。

### 3.3 增量
对比新抓到的 URL 集合与 manifest（去掉 `chksm` 等易变参数后比较），只处理新增条目；
日常 1–5 篇也可用 wechat-control 的 `wx biz-articles --account "<公众号名>" --json`。

---

## 4. 图片离线化（必做，已验证）

1. 扫描每篇 `#js_content` 内 `<img data-src>`，挑出 `http` 开头的在线图（有序、去重）；
2. 请求头：UA 含 `MicroMessenger`，`Referer: https://mp.weixin.qq.com/`；
3. 扩展名：URL 含 `mmbiz_png`→`.png`、`mmbiz_gif`→`.gif`、其余→`.jpg`；
4. 命名：**接续 `images/` 现有最大序号**（兼容 `01` 两位与 `000` 三位风格），不覆盖；
5. HTML 内把在线 URL 替换为 `images/NN.ext`，并**去掉相对路径上的 `?wx_fmt=...` 查询串**；
6. 更新 `article.json`：`image_count`（= images 文件数）、`image_remap`（{原URL: 文件名}）。

> 老帖 mmbiz 链接长期有效（2022 年帖实测仍可下载）；失败重试 1–2 次即可。

---

## 5. 已验证死路（禁止重试）

| 方案 | 失败原因 |
|------|------|
| 公众号后台跨号 searchbiz/appmsgpublish | 2026-07-30 被官方关闭，无法绕过 |
| 外部 curl 带残缺凭证调 getmsg | `ret=0` 但 `msg_count=0` |
| 外部浏览器/文件助手发 profile_ext home 链接 | 被 native 拦截为 ContactInfoUI，不产生带会话 WebView |
| mitmproxy / res-downloader / 系统代理抓列表 | 文章列表 API 不走系统代理 |
| Android 外部存储 bizcache | 滚到底仍只存第一页（顶底之王仅 12 篇、文件仅 +207B） |
| uiautomator dump 历史列表 | 自绘 UI，只得到空节点 |
| 读本地加密 SQLite 拿全量 | 只缓存最近 1–5 篇推送 |
| 捕获 appmsg_token 调官方 API | token 由内部 xweb.worker 生成，不走 HTTP |
| 搜狗微信搜索 | 仅少量旧文 |
| tcpdump / 网卡抓包解密 | 长连接无新握手，且内容加密 |
| 反编译 / 重签 / Frida / LLDB 注入 | 触发风控且有法律风险，禁用 |

---

## 6. 参考
- 微信基础操作：[wechat-basic-operations.md](wechat-basic-operations.md)
- 视频号采集：[wechat-channels-capture.md](wechat-channels-capture.md)
- 目录结构总览：[../DIRECTORY_STRUCTURE.md](../DIRECTORY_STRUCTURE.md)
- 全量导出任务书：`project-management/active/wechat-article-full-export-task.md`
- wechat-control 技能：`~/Doubao/skills/wechat-control/SKILL.md`
