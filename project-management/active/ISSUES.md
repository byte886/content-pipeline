# 问题清单（ISSUES）

> **文档类型**：Active（活态台账 — 实时更新）
> **更新频率**：发现问题/解决问题时立即更新
> **维护者**：AI自动维护

---

## 开放问题（Open）

### ISSUE-001: 捕获工具证书路径问题 ✅ 已解决
- **状态**：已修复（2026-09-15）
- **发现时间**：2026-09-15
- **问题描述**：捕获工具用相对路径`ca.crt`加载证书，从项目根目录运行时找不到`platforms/wechat_channels/video-capture/ca.crt`，会生成新的未信任证书，导致TLS握手失败、全网阻断。
- **根因**：`captor.go`的`loadOrGenerateCA()`用相对路径`"ca.crt"`
- **修复方案**：改为相对于可执行文件的路径（`os.Executable()` + `filepath.Dir()`）
- **验证**：从项目根目录运行，正确加载`platforms/wechat_channels/video-capture/ca.crt`，根目录不生成新证书

### ISSUE-002: 直播回放尚未转写（中优先级）
- **状态**：待启动
- **问题描述**：23个直播回放（每个1-3小时）尚未转写，转写时间较长
- **方案**：用FunASR批量转写，后台运行
- **预计耗时**：每个视频约10-30分钟（FunASR 9.7x实时）

### ISSUE-003: 高质量URL原始版本未找到（低优先级）
- **状态**：研究中
- **问题描述**：当前最大格式xWT111只有3.92MB，而元数据显示原始大小48.5MB
- **可能方向**：从objectDesc.media[0].spec数组中获取每个格式的独立URL
- **参考**：`docs/research/video-quality-url.md`

### ISSUE-004: 文章采集脚本目录统一 ✅ 已解决
- **状态**：已解决（2026-09-15，架构重构）
- **问题描述**：文章采集脚本在`scripts/article/`，与`tools/`目录分离
- **解决方案**：架构重构时迁移到`platforms/wechat_official/article/`，统一在平台插件目录下

### ISSUE-005: 2篇公众号文章无正文（低优先级）
- **状态**：待重新采集
- **问题描述**："每年12月哪个板块涨的最好？"和"春去冬来，顶底相伴，祝大家冬至快乐"无正文
- **方案**：重新采集这两篇

### ISSUE-010: GitHub仓库未改名（低优先级）
- **状态**：待处理
- **问题描述**：本地目录已改名为multiplatform-content-pipeline，但GitHub仓库还是stock-knowledge-base
- **原因**：GitHub API token有问题，无法通过API改名
- **方案**：手动在GitHub网页改名（Settings → Rename），旧URL会自动重定向，不影响git操作

### ISSUE-011: 数据未迁移到新结构（中优先级）
- **状态**：待执行（架构重构阶段2）
- **问题描述**：现有数据还在旧目录（data/videos、data/transcripts、knowledge-base/），新目录library/是空的
- **方案**：按DIRECTORY_STRUCTURE.md的迁移计划，复制+验证后清理旧目录
- **影响**：脚本中的默认路径还指向旧目录，迁移完成后需要更新脚本

### ISSUE-012: 平台插件接口待完善（中优先级）
- **状态**：待实现
- **问题描述**：platforms/base.py定义了统一接口，但wechat_official和wechat_channels还没有实现PlatformFetcher接口
- **方案**：先实现微信两个平台的Fetcher类，验证接口设计，再扩展到B站/抖音/YouTube

### ISSUE-013: 方法提炼LLM深度分析待实现（低优先级）
- **状态**：框架已搭，待接入LLM
- **问题描述**：processing/method_extraction/method_extractor.py框架已创建，但实际的方法提炼需要LLM深度分析
- **方案**：接入LLM，分析转写稿中的拍摄技巧、AI使用、内容呈现，提炼可复用的生成方法

### ISSUE-014: 百度凭证解密口令曾明文进入 public git 历史（高优先级·安全）✅ 已解决
- **状态**：✅ 已解决（2026-09-22：工作区止血 + filter-repo 全历史清除并强推，本地与全新克隆双路复验 0 命中）
- **发现时间**：2026-09-21（doc_health_check 首次扫描命中）
- **问题描述**：百度网盘加密凭证 `.secrets/baidu_credentials.enc` 的解密口令（与本机 sudo、GitHub PAT 解密口令相同）曾被硬编码在 `scripts/netdisk/sync_stock.sh`、`sync_library.sh`、`sync_netdisk.sh`、`baidu_upload.py` 示例中，并随多个历史提交推送到 public GitHub；同时 `.enc` 加密件本身也被跟踪入库，另有 3 个视频号捕获 JSON（含真实签名直链）曾入库。
- **处置（已全部完成）**：
  1. 工作区止血：4 个脚本改为强制从环境变量 `BAIDU_ENC_PASS` 读取（未设置即报错退出）；体检脚本把明文口令/票据列为 ERROR，弱口令检测规则改字面量拼接（规则自身不再含连续明文）。
  2. 入库策略收紧：`.gitignore` 改为整个 `.secrets/` 目录不入库（含 `.enc`，移除原先对 `*.enc` 的放行）；`.enc` 改为本地持有（工作区保留、仓外备份于 `~/.config/multiplatform-content-pipeline/.secrets/`）。
  3. 全历史重写：`git filter-repo --replace-text`（口令→`***REMOVED***`）+ `--invert-paths` 移除 `.secrets/` 与 3 个捕获 JSON（`capture_result_20260918.json`、`capture_wushi_20260918.json`、`capture_mp_credential.json`），改写全部提交哈希后 `--force` 强推 master（旧 HEAD `146e007` → 新 HEAD `55596ef`）。
  4. 复验：本地与"从 GitHub 全新克隆"双路全历史 `git grep` 口令 / PAT / 私钥 / 真实票据均 0 命中；`py_compile`、`bash -n`、captor `go build`、doc_health_check 全通过（0 ERROR/0 WARN）。
- **filter-repo 无法消除的残留风险（须知悉）**：
  1. 强推不保证已泄露副本消失：旧提交哈希在 GitHub 侧可能短时仍可经直接 URL/缓存访问，**已存在的 fork / 他人 clone / 第三方抓取不受影响、无法收回**。要彻底抹除 GitHub 侧残留需联系 GitHub Support 或删仓重建（会丢 issue/star，本次未做）。
  2. 用户决定**口令不更换**。鉴于口令与 `.enc` 曾同时公开，应按"百度凭证已等同泄露"处置：建议重新走一次百度网盘 OAuth 授权，使旧 access_token/refresh_token 失效（access_token 约 30 天自然过期，refresh_token 约 10 年；**重新授权是否立即作废旧 refresh_token 取决于百度规则，尚未实测、不确定**）。这是不改口令前提下最有效的补救。
  3. 其他机器/历史克隆无法 fast-forward，必须删除后重新克隆。
- **备份处置**：重写前全量兜底 `~/Desktop/mcp-PRE-CLEANUP-20260922.bundle`（8MB，**含原始敏感历史**）仅用于回滚；确认新仓无误后应删除，勿长期保留或外传。
- **关联**：ADR-003 密钥管理；`docs/项目维护SOP.md` 安全红线。

### ISSUE-015: sync_netdisk.sh 疑为高顿项目遗留脚本（低优先级）
- **状态**：待确认是否退役
- **问题描述**：`scripts/netdisk/sync_netdisk.sh` 引用 `data/_workspace/...`、`scripts/upload_course.sh`、`GAODUN_COURSE_PROFILE`，是高顿课程同步脚本复制而来，在本仓目录结构下疑似 0 引用、不可直接运行。
- **方案**：确认无引用后删除或迁入归档；当前仅已去除其中明文口令。

### ISSUE-016: 短视频重复文件去重、3场缺回放补下、inventory 台账重建（高优先级）
- **状态**：待执行（删除动作需用户确认）；方案见 `project-management/active/wechat-channels-dedup-and-inventory.md`
- **问题描述**：ffprobe 严格对账（catalog 339 短视频/28 回放为全集）确认：短视频 410 文件覆盖 339、0 缺、71 组各 2 个重复（71 个多余、约 300MB）；回放 25 文件缺 3 场（`1fb195bc2a6b5838` 上涨中继2266s、`6ea0215f7f0297e2` 再次缩量见底2415s、`bdfd5f9fb4fccd6d` 再次缩量见底2018s）。旧 inventory 台账 150 条 shorts encfilekey 为 null、lives 同名不同场次被错标同一 id，需按 catalog id 重建。
- **方案**：①新 hook 刷新换签（ISSUE-017）→ ②补 3 场回放并转写 → ③出 71 组 keep/drop 清单（keep 须解密可播放+有转写），用户确认后删视频并同步去重转写目录 → ④按 catalog id 重建 inventory，audit_disk.py 跑到缺/重/游离/歧义全 0。

---

## 已解决问题（Closed）

### ISSUE-017: 新 hook 一次刷新全量换签覆盖率验证 ✅
- **解决时间**：2026-09-22
- **结论**：方案 A（Pinia action 驱动，不滚 DOM、零播放）一次刷新即拿全全部可播放直链，**无需逐条播放或主动调 getObjectAsyncLoadInfo 换签**（RLIST_ACTSRC 作为备用手段保留）。
- **实测数据**（用户重进「交易的游戏」主页，新二进制 captor，日志 `/tmp/cap_iss017b_api.log`）：`all-done {short:340, live:28}`；parse 后 signed_coverage = 短视频 urlToken 339/339、decodeKey 339/339、回放 28/28。
- **关键修正**：回放对象是 slim 扁平结构，token 直接内嵌在顶层 `url`（`?encfilekey=…&token=…`），`urlToken` 字段留空、无 decodeKey（明文 MP4）；parse_capture_log.py 原用空 urlToken 误判回放未签名，已改为统一以最终 URL 是否含 `token=` 判定（commit a078a79）。
- **直链抽测**：短视频 HTTP 206 + 加密头 + decodeKey；3 场缺回放全 206、`ftyp` 明文头（适中档约 207–213MB/场，非 700MB 高清）。回放 id 经 `md5(md5)[:16]` 28/28 命中权威 catalog，缺的 3 场（1fb195bc/6ea0215f/bdfd5f9f）均在。
- **产物**：脱敏 catalog 刷新为全 has_signed（零票据，安全扫描 0 命中）；含票据清单落 `workspace/signed/`（gitignore，不入库）。

### ISSUE-006: 只设置Wi-Fi代理微信不走 ✅
- **解决时间**：2026-09-14
- **根因**：用户电脑实际使用Ethernet接口，微信走Ethernet
- **方案**：对所有活动网络服务同时设置HTTP/HTTPS代理

### ISSUE-007: 短视频加密无法播放 ✅
- **解决时间**：2026-09-14
- **根因**：微信短视频加密，DecodeKey→ISAAC64生成128KB数组→XOR文件前128KB
- **方案**：用Node.js封装`wechat_decrypt.js`，直播回放无DecodeKey无需解密

### ISSUE-008: 下载的视频只有2-5MB ✅
- **解决时间**：2026-09-14
- **根因**：默认下载低分辨率版本（xWT113）
- **方案**：用`quality=max`参数下载xWT111格式（大69%）

### ISSUE-009: OCR速度极慢 ✅
- **解决时间**：2026-09-15
- **根因**：swift解释执行每次都要编译
- **方案**：先用`swiftc -O`编译为二进制，速度提升10倍（1.5秒/张）

---

*最后更新：2026-09-22（ISSUE-017 验证闭环并移入 Closed；ISSUE-016 补回放进行中；ISSUE-014 历史清除完成）*
