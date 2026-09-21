# 任务状态台账（TASK_STATUS）

> **文档类型**：Status（状态台账，动态更新）
> **更新频率**：每个子任务完成时、遇到阻塞时
> **本页是"当前做什么、到哪"的唯一进度真相**
> 需求溯源看 `docs/REQUIREMENTS.md`，开放缺陷看 `project-management/active/ISSUES.md`
> 稳定结论的权威版在 ADR / 工程记忆，本页只放指针、不复制结论

---

## 当前进度总览

| 阶段 | 状态 | 说明 |
|------|------|------|
| ① 资源采集 | ✅ 完成 | 313短视频 + 23直播回放 + 278篇文章 |
| ② 内容处理 | ✅ 完成 | 短视频转写✅、图文OCR✅、直播回放转写✅ |
| ③ 知识提取 | 进行中 | 规则版已完成，LLM深度提取待接入 |
| ④ 知识库组织 | 方案就绪 | 待执行 |
| 项目治理 | ✅ 完成 | 文档架构、ADR、工程记忆、SOP |

---

## 进行中/待办工单

| 编号 | 标题 | 类型 | 状态 | 说明 |
|------|------|------|------|------|
| T-10 | 视频号API研究（方案B） | research | todo | 证书路径已修复，appmsg_token捕获已验证不可行，待另寻方案 |
| T-22 | 方法提炼（MethodNote）LLM分析 | feature | blocked | 框架已搭，抖音反爬403，等用户手动下载视频后继续 |
| T-31 | 指定博主全量采集 | feature | todo | 抖音反爬403，暂时跳过 |
| T-32 | 艺术/博物馆站点采集 | research | todo | 6个站点，待评估爬虫友好度 |
| T-33 | 视频提到的书籍收集 | feature | 进行中 | 5本完成，《广义趋势理论》待用户决策 |
| T-34 | 通用增量采集框架 | feature | ✅ 完成 | B站/YouTube验证通过，抖音/公众号/视频号待验证 |
| T-35 | 视频号短视频换签直链+Isaac64解密闭环 | feature | 进行中 | ✅解密算法与工具链已端到端验证（见 docs/research/wechat-short-video-decryption.md）；清单340短视频/27回放，当前15条短视频+27回放有换签直链可闭环，余约325条短视频需滚动/播放捕获换签；best_format高清md5对账待做 |

---

## 下一步（按优先级）

> **2026-09-18 更新：SOP瘦身完成，AGENTS/WORKFLOW通路去重完成**

1. **百度网盘统一重新同步**（用户明确暂停，等所有前置问题解决后统一执行）
2. **视频号增量采集验证**（框架就绪，需网络捕获元数据补充唯一ID）
3. **广义趋势理论课程**（用户决策是否付费获取）
4. **股票书籍知识详解生成**（13本书拆解）
5. **珠宝书籍补充**（当前0本）
6. **高质量URL原始版本研究**（当前2-5MB/个，真正原始48.5MB待找）

---

## 关键口径（指针，不展开）

- **视频解密原理（✅已验证）**：decode_key→WxIsaac64 生成128KB密钥流(reverse)→前128KB XOR → 见 `docs/research/wechat-short-video-decryption.md`（工具：`platforms/wechat_channels/video-downloader/`）
- **高质量URL参数**：X-snsvideoflag=xWT111 → 见 `docs/research/video-quality-url.md`
- **证书与代理方案**：相对可执行文件路径 + 上游代理 → 见 ADR-002
- **转写工具**：FunASR SenseVoiceSmall → 见 `processing/transcription/tools/`
- **OCR工具**：macOS Vision → 见 `processing/ocr/tools/`
- **存储分工**：GitHub(代码) / 本地library(数据) / 百度网盘(镜像) → 见 ADR-001

---

## 最近完成（2026-09-21）

- ✅ 视频号短视频解密闭环端到端验证：Isaac64 算法确认（非AES、仅前128KB加密）；仓内自包含 `decrypt_node.js` 与官方 wasm 密钥流逐字节一致；完整样本解密后 h264 1080x1920+aac、时长134.86s 与记录吻合
- ✅ 下载编排 `batch_download_v4.py` 修复（解密器同目录路径、可选代理 WC_PROXY、WC_LIMIT、md5 对账、规格差异标注）
- ✅ 捕获代理 `-short-probe` 静默探针落库换签直链+decode_key（captor.go/main.go/short_probe_hook.go，go vet/build 通过）
- ✅ 安全：含签名票据的捕获产物加入 video-capture/.gitignore，旧 capture_*.json 停止跟踪（git 历史清理待用户决策）
- 📄 新增权威技术文档 docs/research/wechat-short-video-decryption.md，采集SOP同步更新

---

## 最近完成（2026-09-18）

- ✅ SOP瘦身：三个微信SOP从1107行减到424行（-62%）
- ✅ AGENTS/WORKFLOW通路去重：工具索引精简，常见问题去重，章节引用修正
- ✅ REVIEW-governance-summary瘦身：577→~120行（-79%）
- ✅ DESIGN-knowledge-base-organization瘦身：443→~130行（-71%）

---

*最后更新：2026-09-21*
