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

---

## 已解决问题（Closed）

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

*最后更新：2026-09-17*
