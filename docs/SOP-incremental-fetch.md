# SOP：增量采集（多平台内容更新发现）

> **适用场景**：定期检查已关注博主是否有新内容，自动发现并下载
> **核心工具**：`scripts/incremental/fetch_new.py`

---

## 1. 使用方法

```bash
# B站（dry-run，只对比不下载）
python3 scripts/incremental/fetch_new.py --platform bilibili --account 宝石学家老许 --dry-run

# 所有启用的源批量检查
python3 scripts/incremental/fetch_new.py --all --dry-run

# 确认后实际下载
python3 scripts/incremental/fetch_new.py --all
```

**视频号特殊步骤**：需先通过网络捕获获取列表JSON，再指定 `--list-file` 参数。

---

## 2. 配置

采集源配置在 `config/sources.json`，新增博主时在此文件添加即可：

```json
{
  "sources": [
    {
      "platform": "bilibili",
      "account": "宝石学家老许",
      "domain": "jewelry",
      "enabled": true
    }
  ]
}
```

---

## 3. 平台实现状态

| 平台 | 列表获取 | 唯一键 | 自动下载 | 状态 |
|------|----------|--------|----------|------|
| B站 | 内联wbi签名 | bvid | yt-dlp | ⚠️ API临时412（需已登录cookie） |
| YouTube | yt-dlp flat-playlist | video_id | media_downloader.py | ✅ 已验证 |
| 视频号 | 网络捕获JSON | 标题+大小 | 需手动捕获 | ⚠️ 需手动捕获列表 |
| 抖音 | 手动提供列表 | aweme_id | media_downloader.py | ❌ 403反爬 |
| 公众号 | 网络捕获JSON | URL | fetcher.py | ⚠️ 框架就绪，需微信登录态 |

---

## 4. Manifest机制

每个博主目录下有一个 `manifest.json`，是已采集内容的权威清单：
- 增量采集时读取manifest对比最新列表
- 下载后追加到manifest，编号自动续接
- 不要手动修改manifest，通过脚本更新

---

## 5. 注意事项

- **dry-run优先**：首次运行或不确定时先用 `--dry-run` 查看新增数量
- **视频号去重**：用标题+大小组合键区分同主题多次直播
- **增量后同步网盘**：下载新增后运行网盘同步脚本
- **B站API限制**：需要wbi签名，直接调用可能412，需复用bili_list.py的签名逻辑

---

*最后更新：2026-09-17*
