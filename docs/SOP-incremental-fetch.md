# SOP：增量采集（多平台内容更新发现与下载）

> **文档类型**：SOP（标准操作流程）
> **适用场景**：定期检查已关注博主是否有新内容，自动发现并下载新增视频/文章
> **核心工具**：`scripts/incremental/fetch_new.py`

---

## 1. 设计原理

### 1.1 通用框架

增量采采用**平台无关的通用框架**，各平台只实现两个方法：

| 方法 | 职责 | 平台差异 |
|------|------|----------|
| `fetch_latest_list()` | 获取博主最新内容列表 | 各平台不同（API/网络捕获/爬虫） |
| `get_unique_key()` | 提取唯一标识符 | B站=bvid，视频号=标题+大小，公众号=URL |

对比、下载、更新manifest是**通用逻辑**，不随平台变化。

### 1.2 唯一标识符

| 平台 | 唯一键 | 说明 |
|------|--------|------|
| B站 | `bvid` | 视频唯一ID，精确去重 |
| 视频号 | `标题+大小(MB)` | 历史数据无唯一ID，用组合键（可能有重复标题） |
| 公众号 | `文章URL` | 含__biz和mid，唯一 |
| 抖音 | `aweme_id` | （反爬，暂不可用） |
| YouTube | `video_id` | 视频唯一ID |

### 1.3 增量流程

```
获取博主最新列表 → 与manifest对比 → 找出新增项 → 下载 → 追加到manifest → 同步网盘
```

---

## 2. 使用方法

### 2.1 单个博主增量检查

```bash
# B站（dry-run，只对比不下载）
python3 scripts/incremental/fetch_new.py --platform bilibili --account 宝石学家老许 --dry-run

# B站（实际下载新增）
python3 scripts/incremental/fetch_new.py --platform bilibili --account 宝石学家老许

# 视频号（需先捕获列表）
python3 scripts/incremental/fetch_new.py --platform wechat_channels --account 交易的游戏 \
  --list-file /tmp/wechat_channels_list.json
```

### 2.2 所有启用的源批量检查

```bash
# 所有源dry-run
python3 scripts/incremental/fetch_new.py --all --dry-run

# 所有源实际下载
python3 scripts/incremental/fetch_new.py --all
```

### 2.3 视频号增量的特殊步骤

视频号没有公开API，需要先通过网络捕获获取列表：

1. 用res-downloader捕获视频号列表页请求
2. 保存为JSON文件（格式：列表，每项含title/size_mb）
3. 运行增量脚本指定 `--list-file`

```bash
# 步骤1：捕获列表（参考 SOP-wechat-channels-capture.md）
# 步骤2：保存为 /tmp/wechat_list.json
# 步骤3：增量检查
python3 scripts/incremental/fetch_new.py --platform wechat_channels --account 交易的游戏 \
  --list-file /tmp/wechat_list.json --dry-run
```

---

## 3. 配置

采集源配置在 `config/sources.json`：

```json
{
  "sources": [
    {
      "platform": "bilibili",
      "account": "宝石学家老许",
      "uid": "1841256325",
      "domain": "jewelry",
      "enabled": true
    },
    {
      "platform": "wechat_channels",
      "account": "交易的游戏",
      "domain": "stock",
      "enabled": true
    }
  ]
}
```

新增博主时，在此文件添加配置即可，增量脚本自动识别。

---

## 4. Manifest结构

每个博主目录下有一个 `manifest.json`，是已采集内容的权威清单：

```
library/01_video/jewelry/宝石学家老许/manifest.json
library/01_video/stock/交易的游戏/manifest.json
```

增量采集时：
- 读取manifest获取已有内容
- 对比最新列表发现新增
- 下载后追加到manifest
- 编号自动续接（如已有743个，新的从744开始）

---

## 5. 定期运行建议

### 5.1 手动运行

需要检查更新时手动运行：
```bash
python3 scripts/incremental/fetch_new.py --all --dry-run  # 先看有多少新增
python3 scripts/incremental/fetch_new.py --all            # 确认后下载
```

### 5.2 定时任务（可选）

如需自动定期检查，可配置cron：
```bash
# 每天早上9点检查一次（dry-run，不自动下载）
0 9 * * * cd /path/to/project && python3 scripts/incremental/fetch_new.py --all --dry-run >> logs/incremental.log 2>&1
```

> 注意：视频号增量需要手动捕获列表，不适合完全自动化。

---

## 6. 平台实现状态

| 平台 | 列表获取 | 唯一键 | 自动下载 | 状态 |
|------|----------|--------|----------|------|
| B站 | bili_list.py (wbi签名) | bvid | yt-dlp | ✅ 框架就绪，需调环境 |
| 视频号 | 网络捕获JSON | 标题+大小 | 需手动捕获 | ⚠️ 需手动捕获列表 |
| 公众号 | 网络捕获 | URL | 需手动捕获 | ⚠️ 待实现 |
| 抖音 | （反爬403） | aweme_id | - | ❌ 暂不可用 |
| YouTube | yt-dlp | video_id | yt-dlp | 🔲 待接入 |

---

## 7. 新增平台接入步骤

1. 在 `scripts/incremental/fetch_new.py` 中继承 `IncrementalFetcher`
2. 实现 `fetch_latest_list()` 和 `get_unique_key()`
3. 实现 `download_item()`（或复用通用下载逻辑）
4. 在 `FETCHER_REGISTRY` 中注册
5. 在 `config/sources.json` 中添加该平台的源

---

## 8. 注意事项

- **dry-run优先**：首次运行或不确定时先用 `--dry-run` 查看新增数量
- **视频号去重**：用标题+大小组合键，可能有重复标题（如同主题多次直播），大小可区分
- **manifest是权威**：不要手动修改manifest，通过脚本更新
- **增量后同步网盘**：下载新增后运行网盘同步脚本
- **B站API限制**：需要wbi签名，直接调用可能412，需复用bili_list.py的签名逻辑
