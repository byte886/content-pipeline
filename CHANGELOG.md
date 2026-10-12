# CHANGELOG（编年体 · 只增不改）

> 格式：`YYYY-MM-DD ［类型］一句话（+影响/依据）`；类型 = 新增/变更/修复/废弃/移除。倒序编年（最新在上）。
> 历史说明：本仓此前无根级 CHANGELOG，变更记录由 `docs/HANDOFF.md`（倒序活日志）承担；自 2026-10-08 起以本文件为根级显著变更台账（HANDOFF 偏接手上下文，职能不同）。

## 2026-10-12

- ［新增］转写近重复普查脚本与全库普查报告：郭颖作品 238 / 唯一内容 234（commit a376236）。
- ［新增］视频画面 dHash 普查脚本：近重复报告由"文本单维度"升级为"文本+画面双维度"（commit a31ec39）。
- ［新增］视频资产台账元数据入库：`manifest.csv` 16 列字段定义 + 五档价值分级与 A/B/C 评级 SOP（`docs/guides/video-asset-manifest.md`）+ xlsx→manifest 同步对账脚本 `scripts/xlsx_to_manifest.py`（commit 00993e6）。
- ［变更］视频资产来源索引补全：登记宝石学家老许 B站 744、交易的游戏视频号 336；注明 json 历史富清单与 csv 新统一台账并存（commit 967c85b）。
- ［新增］郭颖 B 级首批 10 条创作对标：下载转写完成、双轨预处理脚本入库、台账对账通过（248/248）（commit 4f22a38、3d220e1）。
- ［新增］郭颖 B 级剩余 73 条续采：6 批次方案（拍卖天价/明星品牌/文化寓意/原石猎奇/钻石蓝宝/玉石珍珠南红）→ 全量下载+转写+双轨分析+创作对标完成，台账回写、manifest 对账通过（commit 7b19a77、127c0e8）。
- ［修复］`scripts/.../video_dual_analysis_prep.py` 第 106 行死代码 bug（随 B 级续采收尾一并修复，commit 127c0e8）。
- ［维护］全仓评审与治理同步：①P0死链3处修复（architecture-storage-layout→ADR-001实际名 / DOCUMENTATION_MAP移除不存在SOP / project-management README移除legacy）②ISSUES关闭3条（010/011/015）+已✅项移Closed+新增ISSUE-018~020待拍板 ③TASK_STATUS刷新（T-31/37/38/39补登、T-39 mp_verify消解、新增评审行）④CHANGELOG补登10-09以来变更 ⑤旧仓名与迁移阶段修正（memory concept）⑥DIRECTORY_STRUCTURE/ROADMAP/REQUIREMENTS状态刷新 ⑦导航补全（docs README/DOCUMENTATION_MAP/memory index/WORKFLOW日期）⑧domains README 修正。
- ［新增］新立 `project-management/decisions/ADR-005-仓库二次改名留痕（multiplatform-content-pipeline→content-pipeline）.md`（Status: Accepted），为 2026-10-09 二次改名补 ADR 留痕（ISSUE-020 closed）；project-management/README.md ADR 范围更新为 ADR-001~005。
- ［维护］评审待拍板三项收尾（用户拍板"全部执行"）：①heritage 总域正式登记——根 README.md domains 行、DIRECTORY_STRUCTURE.md 目录树补 6 子域段、DOCUMENTATION_MAP.md 新增「行业知识域导航」条目（ISSUE-018 closed）；②HANDOFF.md 补 10 月倒序条目（10-09 T-31+二次改名 / 10-11 T-37+T-38+T-39 / 10-12 台账+B级对标+治理同步）、§0「现在在」刷新，恢复交接主通道（ISSUE-019 closed）；③AGENTS.md §1.1 冷启动段加跨体系薄指针（先读总控仓 ~/Desktop/control-tower/README.md）。
- ［维护］文档层遗留项清理（评审 D-P2-3 / S-P2-1）：①`docs/DOCUMENTATION_MAP.md` 三处「技能路径/」占位精确化为 `~/Doubao/skills/multiplatform-media-fetch/…`（author-video-knowledge-base.md 校正到 references/pipeline/；extract_keyframes.py 本仓外 skill 内未定位到，标注路径待核实）；②裸 basename 引用补全仓库相对路径——TASK_STATUS.md（audit_disk.py/incremental_sync.py/rebuild_inventory.py/parse_capture_log.py/audit_交易的游戏.json/captor.go 等）、ISSUES.md（rebuild_inventory.py/parse_capture_log.py/audit_交易的游戏.json/dedup_plan_交易的游戏.json/short-dedup-checklist.md）、wechat-channels-dedup-and-inventory.md（inventory/audit_交易的游戏.json/audit_disk.py/batch_download_v4.py/incremental_sync.py）；③本轮改正文的 memory concept `architecture-multiplatform-pipeline.md` frontmatter `last_updated` 滚至 2026-10-12（另两篇无该字段，按"字段名以既有为准"不新增）；④`config/sources.json` 新增 douyin 源条目（珠宝学者郭颖，sec_uid/URL/chrome_profile 等待真实源数据补录，不臆造）。
- ［新增］鉴藏知识库云文档组织落地：云盘归档与组织规则（AI 工作守则）+「鉴藏知识库·孵化」容器（00_组织方法 / 01_鉴藏知识·郭颖 23 份 / 02_内容方法 / 03_案例对标）+ 珠宝电商 00_索引挂载（commit 9e1799d）。
- ［新增］视频知识工作流融合规划 + P1 工作流骨架：七阶段 S0–S7 + 决策门 G0–G6 + 多模态路由（视频/音频/PDF/图片/文本/图文）+ 待办登记（commit 8a730e8）。
- ［维护］workflow/README 补登记 workflow-main 并写明三层文档分工（概览/详设/SOP）与 AI 接手顺序（commit dabc6fa）。
- ［变更］文稿用途分型入工作流：读者/知识/运营/视频创作四型，同步 G0 目标形态 + G4 成文决策 + S4 校验门（commit c78bc5b）。
- ［新增］文档治理补强：ADR-006 文稿用途分型决策 + `project-management/standards/DOCUMENTATION_PRINCIPLES.md`（类型词典/落位决策表/README 防则），ADR-001 加演进注记（commit 5281516）。
- ［维护］晚间独立旁观者评审 A-1~A-6 修正（commit 51a6d86，评审报告见 `project-management/reviews/2026-10-12-evening-independent-audit.md`）：①新增 `library/README.md`（编号体系表 00_manifest~08_sources + 03 跳号说明 + 各目录一句话用途）②`TASK_STATUS.md` 当前进度总览改七阶段视角（对齐 WORKFLOW.md S0–S7，四阶段降为历史口径，信息保留）③`AGENTS.md` §2.4 补 `DOCUMENTATION_PRINCIPLES.md` 必读指针 ④新增 `domains/README.md`（jewelry 过渡保留 / stock 旧域仍活跃去留待用户拍板 / heritage 总域 6 子域）⑤`docs/guides/wechat-official-article.md` data URI 占位词改述——doc_health_check 0 ERROR / 0 WARN。
- ［新增］P2 首批交付（2026-10-12 晚）：①抖音评论采集——脚本 `collect_douyin_comments.py`（匿名档优先、只读低频串行、单会话 ≤15 条）+ 参考文档 `references/platforms/douyin-comments-extract.md`（均落技能仓 multiplatform-media-fetch），实采郭颖置顶片 6 条入库 `library/08_sources/douyin_comments/7474846772968426811_comments.json`；②四类多模态素材接入端到端验收——音频（byted-mediakit-audio Cloud 鉴权实测可用、异步需 query-task，+ FunASR 转写样例 `library/02_audio/jewelry/_pipeline验证/`）、PDF（PyMuPDF 提取 txt/JSON，`library/07_books/stock/extracted/`；扫描件分支待真实扫描样例）、图片（image-ocr Cloud + 本地 `ocr_vision` 兜底，单图勿用视频流水线脚本）、公众号正文链路（`06_articles/<行业>/<公众号名>/` 现成产物复核，`wechat_official/` 空目录勿用）；③小红书图文 note 采集端待核（规划 §12-⑩，需真实带 xsec_token 笔记 URL）；④规划 §5.4 路由表状态列、§11 待办（T04/T20–T23）、§12 待核（⑧销号、新增⑩）、workflow-main 相应小节、TASK_STATUS S1/S2 全部更新。
- ［新增］P2 续项（2026-10-12 晚）：T05——B站评论 `collect_bilibili_comments.py`（游客 buvid + `x/v2/reply`，纯 API 直连强制绕代理）+ 参考文档 `references/platforms/bilibili-comments-extract.md`（技能仓），实采老许 BV1kK4y1w7UN 顶层 3 条入库 `library/08_sources/bilibili_comments/`；微信视频号评论正文抽取坐实"仅计数入台账、需人工开窗 + captor 新增评论列表 hook"；YouTube 评论评估=yt-dlp `--dump-json` comments 需代理，暂缓（待核⑦已评估）。T06——小红书 collect_comments 接入方案（产物 normalize 成 canonical 补 comment_id/reply_count/meta + 滚动封顶 ≤3 页），文档落技能仓 `references/platforms/xiaohongshu-comments-pipeline.md`；实采因账号违规预警冷却期（7–14 天第 5 天）+ 缺真实 xsec_token 链接标「待用户提供链接」（⑩）。
- ［新增］P3 先行评估（2026-10-12 晚）：`docs/workflow/article-to-okf-bridge.md` 方案落盘——现状修正（老许 20 篇已是 `type: ArticleNote` draft、顶底之王 277 篇无 frontmatter、与 concepts bundle 孤儿断链，"0 ArticleNote"结论修正为"缺桥不缺格式"）、ArticleNote 形态定稿（新增 `kind:` 模态键）、manifest 双向指针协议（`fused_into`）、跨模态 src 标签协议（src-douyin / src-bili-video / src-bili-opus / src-wechat / src-xhs / src-pdf / src-audio / src-transcript / src-ocr）、增量归并原则（并入为主）；试点 2 条（stock 公众号 + 老许 B站图文）通过 `okf_validate` E0·W0；批量执行待拍板 3 项（顶底之王 277 篇 wrap / `articles/` 落点 / `kind:` 键）。

## 2026-10-09

- ［变更］仓库改名 `multiplatform-content-pipeline → content-pipeline`（用户拍板：原名过长；content-pipeline 为英文标准术语、砍掉 multiplatform 隐含属性、与体系 2 词命名风格统一）。GitHub rename + 本地目录 mv + remote set-url + 全链指针同步（含 we-media-ops 子模块 URL）。

## 2026-10-08

- ［变更］`docs/SYSTEM_ARCHITECTURE.md` 降级为薄指针：五仓体系总览 / 职责表 / 产物驱动对接 / 任务路由 / 跨仓纪律的权威正文迁移至五仓总控仓 `~/Desktop/system-architecture/`（`README.md` + `docs/五层现状总表.md`），本仓不再单独维护以避免双写漂移；降级前 v1 全文归档至 `docs/archive/SYSTEM_ARCHITECTURE_v1_full_2026-10-08.md`（头部注明归档日期/降级原因/新权威源路径）
- ［新增］根目录 `CHANGELOG.md`（本文件）：此前本仓无根级变更日志，由 `docs/HANDOFF.md` 倒序活日志替代，自今日起显著变更在本文件登记
- ［变更］`README.md` 快速导航表总控仓那行措辞微调：反映"体系架构正文以总控仓为准、本仓 SYSTEM_ARCHITECTURE.md 为薄指针"
- ［备注］既有 9 个未提交文件（本次**不代提交**，待该仓维护时处理）：
  - Modified：`AGENTS.md`、`docs/DOCUMENTATION_MAP.md`、`docs/WORKFLOW.md`、`domains/jewelry/README.md`、`platforms/douyin/README.md`
  - Untracked：`library/05_knowledge/jewelry/郭颖/`、`library/jewelry/`、`platforms/douyin/COLLECT_SOP.md`、`platforms/douyin/scripts/`
