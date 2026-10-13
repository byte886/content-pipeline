# 任务状态台账（TASK_STATUS）

> **文档类型**：Status（状态台账，动态更新）
> **更新频率**：每个子任务完成时、遇到阻塞时
> **本页是"当前做什么、到哪"的唯一进度真相**
> 需求溯源看 `docs/REQUIREMENTS.md`，开放缺陷看 `project-management/active/ISSUES.md`
> 稳定结论的权威版在 ADR / 工程记忆，本页只放指针、不复制结论

---

## 当前进度总览（七阶段视角，与 docs/WORKFLOW.md S0–S7 对齐）

| 阶段 | 状态 | 说明 |
|------|------|------|
| S0 任务定义与预判 | ✅ 骨架完成 | P1 已交付：决策门 G0–G6 成文（`docs/workflow/workflow-main.md`，含素材类型分路/多模态路由/任务卡字段）；多智能体编排试点待 P7 |
| S1 采集 | 进行中 | 视频号权威全集 **340短视频/29回放/1图文**（catalog 09-23），磁盘 340+29 全有、去重干净（ISSUE-016/017 已闭环）；郭颖 A 类 46 补采 + B 级 73 续采完成；公众号文章待全量导出；**P2 首批 ✅（2026-10-12）：抖音评论实采（6 条入库）+ 音频/PDF/图片/公众号链路验收**；**P2 续 ✅/🔵：B站评论游客 API 实采 3 条入库、小红书接入方案已定（实采待用户提供真实链接）、视频号正文待人工开窗** |
| S2 内容提取 | ✅ 视频链路完成 / 多模态 ✅ | 转写 **340+29 全齐**（含 09-23 新增 live_029），图文 OCR ✅；郭颖 192+46 转写；多模态提取（音频/PDF/图片/图文）✅ P2 首批验收（中间物样例见规划 §5.4） |
| S3 多媒体分析 | 进行中 | 视频效果分析判型与双轨 SOP 已沉淀；郭颖 B 级 10 条创作对标已交 video-studio；行业×需求矩阵成文待 P5 |
| S4 最终文稿 | 部分 | article-pipeline 已沉淀（7 类作者角色），06_articles 298 篇；文稿用途分型（读者/知识/运营/视频创作）已入工作流（ADR-006）；**文稿→OKF 融合桥 ✅ P3 完成（278 wrap + 278 原子页 + 老许 20→5 topics + fused_into 298/298）** |
| S5 知识化（OKF） | 基本完成 | 郭颖 23 份知识文档 + 吸收对账 193 条零遗漏；老许 744 篇 draft；规则版知识提取完成，LLM 深度提取待接入（T-22）；**跨模态归并已落地（P3）：stock 278 原子页 + 老许 20→5 topics** |
| S6 质检迭代 | 部分 | 机械门可执行（okf_validate / doc_health / 双维查重）；吸收对账固化、人工复核 verified、评估 Agent 待 P4 |
| S7 云文档发布维护 | 部分 | 组织守则 + 「鉴藏知识库·孵化」容器已落地；残留/过时/重复维护机制待 P6 |
| 项目治理 | ✅ 完成 | 文档架构、ADR、工程记忆、SOP |
| 全仓评审与治理维护（2026-10-12） | ✅ 完成 | 白天三层评审闭环（MD 链接 0 断链、.gitignore 合规、ISSUE-018~020 拍板收尾）；晚间独立旁观者评审 A-1~A-6 已修正（见 `project-management/reviews/2026-10-12-evening-independent-audit.md`） |
| P2 首批（评论采集 + 多模态接入，2026-10-12 晚） | ✅ 首批交付 | 抖音 `collect_douyin_comments.py` 匿名档实采 6 条入库 `library/08_sources/douyin_comments/`；音频（mediakit+FunASR）/ PDF（PyMuPDF）/ 图片（Cloud OCR + ocr_vision 兜底）/ 公众号链路端到端验证；小红书图文 note 采集端待核（规划 §12-⑩）；T05/T06（B 站/视频号评论、小红书评论接入）待续 |
| P2 续 + P3 先行评估（2026-10-12 晚，历史） | 🔵 部分交付 | T05 ✅：B站 `collect_bilibili_comments.py` 游客 API 实采 3 条入库（BV1kK4y1w7UN），视频号正文待人工开窗+captor hook，YouTube 评估暂缓（⑦）；T06 🔵：小红书 normalize 方案已定（canonical + ≤3 页封顶），实采按用户原则"只处理已得原数据"保持设计就绪（⑩，2026-10-13 澄清）；P3 🔵 先行评估：`article-to-okf-bridge.md` 方案 + 试点 2 条 E0W0（后续批量执行见上行） |
| P3 批量执行（2026-10-13，历史） | ✅ 完成 | ①顶底之王 **278 篇 wrap**（wrapper `scripts/wrap_wechat_articles.py`，6 批 50/50/50/50/50/28、幂等、正文一字未动、逐批校验；`article_278` None 条有内容按同规则 wrap；4 条 unknown-date 存量条目按同规则处理）；②stock concepts 骨架 + **278 原子页**（两线并行提炼，正文=编译摘要+要点+来源指针，不复制全文）；③老许 20 篇按实际珠宝主题归入 **5 个既有 topic**（未新建）+ meta.json `fused_into` 回填；④对账：fused_into **298/298 闭合**、stock `okf_validate` **E0·W0·I278**（index 已登记）、jewelry E0（W721 存量孤儿非本次引入）、`doc_health_check` 0 ERROR；仅知识层+文档+脚本入 git，06_articles 留本地不入库 |
| K 线·知识化统一（2026-10-13） | ✅ K1 规划落盘 | **用户指示：所有知识化工作归并为统一规划**。K1 已交付 `docs/workflow/知识化总规划-2026-10-13.md`：类型词表（新增 BookNote/CourseNote）、BookNote/CourseNote frontmatter 规范、批量流程（两段式≤50/批/E0/对账）、课程清洗门 G7、云同步顺序（K5）、任务重排（K2 书籍线→K3 课程线→K4 质检→K5 云同步；原 P4/P6 并入，P5/P7/P8 保留）。资产实况实测：07_books 689 文件（jewelry 654/stock 34，git 0）、04_transcript 96 集 ASR 初稿（"已词典清洗"待核）。待拍板 7 项见规划 §6 |
| K2 书籍线 OKF 化（2026-10-13，并行批） | ✅ 完成 | **220 个 BookNote 原子页**（stock 13 全量＋jewelry 精选 207＝212 源 md 去重 5 对同源后 207）落 `05_knowledge/{stock,jewelry}/concepts/books/`，两 bundle `okf_validate` **E=0**（books 页零 W60/I11/W81）；**评估课件 419 索引级登记**（`_课件索引/` 总览＋5 日期卷，按需提炼）；随手项：⑤ `~/Doubao/library/07_books/` 空壳目录已清、⑥ 5 对同名提取物 difflib ≥99.98% 判同源重复（未删）、⑦ 宋元耳环 caj 原件归位 `07_books/jewelry/raw/`（BookNote src-extract 路径已同步） |
| K3 课程线 OKF 化（2026-10-13，并行批） | ✅ 完成 | **107 个 CourseNote 原子页**（jewelry 96＝82 鉴藏讲＋11 翡翠物语＋3 样本单列＋stock 顶底之王 11）落 `05_knowledge/{jewelry,stock}/concepts/courses/`，双 courses/index 登记，`okf_validate` **E=0**；**前置核实③结论**：课程目录无 manifest.json/"转写字数_清洗后_P0.5"字段（待核①）；md 实况＝ASR 控制符 0 残留但语气词/同音误字/翡翠物语英文＋假名残留 → 107 页均 `clean:false` **待清洗（K4 承接）**；stock/交易的游戏已提取（short 313＋live 24）按指令跳过 |
| K4 质检加固（2026-10-13，吸收原 P4） | ✅ 完成 | **课程清洗**：107 篇转写备份 107/107→确定性清洗（语气词删 5825/假名 270/英文碎片 230＋白名单误字归并，技术词保全）→courses 页 **clean:true 84、待核 23**（翡翠物语 11＋误字 12，不冒充）→courses E0。**其余项**：fused_into **298/298 双向闭合**复核＋固化脚本；一致性检查脚本（野脚注 0，558 条 provenance 属设计）；顶底之王 **278 篇补 stale_after 2027-01-01**（不补 verified）；老许 topics verified 核对一致；郭颖不凭空加 verified、3 篇价格类待核；`verified-stale-rule.md`＋`evaluation-agent-template.md` 成文；金融炼金术 pdf/mobi **判重同源 99.87%→合并互指零删除**。两 bundle **E0、无新增 W60/I11** |
| K6 云文档治理收尾（2026-10-13） | ✅ 完成 | 00_索引补老许 topics 与 stock 容器两入口（更新孵化条目描述）；《如何组织》增补「六、并行知识域（domain）与同步原则」5 条（一域一 bundle+一容器、draft 不同步/stable 才同步/选择性同步、串行导入、四处登记）；写入前重读/写入后复验 |
| 278 篇 AI 核验（2026-10-13） | ✅ 全量完成 | 试点 26 篇误判率 0%→全量铺开：①抽取器修复（折行合并，`scripts/recompile_article_atoms.py`）重编译 14 篇旧模板折行页；②全量机械核验（`scripts/verify_article_atoms.py`）272 通过/6 异常全处置，**0 编造/0 数字造假**；③howto 9 篇判定 0 新增 stable（7 篇含时点行情）；④unknown 回填 3 篇/留 1；最终 **stable=2/draft=276/待核=1**；⑤2 篇 stable 已同步 stock 容器（云索引就地更新）；E=0 |
| P5 方法提炼·试点执行（2026-10-13） | ✅ 完成 | 建 `jewelry/concepts/methods/`（index 无 frontmatter）；**M1/M2 stable**（3-4 独立源、E0W0）并同步云盘博主研究；M3/M5 后于 P7 升 stable，M4 仅候选登记；02_内容方法 README 补条目；效果数据待核 |
| P7 多智能体编排试点（2026-10-13） | ✅ 完成 | 固化编排 SOP `docs/workflow/multi-agent-orchestration.md`（七角色/六任务卡/G0–G7/回退挂起/冷启动七步）；干跑 M3/M5 逐句对源核验升 stable（verified ai:doubao）并同步云盘（M3/M5 两 URL）；发现 3 缺口已回写 SOP（verified 块式静默丢弃/效果数据本地源/block-id 失效）；E0W0 | 老许 topics **11 页同步**（stable，落 `01_鉴藏知识/宝石学家老许`，10 主题页+导航全导入 docx）；郭颖 23 份**核验一致**未重传；**stock 容器新建**（孵化根下 `股票投资知识库（stock）`）：README+顶底之王 **278 篇索引**（draft 不同步，原子页暂缓）；books/courses **精选 4 本**（大作手回忆录/缠中说禅108课/金融炼金术/系统宝石学），课程章节卡与 draft 书卡暂缓登记；**README-鉴藏知识库已更新**（结构图+进度+日期+K5 callout，写入前重读/编辑后复验） |

> **历史口径**：旧四阶段（① 资源采集 → ② 内容处理 → ③ 知识提取 → ④ 知识库组织）已并入七阶段视角（①≈S1、②≈S2、③≈S3+S5、④≈S5+S7）；各阶段明细见下文工单表与「最近完成」。

---

## 进行中/待办工单

| 编号 | 标题 | 类型 | 状态 | 说明 |
|------|------|------|------|------|
| T-10 | 视频号API研究（方案B） | research | ✅ B方案验证成功 | 列表不走HTTP，走XWEB桥+Pinia；**已验证直接调 `profile.fetchMoreData({username})` 翻页到 noMore、回放切tab首屏即全量，不滚DOM**。实测340视频+1图文/回放29（09-23 增量后）。✅ 2026-09-22 已用 ffprobe 严格对账（`platforms/wechat_channels/video-downloader/audit_disk.py`）：短视频339全有/0缺/71重复、回放缺3，权威基准落 `library/00_manifest/catalog_交易的游戏.json`，报告落 `library/00_manifest/audit_交易的游戏.json` |
| T-22 | 方法提炼（MethodNote）LLM分析 | feature | blocked | 框架已搭；郭颖 6 个测试视频已下载转写，LLM 分析可对已转写样本先行；全量待批量下载后继续 |
| T-31 | 指定博主全量采集（郭颖） | feature | ✅ 完成 | **2026-10-09 全部完成**：**192 视频全部转写（transcript 入库）并完成知识文档化，形成 17 份综合《知识文档》**——145 条高价值科普归并为 **14 份品类文档**（钻石、翡翠、和田玉、彩色宝石×2〔贵重/常见与平替〕、综合文化、水晶、珍珠、黄金贵金属、南红玛瑙、绿松石、蜜蜡琥珀、有机宝石化石、青金石）；46 条潘家园实战归并为 **3 份实战手册**（淘货方法论与案例、分品类玉石类、分品类宝石与有机宝石类）；另 1 条《品鉴价值三个亿的翡翠》即早期《翡翠组配用料溢价》源视频，内容已并入《翡翠-知识文档》。早期 6 份单主题文档保留、内容已并入综合稿。均已 commit/push |
| T-32 | 艺术/博物馆站点采集 | research | todo | 6个站点，待评估爬虫友好度 |
| T-33 | 视频提到的书籍收集 | feature | 进行中 | 5本完成，《广义趋势理论》待用户决策 |
| T-34 | 通用增量采集框架 | feature | ✅ 完成 | B站/YouTube验证通过；视频号 `platforms/wechat_channels/video-downloader/incremental_sync.py` 已于 09-23 实跑成功（对账补下 live_029） |
| T-35 | 视频号短视频换签直链+Isaac64解密闭环 | feature | 进行中 | ✅解密算法与工具链已端到端验证（见 docs/research/wechat-short-video-decryption.md）；slim() 已补 urlToken/decodeKey/cdnFileSize/hlsSpec + 新增 probeSignActions（RLIST_ACTSRC），go build 通过；**ISSUE-017 已闭环（09-22）：一次刷新全量换签、urlToken/decodeKey 全覆盖**，近100%即一次刷新拿全，否则据 ACTSRC 对缺签条目逐条换签；best_format高清md5对账（ISSUE-003）后做 |
| T-36 | 去重/补3场回放/台账重建 | feature | ✅ 完成 | ISSUE-016 已闭环（09-22）；方案见 `wechat-channels-dedup-and-inventory.md`（ISSUE-016）：刷新换签→补3场回放+转写→用户确认后删71重复视频并同步去重转写→按catalog id重建inventory至audit全0 |
| T-37 | 郭颖「普通展示」187条逐条复查 + 知识库入口 | feature | ✅ 完成 | 2026-10-11：187 条逐条语义分级并回写台账（新增 review_grade/review_topic/review_note 三列，xlsx 本地）：**A 建议补采 46 / B 可选 83 / C 不采 58**；产出《普通展示187条筛查报告.md》；参照会计知识库范式为郭颖目录建入口《README.md》（17 份文档地图+存储分工+可信度约定+使用指南）。commit 21e93ac |
| T-38 | 郭颖 A 类 46 条补采与文档归并 | feature | ✅ 完成 | 2026-10-12：依 T-37 复查结论，补采 A 类 46 条（彩宝8/钻石11/翡翠6/和田玉5/珍珠6/黄金7/综合3）：浏览器取流（currentSrc+__vid 铁证法，修正预加载流串流）→FunASR 转写（转写即内容验证，名不副实降级）→按 review_topic 并入对应品类文档；批4-7 共 21 条归并（commit 881494e，T-38 全部完成）。B 类 83 留档按需取，C 类 58+节日6+广告2 放弃 |
| T-39 | 全知识源入口导航 + 知识源组织 SOP | feature | ✅ 完成 | 2026-10-11：参照会计知识库治理范式，为 `05_knowledge/` 全部知识源补导航入口（知识层总入口、jewelry 行业入口、老许 OKF concepts 入口、stock 入口），不移动文件/不改成品；新增落地 SOP `docs/guides/knowledge-source-organization.md`（三层解耦/两种成品形态/入口模板/draft→stable/新增博主 Checklist/质检清单）并登记 DOCUMENTATION_MAP；补登记 archive 旧架构消除 1 个历史体检 ERROR；OKF 校验 E=0、新增文件零新增断链。commit 4a9c359。**遗留（非阻塞）**：老许 10 篇 topics 主题页仍为占位、723 篇 draft 待第二步语义加工。（原遗留待拍板项：`platforms/wechat_channels/video-capture/mp_verify_20261002.json` 疑似票据入库——2026-10-12 核实该文件未被 git 跟踪，体检 ERROR 已自动消解，关闭） |

---

## 下一步（按优先级）

> **2026-09-23 更新：视频号「交易的游戏」已全量闭环——340 短视频 / 29 回放全部下载、转写，audit 缺/重/游离/歧义全 0，inventory 重建。下一步首要 = 公众号文章全量导出（需用户 GUI 配合触发拿凭证一次，之后全自动）。新会话从这里接手。**

1. **公众号文章全量导出（HTTP API，待实测）**：`profile_ext?action=home` 激活拿 `__biz/appmsg_token/pass_ticket`，再 `action=getmsg`（offset 取返回的下一页值、count=10、offset 不变即到底）；专档 `project-management/active/wechat-article-full-export-task.md`；人工只触发拿 token 一下，之后全自动。
   - 若标准 HTTP 路线仍不通，参考 wechat-article-exporter 作者付费版的取凭证方法：https://wechat.zoro.build/guide/first-sync （SPA，需 Chrome 渲染）。
   - ✅ 已完成前置：ISSUE-017 一次刷新全量换签、ISSUE-016 去重/补回放/台账重建（视频号 340/29 全齐）。
2. **百度网盘统一重新同步**（用户明确暂停，等所有前置解决后统一执行；股票/珠宝各开应用，视频原片曾出现空目录需检查，直播回放同步位置待核）
3. **股票书籍知识详解 + 《广义趋势理论》《金融炼金术》**：用户称已拿到两本电子版、晚点提供；桌面 `~/Desktop/股票书籍/` 10 个 PDF/PPTX，扫描件走 RapidOCR（work-doc-extract 技能，Python3.12 venv）；电子资料单独目录统一放、梳理后进知识详解，珠宝同理形成 SOP
4. **高质量URL原始版本研究**（当前 min 2–5MB/个，真正原始 48.5MB 待找，ISSUE-003，best_format md5 对账）

---

## 关键口径（指针，不展开）

- **视频解密原理（✅已验证）**：decode_key→WxIsaac64 生成128KB密钥流(reverse)→前128KB XOR → 见 `docs/research/wechat-short-video-decryption.md`（工具：`platforms/wechat_channels/video-downloader/`）
- **高质量URL参数**：X-snsvideoflag=xWT111 → 见 `docs/research/video-quality-url.md`
- **证书与代理方案**：相对可执行文件路径 + 上游代理 → 见 ADR-002
- **转写工具**：FunASR SenseVoiceSmall（共享venv `~/.venvs/funasr`）→ 见 `docs/guides/audio-transcription.md`，批量脚本 `platforms/wechat_channels/video-transcribe/batch_transcribe.py`
- **OCR工具**：macOS Vision → 见 `processing/ocr/tools/`
- **存储分工**：GitHub(代码) / 本地library(数据) / 百度网盘(镜像) → 见 ADR-001

---

## 最近完成（2026-10-12）

- ✅ **T-38 郭颖 A 类 46 条补采与文档归并（全部完成）**：依 T-37 复查结论补采 A 类 46 条（彩宝8/钻石11/翡翠6/和田玉5/珍珠6/黄金7/综合3），浏览器取流改用 currentSrc+__vid 铁证法（修正预加载流串流）→FunASR 转写→按 review_topic 并入对应品类文档；批4-7 共 21 条归并（commit 881494e，T-38 全部完成）。
- 🗂️ **视频资产台账与普查工具入库**：manifest.csv 元数据入库 + 价值评级 SOP（`docs/guides/video-asset-manifest.md`）+ xlsx→manifest 同步对账脚本；转写近重复普查（作品238/唯一内容234）、视频画面 dHash 普查（文本+画面双维度）；补全来源索引（老许 B站744 / 交易的游戏视频号336）；B级首批10条创作对标 + 剩余73条续采完成，修复 `video_dual_analysis_prep.py:106` 死代码（commit 127c0e8）。
- ✅ **评审待拍板三项收尾（用户拍板"全部执行"）**：①heritage 总域正式登记三份导航（README/DIRECTORY_STRUCTURE/DOCUMENTATION_MAP，ISSUE-018 closed）；②HANDOFF 补 10 月倒序条目、恢复交接主通道（ISSUE-019 closed）；③新立 ADR-005 为二次改名留痕（ISSUE-020 closed）。

## 最近完成（2026-10-11）

- ✅ **T-37 郭颖「普通展示」187条逐条复查 + 知识库入口**：187 条逐条语义分级并回写台账（新增 review_grade/review_topic/review_note 三列）：**A 补采46 / B 可选83 / C 不采58**；产出《普通展示187条筛查报告.md》；为郭颖目录建入口 README（17 份文档地图+存储分工+可信度约定）。commit 21e93ac。
- ✅ **T-39 全知识源入口导航 + 知识源组织 SOP**：为 `05_knowledge/` 全部知识源补导航入口（知识层总入口/jewelry 行业入口/老许 OKF concepts 入口/stock 入口）；新增落地 SOP `docs/guides/knowledge-source-organization.md` 并登记 DOCUMENTATION_MAP。commit 4a9c359。

## 最近完成（2026-10-09）

- ✅ **T-31 指定博主全量采集（郭颖）全部完成**：192 视频全部转写零失败（transcript 入库）并完成知识文档化，形成 17 份综合《知识文档》——145 条高价值科普归并 14 份品类文档、46 条潘家园实战归并 3 份实战手册（commit de247d6 转写完成 / 5b60876 T-31 全部完成）。

---

## 最近完成（2026-09-23）

- ✅ **视频号「交易的游戏」增量收尾（全量闭环）**：重跑全量捕获（action 驱动翻页 + 换签），catalog = 340 短视频 / 29 回放 / 1 图文（mediaType=2 已过滤）。脚本现算对齐 inventory/catalog/磁盘：短视频 340 磁盘/转写全有（台账文字 339 为滞后口径）；唯一新增为回放 live_029。
- ⬇️ `platforms/wechat_channels/video-downloader/incremental_sync.py` 实跑：补下载 live_029「上涨中继」（2182s、190.3MB 明文 MP4，ftyp 校验通过，md5 `6eecb32403c1`，直连），FunASR 转写 28646 字。
- 🧮 audit_disk：短视频 340/340、回放 29/29，缺/重/游离/歧义全 0；`platforms/wechat_channels/video-downloader/rebuild_inventory.py` 重建台账（short 1804MB / live 6296MB，转写 340+29 全齐）。原料（视频/转写）按 .gitignore 不入库，仅台账（catalog/audit/inventory）入库。

---

## 最近完成（2026-09-22）

- 🔐 **ISSUE-014 凭证明文历史清除（filter-repo 全历史重写 + 强推）**：全历史扫描锁定敏感面（明文口令、被跟踪的 `.secrets/baidu_credentials.enc`、3 个含真实签名直链的捕获 JSON；无 PAT/私钥/百度 token 明文，"AKIA" 为 wasm 误报）；`.gitignore` 收紧为**整个 `.secrets/` 不入库**、`.enc` 本地持有（仓外备份 `~/.config/content-pipeline/.secrets/`）；体检弱口令检测改字面量拼接；`git filter-repo --replace-text + --invert-paths` 重写全部提交并 `--force` 强推（旧 HEAD `146e007` → 新 HEAD `55596ef`）；本地与"从 GitHub 全新克隆"双路全历史 grep 口令/PAT/私钥/真实票据均 **0 命中**，py/sh/go 构建与体检全过（0 ERROR/0 WARN）。
  - **残留动作（非阻塞）**：①建议重新走百度 OAuth 授权作废旧 token（口令用户选择不改，这是最有效补救；refresh_token 约 10 年，重新授权是否立即作废旧 refresh 未实测）；②确认新仓无误后删除桌面兜底 `mcp-PRE-CLEANUP-20260922.bundle`（含原始敏感历史）；③其他机器的旧克隆需删除重克隆。详见 ISSUE-014。
- 🧮 **视频号文件盘严格对账 + 全量基准落库（方案 A 离线收尾）**：固化 `platforms/wechat_channels/video-capture/parse_capture_log.py`（重组 captor `_api.log` 的整块/分块 payload，产出脱敏 catalog + 含票据 signed 两份分离，复刻 id=md5(md5sum)[:16]）与 `platforms/wechat_channels/video-downloader/audit_disk.py`（ffprobe 时长+归一化标题+hashtag 消歧，文件盘 vs catalog 对账，带时长缓存）。权威基准落 `library/00_manifest/catalog_交易的游戏.json`（339 短视频/28 回放/1 图文，零签名）、报告落 `library/00_manifest/audit_交易的游戏.json`。结论：**短视频 339 全有、0 缺、0 游离、71 组各 2 个重复（71 个多余、约 300MB）；回放 28 缺 3、0 重复**。多匹配 short_055/short_311 已用 hashtag 消歧为两条不同视频。修复 `platforms/wechat_channels/video-downloader/incremental_sync.py` 三处 `live`→`lives` 键 bug（待 dry-run）。改 `platforms/wechat_channels/video-capture/replay_list_hook.go` slim 增换签字段 + probeSignActions（go build 通过，待刷新验证 → ISSUE-017）。去重/补回放/台账重建方案见 ISSUE-016。

---

## 最近完成（2026-09-21）

- ✅ **新窗口接手闭环建成（对标 astock-quant）**：新增 `docs/项目维护SOP.md`（SSOT 路由/维护节奏/冷启动六问/提交检查）、`docs/新窗口接手开场白.md`（开窗触发词+收口四步+标准句+六问验收+换机兜底）、`docs/HANDOFF.md`（30秒画像+倒序日志+当前纠结+产物地图）、`scripts/doc_health_check.py`（核心文件/断链/登记/禁入内容/明文凭证检查，0 ERROR 才提交）；AGENTS §1.1 冷启动六问、§2.7 体检门，README「🚑新会话快速恢复」，DOCUMENTATION_MAP 全部登记
- 🔧 **体检首跑 43 ERROR 全部清零（复检 0 ERROR / 0 WARN）**：修复 docs/README 8 条旧文件名断链、design 文档 3 条缺 `../`、memory/index 3 个不存在的幽灵 concept 链接、解密研究文档漏登记；珠宝知识成品 videos 下 20 个 md 相对链接多一层 `../`（`../../topics/`→`../topics/`）；**4 个网盘脚本明文解密口令止血（改环境变量强制）→ ISSUE-014 已于 2026-09-22 filter-repo 全历史清除并强推（见上"最近完成 2026-09-22"）**；sync_netdisk.sh 疑高顿遗留见 ISSUE-015
- ✅ **T-10 B方案（Pinia action 驱动）端到端验证成功**：注入脚本直接调 `profile.fetchMoreData({username})` 翻短视频到 `noMore`、切"直播回放"tab 后 `liveCardObjects` 首屏即全量，**不滚 DOM**。交易的游戏实测 cardObjects 340（339视频 mediaType=4 + 1图文 mediaType=2）、liveCardObjects 28，oid/nid 双唯一零重复，纯视频339与旧滚动manifest精确一致（回放多1为新增）。代码 `replay_list_hook.go:actionDrive()`，结论落 api.md §6.2 / capture SOP §2.1。待办：把 action 全量接入下游下载管道（decode_key 沿用 -short-probe）、按339权威值重对账落库410口径
- ✅ **T-10 视频号API深挖完成**：列表不走HTTP，走XWEB原生桥(postMessage)+Vue Pinia状态树；凭证在主页URL(username+exportkey+pass_ticket)；结论落 docs/research/wechat-channels-api.md §6
- ✅ **视频号增量脚本** `platforms/wechat_channels/video-downloader/incremental_sync.py`：按 encfilekey(=捕获id) 对账，dry-run验证通过，只下新增差集，待实跑
- ✅ **凭证最短路径+人机协作边界**：视频号=人工点进主页即拿凭证；公众号=人工激活文章链接拿appmsg_token；"人工触发一次拿token+脚本全自动"原则落 docs/guides/wechat-channels-capture.md §6/§7
- 📄 **公众号文章HTTP API方案**：getmsg翻页参数已调研（__biz/offset/count/appmsg_token/pass_ticket），任务文档 project-management/active/wechat-article-full-export-task.md（公号三刀v1.1.0路径），待实测

- ✅ FunASR 批量转写全量完成：短视频 410 + 直播回放 25 = 435 份转写稿，0 失败，仅 1 个纯配乐空稿（short_411，有音轨无人声）。产物 `library/04_transcript/stock/交易的游戏/{short,live}/<标题>/transcript.md`
- ✅ 环境搭建：共享 venv `~/.venvs/funasr`（funasr1.4.3/torch2.2.2/torchaudio2.2.2，Intel x86_64；llvmlite 用 `--only-binary` 预编译解决源码编译坑）
- ✅ 新增 SOP `docs/guides/audio-transcription.md` + 批量脚本 `platforms/wechat_channels/video-transcribe/batch_transcribe.py`，已入库

- ✅ 视频号短视频解密闭环端到端验证：Isaac64 算法确认（非AES、仅前128KB加密）；仓内自包含 `decrypt_node.js` 与官方 wasm 密钥流逐字节一致；完整样本解密后 h264 1080x1920+aac、时长134.86s 与记录吻合
- ✅ 下载编排 `batch_download_v4.py` 修复（解密器同目录路径、可选代理 WC_PROXY、WC_LIMIT、md5 对账、规格差异标注）
- ✅ 捕获代理 `-short-probe` 静默探针落库换签直链+decode_key（`platforms/wechat_channels/video-capture/` 下 captor.go/main.go/short_probe_hook.go，go vet/build 通过）
- ✅ 安全：含签名票据的捕获产物加入 video-capture/.gitignore，旧 capture_*.json 停止跟踪；其历史痕迹已于 2026-09-22 随 ISSUE-014 一并 filter-repo 清除
- 📄 新增权威技术文档 docs/research/wechat-short-video-decryption.md，采集SOP同步更新

---

## 最近完成（2026-09-18）

- ✅ SOP瘦身：三个微信SOP从1107行减到424行（-62%）
- ✅ AGENTS/WORKFLOW通路去重：工具索引精简，常见问题去重，章节引用修正
- ✅ REVIEW-governance-summary瘦身：577→~120行（-79%）
- ✅ DESIGN-knowledge-base-organization瘦身：443→~130行（-71%）

---

*最后更新：2026-10-12（全仓评审治理同步：T-31/T-37/T-38/T-39 10月完成条目补登；T-39 mp_verify 遗留 ERROR 核实未跟踪、自动消解关闭；新增评审与治理维护行）*
