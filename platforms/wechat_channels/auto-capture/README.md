# 自动化采集工具

> ⚠️ **已废弃（DEPRECATED），请勿使用本目录脚本。**
>
> - `auto_capture.py` 用 osascript 自动操控微信窗口（搜索/点击/切 tab/滚动）。
>   微信是腾讯桌面客户端，其界面**不允许 AI 自动化**，这条路在边界上不可用。
> - `incremental_collect.py` 自维护 manifest 的增量逻辑，已被
>   `video-downloader/incremental_sync.py`（按 inventory 的 16hex `id` 对账）取代。
>
> **现行正路**：`platforms/wechat_channels/collect_channels.py`
> （captor 注入 Pinia action **自动翻页枚举**，人工只需搜索账号→点「视频号」行
> 进入主页，无需滚动/播放；之后增量下载、转写、台账、对账全自动）。
> 操作 SOP 见 `docs/guides/wechat-channels-collect-sop.md`。
>
> 以下内容仅作演进历史保留。

---

一键采集微信视频号的所有视频和直播回放，无需人工滚动页面。

## 功能

- 自动搜索视频号并进入主页
- 自动滚动"视频"标签到底部
- 自动切换到"直播回放"标签并滚动到底部
- 自动捕获视频URL（含解密密钥）
- 自动下载并解密视频
- 自动清除系统代理

## 用法

```bash
# 完整采集（捕获+下载）
python3 platforms/wechat_channels/auto-capture/auto_capture.py "交易的游戏"

# 只捕获不下载
python3 platforms/wechat_channels/auto-capture/auto_capture.py "交易的游戏" --no-download

# 指定参数
python3 platforms/wechat_channels/auto-capture/auto_capture.py "交易的游戏" \
    --port 8899 \
    --output videos.json \
    --download-dir ./downloads \
    --scroll-timeout 60
```

## 前置条件

1. 微信已登录并运行
2. CA证书已信任（video-capture工具的ca.crt）
3. ClashX可选（默认使用7890端口作为上游代理，不可用时自动降级直连）

## 工作流程

```
启动捕获工具(设置系统代理)
    ↓
激活微信 → Cmd+F搜索视频号 → 回车进入主页
    ↓
滚动"视频"标签到底部（检测无新内容则停止）
    ↓
点击"直播回放"标签 → 滚动到底部
    ↓
停止捕获工具(清除系统代理)
    ↓
分类视频/直播回放 → 批量下载+解密
```

## 已知限制

1. **标签切换坐标**：视频/直播回放标签的点击坐标是估算的，不同窗口大小可能需要调整
2. **搜索结果**：假设搜索后第一个结果就是目标视频号，如有多个同名账号可能点错
3. **滚动检测**：通过捕获数量判断是否到底部，网络延迟时可能提前停止
4. **微信版本**：基于微信4.1.8测试，其他版本界面可能不同

## 故障排查

- **微信不走代理**：确保对所有活动网络服务设置了代理（工具自动处理）
- **捕获不到视频**：检查CA证书是否信任，检查JS注入是否生效
- **滚动无效**：确保鼠标在视频列表区域上方，检查窗口是否被遮挡
