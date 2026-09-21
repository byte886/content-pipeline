# 视频/音频转文字 SOP（FunASR 本地离线）

> **文档类型**：Guide（操作指南）
> **适用**：所有平台（视频号/B站/抖音/YouTube…）的视频或音频转文字，跨平台公共能力，不绑定单一来源
> **更新频率**：环境或脚本用法变化时

---

## 1. 选型与原则

- **引擎**：FunASR `SenseVoiceSmall` + `fsmn-vad`，本地离线、CPU 即可、中文财经语义准。
- **不使用** faster-whisper（Intel CPU 过慢，已弃用）；不依赖云端转写。
- 转写参数固定（不要改）：`use_itn=True`、VAD 单段 ≤30s、`batch_size_s=60`、`language=auto`。
- 知识型内容最终都转文字，**默认最低清视频即可**（见采集 SOP）；转写只抽 16k 单声道音轨，与原片清晰度无关。

## 2. 环境（共享 venv，跨项目复用）

- 解释器：`~/.venvs/funasr/bin/python`（Python 3.11，本机 Intel x86_64）
- 版本：funasr 1.4.3 / torch 2.2.2 / torchaudio 2.2.2
- 每次跑转写前必须：`export FUNASR_PYTHON="$HOME/.venvs/funasr/bin/python"`

### 安装命令（首次/换机重建，含已踩坑）

```bash
python3.11 -m venv ~/.venvs/funasr
~/.venvs/funasr/bin/pip install --upgrade pip
# 关键：llvmlite/numba/torch/torchaudio 必须强制用预编译 wheel，
# 否则会走源码编译失败（cmake 报错）；纯 Python 包（jieba 等）不加限制
~/.venvs/funasr/bin/pip install --only-binary=llvmlite,numba,torch,torchaudio \
    'torch==2.2.2' 'torchaudio==2.2.2' 'numpy<2' 'funasr==1.4.3' modelscope
```

**已踩坑**：
- `--only-binary=:all:` 不能用——会把纯 Python 的 `jieba`（只有 sdist）也拒掉。只对会编译的四个包列名。
- 必须用 Python 3.11；Python 3.14 装不上 onnxruntime/torch。
- 首次运行自动下载模型（SenseVoiceSmall ~1GB、fsmn-vad），属正常。

## 3. 批量转写（模型只加载一次）

脚本：`platforms/wechat_channels/video-transcribe/batch_transcribe.py`

```bash
export FUNASR_PYTHON="$HOME/.venvs/funasr/bin/python"
"$FUNASR_PYTHON" platforms/wechat_channels/video-transcribe/batch_transcribe.py \
    <视频目录> <输出目录>
# 例:
"$FUNASR_PYTHON" .../batch_transcribe.py \
    library/01_video/stock/交易的游戏/short \
    library/04_transcript/stock/交易的游戏/short
```

行为：
- 遍历 `<视频目录>/*.mp4`，**模型全程只加载一次**（不要逐文件调用 transcribe.py，那会每个都重载模型）。
- 每个：ffmpeg 抽 16k 单声道 wav → `model.generate(...)` → 写产物。
- **断点续跑**：`<输出目录>/<标题>/transcript.md` 已存在且 >50 字节则跳过。
- 长音频（直播回放 30–50 分钟）由 fsmn-vad 自动分段，无需手工切。

## 4. 输出与目录约定

- 产物：`<输出目录>/<视频文件名（去扩展名）>/transcript.md` + `transcript.json`
- 落库目录：`library/04_transcript/<domain>/<account>/{short,live}/<标题>/`
- `04_transcript/` 在 .gitignore（中间产物，不入库；网盘同步统一走后续流程）。
- `transcript.md` 头部记录：标题、转写时间、字数；正文为整段文本。

## 5. 性能与验收

- 实测 rtf ≈ 0.055（约 18 倍实时）：40 秒音频约 2 秒。
- 验收：
  - 字数与时长相称（中文口播约 250–350 字/分钟）。
  - **空稿判定**：`ffprobe` 有音频流但转写 0 字 = 纯配乐/无人声画面，属正常内容，**不要当下载失败**（如 short_411）。
  - 个别财经词误识别（如"骗线"→"片线"）可接受，进知识库前可人工/LLM 校。

## 6. 本次实绩（2026-09）

- 视频号「交易的游戏」：短视频 410 份 + 直播回放 25 份 = **435 份转写稿，0 失败**，仅 1 个纯配乐空稿。
