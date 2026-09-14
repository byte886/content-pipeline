# 视频号内容采集SOP

> **文档类型**：SOP（标准操作流程）
> **更新时间**：2026-09-15
> **维护者**：AI自动维护 + 用户审核
> **适用范围**：微信视频号「交易的游戏」内容自动化采集

---

## 1. 概述

本文档描述微信视频号内容的自动化采集流程，包括视频URL捕获、下载、解密和存档。

**目标账号**：
- 视频号名称：交易的游戏
- 认证：证券投资顾问（刘广义，执业编号A0630624060004）
- 关联公众号：顶底之王

---

## 2. 核心技术突破

### 2.1 微信代理问题（关键）

**问题**：微信完全不走系统代理，传统的只设置Wi-Fi代理的方式无效。

**根本原因**：微信使用Ethernet接口（IP 192.168.2.9），而不是Wi-Fi。

**解决方案**：必须对**所有活动网络服务**设置代理，而不仅仅是Wi-Fi。

```bash
# 获取所有活动网络服务
networksetup -listallnetworkservices

# 对每个活动服务设置HTTP和HTTPS代理
networksetup -setwebproxy "Ethernet" 127.0.0.1 8899
networksetup -setsecurewebproxy "Ethernet" 127.0.0.1 8899
networksetup -setwebproxy "Wi-Fi" 127.0.0.1 8899
networksetup -setsecurewebproxy "Wi-Fi" 127.0.0.1 8899
```

**参考**：RES Downloader源码 `core/system_darwin.go` 的 `setProxy()` 函数。

### 2.2 视频解密机制（关键）

**问题**：微信视频号的短视频是加密的，直接下载后无法播放。

**解密原理**：
1. 每个视频有一个 `DecodeKey`（9-10位数字字符串，如 `950135168`）
2. 用 `DecodeKey` 作为种子，通过 **ISAAC64** 伪随机数生成器生成 128KB 字节数组
3. 将这个字节数组与文件前 128KB 进行 XOR 解密
4. 解密后的文件是标准 MP4 格式

**实现方式**：
- 使用 Node.js 运行 RES Downloader 自带的 `decrypt.js`（Emscripten 编译的 WASM）
- 关键函数：`Module.WxIsaac64(seed).generate(131072)` 生成 128KB 数组
- 解密脚本：`tools/video-downloader/wechat_decrypt.js`

**直播回放**：不需要解密（无 DecodeKey），可直接下载播放。

### 2.3 视频质量说明

- **原始URL**：返回低分辨率版本（通常2-5MB，720x1280）
- **高质量URL**：只保留 `encfilekey` + `token` 参数，但当前测试不工作
- **当前策略**：使用原始URL下载低分辨率版本，解密后可用

---

## 3. 工具说明

### 3.1 视频捕获工具

**位置**：`tools/video-capture/`

**功能**：
- 启动时自动设置系统代理（对所有活动网络服务）
- 退出时自动清除系统代理
- 通过 MITM 代理注入 JS Hook，捕获视频号视频 URL
- 支持自动下载（可选）
- 支持上游代理（如 ClashX），实现国内直连/国外自动VPN

**使用方法**：
```bash
# 基础用法（直连，国内视频号足够）
./video-capture -port 8899 -output videos.json

# 带上游代理（推荐，国内直连/国外自动VPN）
./video-capture -port 8899 -output videos.json -upstream http://127.0.0.1:7890

# 不自动设置系统代理（需手动配置）
./video-capture -port 8899 -output videos.json -no-auto-proxy
```

**上游代理说明**：
- `-upstream` 参数指定上游代理地址（通常是 ClashX 的 `http://127.0.0.1:7890`）
- 设置后，所有上游请求走 ClashX，由 ClashX 根据规则自动选择直连或 VPN
- 国内域名（finder.video.qq.com、mp.weixin.qq.com 等）自动直连
- 国外域名自动走 VPN 节点
- 不影响 iTerm 的 Shell 环境变量和 TUN 模式

**代理影响范围**：
| 程序 | 是否受影响 | 原因 |
|------|-----------|------|
| Chrome（无代理扩展） | ✅ 受影响 | 读系统代理 |
| Chrome（SwitchyOmega） | ❌ 不受影响 | 扩展覆盖系统代理 |
| iTerm 命令行工具 | ❌ 不受影响 | 读 Shell 环境变量，不读系统代理 |
| TUN 模式下的程序 | ❌ 基本不受影响 | TUN 在网络层接管，绕过本地回环 |
| 微信 | ✅ 受影响（正是需要的） | 读系统代理 |

> **注意**：仅捕获 URL 阶段需要代理（几分钟），下载阶段完全不走代理。捕获工具退出时自动清除系统代理。

**使用方法**：
```bash
cd tools/video-capture
./video-capture -port 8899 -output videos.json
# 按 Ctrl+C 停止，会自动清除代理
```

**关键文件**：
- `main.go` - 入口，代理设置/清除
- `captor.go` - 核心捕获逻辑（代理+JS注入+URL保存）
- `proxy_darwin.go` - macOS 系统代理设置/清除
- `ca.crt` / `ca.key` - 自签名 CA 证书（已信任，持久加载）

### 3.2 视频下载工具

**位置**：`tools/video-downloader/`

**功能**：
- 批量下载视频
- 自动解密（调用 Node.js 解密脚本）
- 验证 MP4 有效性
- 去重（跳过已下载的有效文件）

**使用方法**：
```bash
python3 tools/video-downloader/batch_download_v4.py <视频列表.json> <输出目录> <类型:live/short> [起始序号]
```

**关键文件**：
- `batch_download_v4.py` - 批量下载脚本
- `wechat_decrypt.js` - 视频解密脚本（Node.js）
- `decrypt_node.js` - RES Downloader 的 decrypt.js（去掉 export）

---

## 4. 采集流程

### 4.1 捕获视频URL

1. 启动捕获工具（推荐带上游代理）：
   ```bash
   ./video-capture -port 8899 -output videos.json -upstream http://127.0.0.1:7890
   ```
2. 在微信中搜索「交易的游戏」，进入视频号主页
3. 切换到「视频」标签，滚动列表到底部
4. 切换到「直播回放」标签，滚动列表到底部
5. 按 Ctrl+C 停止捕获，工具自动清除系统代理

### 4.2 导出和去重

1. 从捕获工具输出的 `videos.json` 中提取视频
2. 按 `encfilekey` 去重
3. 按大小分类：<100MB 为短视频，>=100MB 为直播回放
4. 过滤掉没有标题的视频

### 4.3 下载和解密

1. 短视频：使用 `batch_download_v4.py` 下载，自动解密
2. 直播回放：使用 `batch_download_v4.py` 下载，无需解密
3. 验证：检查文件头是否为 `ftyp`（有效 MP4）

### 4.4 存档

1. U盘存档：`/Volumes/Ubuntu-Serv/主播视频/交易的游戏/`
   - `短视频/` - 短视频 MP4
   - `直播回放/` - 直播回放 MP4
   - `短视频清单.csv` - 短视频清单
   - `直播回放清单.csv` - 直播回放清单
2. 命名格式：`序号_标题.mp4`

---

## 5. 数据统计（截至2026-09-15）

| 类型 | 数量 | 说明 |
|------|------|------|
| 短视频 | 314个（有效标题） | 需解密，低分辨率版本 |
| 直播回放 | 23个（无DecodeKey） | 无需解密 |
| 公众号文章 | 277篇 | 已采集完成 |

---

## 6. 常见问题

### Q1: 微信不走代理怎么办？
A: 确保对所有活动网络服务设置代理，不仅仅是Wi-Fi。使用 `networksetup -listallnetworkservices` 查看所有服务。

### Q2: 下载的视频无法播放怎么办？
A: 短视频需要解密。使用 `node tools/video-downloader/wechat_decrypt.js <DecodeKey> <文件路径>` 解密。

### Q3: 如何获取 DecodeKey？
A: DecodeKey 在捕获的视频数据中，字段名为 `decode_key`（9-10位数字）。

### Q4: 直播回放需要解密吗？
A: 不需要。直播回放没有 DecodeKey，下载后可直接播放。

### Q5: 下载的视频很小（2-5MB）是怎么回事？
A: 原始URL返回的是低分辨率版本。高质量URL（只保留encfilekey+token）当前测试不工作，待进一步研究。

### Q6: 设置全局代理会不会影响其他程序？
A: 影响有限。仅捕获URL阶段（几分钟）设置全局代理，下载阶段完全不走代理。iTerm命令行工具（读Shell环境变量）和TUN模式下的程序不受影响，只有Chrome等读系统代理的GUI程序会受影响。工具退出时自动清除代理。如需完全隔离，可使用`-upstream`参数走ClashX规则路由。

### Q7: 上游代理和ClashX是什么关系？
A: `-upstream http://127.0.0.1:7890` 把ClashX作为上游代理。我们的MITM代理负责解密HTTPS和注入JS，ClashX负责根据规则选择直连或VPN。国内域名（视频号、公众号）自动直连，国外域名自动走VPN。

---

## 7. 待优化项

- [ ] 研究高质量URL的正确构建方式
- [ ] 优化解密速度（预生成解密数组缓存）
- [ ] 实现增量采集（只采集新视频）
- [ ] 自动转文字（使用 whisper 或 FunASR）
- [ ] 自动生成字幕

---

*本文档随技术演进而更新。发现新问题或解决方案时，按"问题驱动更新"原则立即补充。*
