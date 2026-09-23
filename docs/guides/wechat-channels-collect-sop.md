# 视频号一键采集 SOP（人工一步）

> **文档类型**：场景 SOP（最短路径）
> 方案：A — captor 中间人 + 注入 Pinia action **自动翻页枚举全量**，零播放、零手动滚动。
> 平台：仅 macOS。详细原理见 [wechat-channels-capture.md](wechat-channels-capture.md) 与
> [../research/wechat-channels-api.md](../research/wechat-channels-api.md)。

---

## 1. 一条命令

```bash
cd ~/Desktop/multiplatform-content-pipeline
python3 platforms/wechat_channels/collect_channels.py "交易的游戏" --domain stock --quality min
```

- `--domain`：行业目录（stock / jewelry / …），决定落到 `library/01_video/<行业>/<账号>/`。
- `--quality`：`min`（默认，知识型转文字够用，短视频约 5–15MB）/ `default` / `max`。
- `--upstream auto`（默认）：启动前自动跑网络预检——探测到**能翻墙**的本地代理
  （如 ClashX 7890）就把它作上游（仅外网域名走它），否则直连；微信/腾讯域名始终直连。
  一般无需手动指定；强制直连传 `--upstream ""`。
- `--no-download`：只捕获+重组+落 catalog，先不下载/转写。
- `--build`：启动前重新 `go build` captor（改过注入 JS 后用）。

## 2. 人工只做一步（约 15 秒，脚本会在终端打印同样提示）

命令运行后，在**微信客户端**里：

1. `Cmd+F` 搜索账号名（如「交易的游戏」）；
2. 在搜一搜结果里点中带 **「视频号」** 灰色标签的那一行进入主页（**别点成公众号**）；
3. 如果之前已经开着该主页，**先彻底关掉那个窗口再重新进入**——必须让主页 HTML 重新请求，注入才会生效；
4. 不用滚动、不用点视频、不用播放，静候即可。注入脚本会自动翻完「视频」再翻「直播回放」。

> 微信是腾讯桌面客户端，其界面不允许 AI 自动化：搜索 / 开窗 / 关窗这一步只能人工；
> 此后枚举、换签、下载、解密、转写、去重、台账、对账全部自动。

看到终端打印 `all-done：短视频 N，直播回放 M` 即捕获完成，脚本会自动停 captor
（系统代理随之自动清回）并接管后续全程。

## 3. 脚本自动完成的时序

```
启动 captor（自动设系统代理 :8899）
  → 等待人工开窗（轮询日志，默认超时 360s，--capture-timeout 可调）
  → 命中 all-done
  → SIGTERM 停 captor（自动清代理，兜底复核）
  → parse_capture_log：脱敏 catalog + 含票据 signed manifest
  → catalog 落库（旧版自动备份到 workspace/capture/）
  → incremental_sync 按 16hex id 对账：首次=全量，之后=只下新增
  → batch_download_v4 下载 + Isaac64 解密（图文 mediaType=2 自动过滤）
  → FunASR 转写（已转写自动跳过）
  → rebuild_inventory 重建台账（严格校验门）
  → audit_disk 文件盘对账（缺/重复/游离/歧义应为 0）
```

## 4. 产物位置

| 内容 | 路径 | 是否入 git |
|---|---|---|
| 脱敏全量基准 | `library/00_manifest/catalog_<账号>.json` | ✅ 入库 |
| 本地台账（时长/转写状态） | `library/00_manifest/<账号>_inventory.json` | ✅ 入库 |
| 文件盘对账报告 | `library/00_manifest/audit_<账号>.json` | ✅ 入库（应全 0） |
| 视频原片 | `library/01_video/<行业>/<账号>/{short,live}/short_NNN_*.mp4` | ❌ gitignore |
| 转写稿 | `library/04_transcript/<行业>/<账号>/{short,live}/<名>/transcript.md` | ❌ gitignore |
| 捕获日志 / 含票据 signed | `workspace/capture/`、`workspace/signed/` | ❌ gitignore，确认后可删 |

> signed manifest 含带 token 的签名直链，**绝不能入库**；票据几小时过期，
> 过期后下次采集重新开窗即可。

## 5. 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| 一直等不到 all-done | 多半是旧窗口没重进导致 HTML 未重新请求、注不进；彻底关掉视频号窗口重新搜索进入。也可能点成了公众号。 |
| 只有 15 条、驱动不启动 | 注入 JS 没生效或二进制过旧；`--build` 重编译，确认命令带 `-replay-list -short-probe`。 |
| 标签数/回放为 0 | 部分账号没有直播回放（巫师财经类），属正常；tab 可能是 0/1/2/N 个，驱动自动兼容。 |
| 票据失效 / 下载 403 | signed 直链几小时过期，重新跑一次采集开窗换签即可。 |
| 跑完上不了网 | captor 正常退出会自动快照恢复代理；异常中断按 `AGENTS.md` §2.1「紧急恢复」处理，或系统设置里关掉网页代理。 |
| ClashX 要不要开 | 可保持开启：预检自动识别，仅让外网走它、微信直连，采集期间外网不断。**不要手动改系统代理**，也不要在采集时切换 ClashX 开关；历史断网多因手动抢改代理。 |

## 6. 跟踪更新（增量）

以后该账号发了新视频，**重跑同一条命令、再开一次窗**即可：
`incremental_sync` 按稳定 `id`（`md5(md5sum)[:16]`）对账，只下载新增条目，
已有的视频和转写自动跳过，台账与对账自动重建。暂不挂定时任务，需要时手动跑。
