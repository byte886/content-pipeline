# ISSUE-016：交易的游戏 文件盘去重、缺口补下与 inventory 台账重建

> 创建：2026-09-22　状态：✅ 已完成（2026-09-22：去重删 71 组释放 319.5MB、补 3 场回放并转写、inventory 重建，audit short 339/live 28 全 0）　归属：视频号方案 A 收尾
> 权威数据来源：`library/00_manifest/catalog_交易的游戏.json`（平台全集）+ `library/00_manifest/audit_交易的游戏.json`（文件盘严格对账）
> 对账方法：ffprobe 实际时长（短视频 ±2s / 回放 ±3s）+ 归一化标题 + hashtag 消歧。**不用 mp4 文件 MD5 与高清 md5sum 对账（跨清晰度命中率近 0，不可行）。**

## 1. 现状（2026-09-22 严格对账结论）

| 类别 | 平台全集 | 磁盘文件 | 已覆盖 | 缺口 | 重复文件 | 游离 | 歧义 |
|---|---|---|---|---|---|---|---|
| 短视频 short | 339 | 410 | **339（全）** | **0** | **71 组各 2 个 = 71 个多余** | 0 | 0 |
| 直播回放 live | 28 | 25 | 25 | **3** | 0 | 0 | 0 |

- 短视频内容**零缺口**；410 个文件里有 71 个是同一视频的重复下载（每组一个早期小编号 seq≈1–260 + 一个后来补下的大编号 seq≈329–410，部分为清晰度差异）。去重后保留 339 个，可释放约 **300 MB**。
- 多匹配消歧已确认：`short_055`（60s，标签 财经/行情/股票/股民）= `c8cdabfbd4db5b7f`；`short_311`（61s，标签 上证指数，15.1MB）= `f1e44db873b531b7`，是两条不同视频、均有文件。
- 旧台账 `交易的游戏_inventory.json` 质量差：shorts 410 条中 150 条 encfilekey/duration 为 null；lives 25 条 encfilekey 去重仅 14 个唯一 id（5 组同名不同场次被错标同一 id，实际时长各不相同、是 25 个不同场次）。**不可继续作为水位真相，需重建。**

## 2. 缺的 3 场直播回放（id 已在 catalog.replays）

| id | 时长(s) | 标题 |
|---|---|---|
| `1fb195bc2a6b5838` | 2266 | 上涨中继 |
| `6ea0215f7f0297e2` | 2415 | 再次缩量见底 |
| `bdfd5f9fb4fccd6d` | 2018 | 再次缩量见底 |

回放是明文 MP4（无 decodeKey），但下载 URL 仍带临时 token，必须先用新 hook 刷新主页换签（见 ISSUE-017 / 方案 A 收尾），拿到这 3 场的有效直链后用 `batch_download_v4.py ... live` 补下，再跑转写。

## 3. 去重方案（短视频，删除前需用户确认）

数据来源 `audit_交易的游戏.json -> short.duplicate_groups[]`，每组含 `keep`（建议保留）与 `drop[]`（建议删除）。

1. **保留规则（知识型默认 min）**：每组保留**可正常解密播放、且有对应转写稿**的较小文件（audit 默认 `keep = size_mb 最小`）。执行前对 keep 文件批量跑一次解密+ffprobe 校验，确认能解出可播放 h264/aac；若较小文件损坏，则改保留同组较大文件。
2. **删除 drop 的 71 个视频文件**（高风险，出最终清单给用户确认后才执行）。
3. **转写目录同步去重**：`library/04_transcript/stock/交易的游戏/short/` 现有 410 个子目录。对每组：
   - 比对 keep/drop 两份 `transcript.md`（字数差 <10% 视为同稿）：一致则删除 drop 同名转写目录；不一致则**保留并标记**，人工看一眼。
   - 去重后 short 视频与转写目录都应为 339，一一对应。
4. live 转写现有 26 个子目录（比 25 视频多 1），重建时定位多出的目录：空目录/早期测试目录则删除，否则保留标记。

## 4. inventory 台账重建（去重 + 补回放之后一次性做）

以 catalog 的 16hex id 为主键，用 audit 的"文件→id"严格映射回填，生成新的 `library/00_manifest/交易的游戏_inventory.json`：

- 顶层：account / platform / domain / catalog_generated_at / inventory_generated_at / summary / shorts[] / lives[]。
- 每条：`id`（catalog 16hex）、`oid`、`seq`、`file`、`title`、`duration_s`（ffprobe 实测）、`disk_size_mb`、`md5sum`（catalog）、`has_transcript`、`transcript_path`。
- 校验门：shorts 条数 = 339、lives 条数 = 28（补下后）；每个 id 在 catalog 中存在；每个文件可 ffprobe；转写目录一一对应。重建后 `audit_disk.py` 应跑出 short/live 均 缺 0、重复 0、游离 0、歧义 0。

## 5. 执行顺序（检查点）

1. 【需用户 GUI 一次】新 hook 刷新「交易的游戏」主页 → 验证换签覆盖率、抓 RLIST_ACTSRC（ISSUE-017）。
2. 补下 3 场缺回放 + 转写。
3. 【需用户确认】输出 71 组 keep/drop 最终清单（含可播放校验结果）→ 确认后删视频 + 同步去重转写。
4. 重建 inventory，跑 audit_disk.py 至全 0，commit。
5. 全部本地处理完后再统一同步百度网盘（在此之前不同步，避免镜像错误结构）。

## 6. 复用工具

- 对账：`platforms/wechat_channels/video-downloader/audit_disk.py`（时长缓存 `<video-root>/.duration_cache.json`，重复运行秒级）。
- 解析全量基准：`platforms/wechat_channels/video-capture/parse_capture_log.py`。
- 下载：`batch_download_v4.py`；增量：`incremental_sync.py`（已修 live→lives 键）。
