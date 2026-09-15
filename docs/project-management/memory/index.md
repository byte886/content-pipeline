# 工程记忆 bundle（project-memory）

> 这是项目的**跨会话工程记忆入口**：把散落在 ADR / SOP / 代码里、跨会话仍有效的稳定结论"编译"成少量高密度 concept。
> 新会话恢复顺序：根 `AGENTS.md`（规则）→ 本页 index（有什么、在哪）→ 按需沿每篇的「来源与下钻」深读原始文档。
> 本 bundle 只做"结论 + 指针"，**不复制、不替代**原文；权威细节以被链接的源文档为准。易变状态（进度、计数、当天日期）不进本 bundle，需要时实时读台账。

---

# 架构（Architecture）

* [多平台内容流水线架构](concepts/architecture-multiplatform-pipeline.md) - 五层架构、平台插件化、行业隔离、方法提炼、library/00-08编号目录（ADR-004）
* [四地存储分工与仓库版图](concepts/architecture-storage-layout.md) - Git/本地data/网盘/飞书各放什么、什么才入库
* [工具运行目录与证书信任](concepts/architecture-tool-runtime.md) - 捕获工具必须从platforms/wechat_channels/video-capture/运行、证书路径坑、代理设置

# 链路（Workflow）

* [视频号采集链路](concepts/workflow-video-capture.md) - MITM捕获→下载→解密→验证、高质量URL参数
* [公众号文章采集链路](concepts/workflow-article-capture.md) - 文章下载→图片OCR→结构化存储
* [视频转文字与OCR链路](concepts/workflow-transcription-ocr.md) - FunASR本地转写、macOS Vision OCR、编译二进制提速

# 治理（Standard）

* [证书与代理核心规则](concepts/standard-cert-proxy.md) - 证书路径坑、全网阻断紧急恢复、代理设置
* [故障排查先验顺序](concepts/standard-debugging-first-principles.md) - 九成失败是自身问题、凭证最后怀疑

---

*最后更新：2026-09-15*
