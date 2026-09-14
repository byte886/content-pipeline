# A股投资知识库

> **项目类型**：知识库建设 + 自动化采集
> **创建时间**：2026-09-11
> **维护者**：AI自动维护 + 用户审核

## 项目目标

构建A股投资知识库，自动化采集公众号「顶底之王」和关联视频号「交易的游戏」的全部内容，为后续量化系统和内容生成提供数据基础。

## 目标账号

| 平台 | 名称 | 认证 | 说明 |
|------|------|------|------|
| 公众号 | 顶底之王 | - | 图文文章 |
| 视频号 | 交易的游戏 | 证券投资顾问（刘广义，执业编号A0630624060004） | 短视频 + 直播回放 |

## 项目结构

```
stock-knowledge-base/
├── README.md                    # 项目说明
├── docs/                        # 文档
│   ├── 视频号内容采集SOP.md     # 视频号采集SOP
│   ├── 公众号文章采集SOP.md     # 公众号采集SOP
│   └── ...
├── tools/                       # 工具
│   ├── video-capture/           # 视频捕获工具（Go语言）
│   │   ├── main.go              # 入口（自动设置/清除代理）
│   │   ├── captor.go            # 核心捕获逻辑
│   │   ├── proxy_darwin.go      # macOS代理设置
│   │   ├── video-capture        # 编译后可执行文件
│   │   └── ca.crt/ca.key        # CA证书
│   └── video-downloader/        # 视频下载工具
│       ├── batch_download_v4.py # 批量下载脚本
│       ├── wechat_decrypt.js    # 视频解密脚本
│       └── decrypt_node.js      # RES Downloader解密库
├── knowledge-base/              # 知识库
│   ├── 01-视频号内容/           # 视频转文字稿
│   ├── 02-公众号文章/           # 公众号文章正文
│   └── 03-股票知识/             # 股票知识库
└── data/                        # 数据（gitignore）
    ├── videos/                  # 下载的视频
    └── articles/                # 下载的文章
```

## 核心技术

### 视频采集
- **代理捕获**：MITM代理 + JS注入Hook，捕获视频号视频URL
- **自动代理**：启动时自动设置系统代理（所有活动网络服务），退出时自动清除
- **视频解密**：ISAAC64伪随机数生成器 + XOR解密（前128KB）
- **批量下载**：支持短视频（需解密）和直播回放（无需解密）

### 文章采集
- 微信本地数据库读取
- 公众号文章正文提取

## 数据统计（截至2026-09-15）

| 类型 | 数量 | 状态 |
|------|------|------|
| 短视频 | 314个 | 下载中 |
| 直播回放 | 23个 | 下载中 |
| 公众号文章 | 277篇 | 已完成 |

## 快速开始

### 捕获视频URL
```bash
cd tools/video-capture
./video-capture -port 8899 -output videos.json
# 在微信中打开视频号，滚动列表
# Ctrl+C 停止（自动清除代理）
```

### 下载视频
```bash
# 短视频（自动解密）
python3 tools/video-downloader/batch_download_v4.py videos.json output/ short 1

# 直播回放
python3 tools/video-downloader/batch_download_v4.py live.json output/ live 1
```

## 存储分工

| 位置 | 内容 | 说明 |
|------|------|------|
| GitHub仓库 | 代码+文档 | 禁止放视频等大文件 |
| 本地 data/ | 视频、文章 | 主存储 |
| U盘 | 视频存档 | 备份 |
| 百度网盘 | 与本地镜像 | 跨设备访问 |

## 后续计划

- [ ] 视频转文字（whisper / FunASR）
- [ ] 图文OCR解析
- [ ] 知识库生成与组织
- [ ] 增量采集（跟踪新内容）
- [ ] 量化系统对接
- [ ] 公众号/视频号文案生成

## 相关文档

- [视频号内容采集SOP](docs/视频号内容采集SOP.md)
- [公众号文章采集SOP](docs/公众号文章采集SOP.md)
