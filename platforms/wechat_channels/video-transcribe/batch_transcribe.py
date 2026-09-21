#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch_transcribe.py — FunASR SenseVoice 批量转写（模型只加载一次）

用法:
  FUNASR_PYTHON=<venv-python> python batch_transcribe.py <视频目录> <输出根目录>
  例: python batch_transcribe.py library/01_video/stock/交易的游戏/short \
                                    library/04_transcript/stock/交易的游戏/short

产物: <输出根目录>/<视频文件名>/transcript.md (+transcript.json)
断点: transcript.md 已存在且>50字节则跳过。长音频自动 fsmn-vad 分段。
"""
import sys, os, subprocess, glob, time, datetime, json
from pathlib import Path

VIDEO_ROOT, OUT_ROOT = sys.argv[1], sys.argv[2]

def extract_wav(video, tmpwav):
    subprocess.run(["ffmpeg", "-y", "-i", str(video), "-ac", "1", "-ar", "16000", "-vn", str(tmpwav)],
                   check=True, capture_output=True)

def main():
    from funasr import AutoModel
    print("加载模型 SenseVoiceSmall + fsmn-vad ...", flush=True)
    model = AutoModel(model="iic/SenseVoiceSmall", vad_model="fsmn-vad",
                      vad_kwargs={"max_single_segment_time": 30000}, disable_update=True)
    vids = sorted(glob.glob(str(Path(VIDEO_ROOT) / "*.mp4")))
    print(f"共 {len(vids)} 个待处理目录={VIDEO_ROOT}", flush=True)
    ok = fail = skip = 0
    for i, v in enumerate(vids, 1):
        base = Path(v).stem
        outdir = Path(OUT_ROOT) / base
        md = outdir / "transcript.md"
        if md.exists() and md.stat().st_size > 50:
            skip += 1; print(f"[{i}/{len(vids)}] 跳过 {base[:36]}", flush=True); continue
        outdir.mkdir(parents=True, exist_ok=True)
        tmpwav = outdir / "_audio16k.wav"
        try:
            extract_wav(v, tmpwav)
            t0 = time.time()
            res = model.generate(input=str(tmpwav), language="auto", use_itn=True, batch_size_s=60)
            text = (res[0]["text"] or "").strip()
            dt = time.time() - t0
            chars = len(text)
            md.write_text(f"# {base}\n\n> 自动转写 FunASR SenseVoice | {datetime.datetime.now():%Y-%m-%d} | 约 {chars} 字 | 转写耗时 {dt:.0f}s\n\n{text}\n")
            (outdir / "transcript.json").write_text(json.dumps(
                {"title": base, "text": text, "chars": chars, "transcribe_sec": round(dt, 1)},
                ensure_ascii=False, indent=2))
            tmpwav.unlink(missing_ok=True)
            ok += 1
            print(f"[{i}/{len(vids)}] OK {chars}字 {dt:.0f}s {base[:34]}", flush=True)
        except Exception as e:
            fail += 1
            print(f"[{i}/{len(vids)}] FAIL {base[:34]}: {e}", flush=True)
    print(f"\n=== 完成: 成功{ok} 失败{fail} 跳过{skip} ===", flush=True)

main()
