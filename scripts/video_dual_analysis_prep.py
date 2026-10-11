#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频双轨效果分析 · 预处理脚本（画面关键帧 + 音频客观特征）

为 multiplatform-media-fetch 的 video-effect-analysis.md 双轨分析提供统一、可复算的客观素材：
  画面：ffmpeg 定时抽帧 -> PIL dHash 相邻去重 -> Laplacian 清晰度评分 -> frames_manifest.csv
  音频：librosa 提 BPM/节拍点、RMS 能量包络、停顿(留白)、能量突变(拟音候选)、低/中/高频段能量占比、chroma 主音

用法：
  python3 video_dual_analysis_prep.py <video.mp4> <out_dir> [--fps 1/4]
产出（<out_dir>/ 下）：
  frames/f001.jpg ...              去重后关键帧（宽640）
  frames_manifest.csv              file,t_sec,sharpness
  audio_features.json              客观音频特征（估算值，调性等低可信项已标注）
  _audio22k.wav                    分析用单声道音频（可删）

边界（重要，避免过度解读）：
  - 本脚本只给“可计算”的客观特征；乐器音色、情绪、人声微反应(哼气/叹气/轻笑)、具体拟音(板凳声)
    无法由本脚本判定，须由分析者结合【画面帧事件 + 能量突变候选时间点 + 转写文案】给出“候选”，
    并标注“需人工复听确认”，严禁把推断写成“听到了”。
  - 频段能量占比 != 声源分离（无人声/伴奏分离模型）：低频多反映低音铺底/鼓，高频多反映弦乐/人声亮度，仅作旁证。
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
import librosa


def probe_duration(src: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nk=1:nw=1", str(src)],
        capture_output=True, text=True).stdout.strip()
    return float(out or 0.0)


def dhash(img: Image.Image, w: int = 9, h: int = 8) -> int:
    a = np.asarray(img.convert("L").resize((w, h)))
    bits = 0
    for row in (a[:, 1:] > a[:, :-1]):
        for b in row:
            bits = (bits << 1) | int(b)
    return bits


def sharpness(img: Image.Image) -> float:
    g = np.asarray(img.convert("L"), dtype=np.float64)
    lap = (-4 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1]
           + g[1:-1, :-2] + g[1:-1, 2:])
    return float(lap.var())


def extract_frames(src: Path, frdir: Path, interval: int):
    frdir.mkdir(parents=True, exist_ok=True)
    for f in frdir.glob("f*.jpg"):
        f.unlink()
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-vf", f"fps=1/{interval},scale=640:-1",
         "-q:v", "3", str(frdir / "f%03d.jpg")],
        capture_output=True)
    rows, prev_hash = [], None
    for i, f in enumerate(sorted(frdir.glob("f*.jpg"))):
        im = Image.open(f)
        h, s = dhash(im), sharpness(im)
        if prev_hash is not None and (h ^ prev_hash).bit_count() <= 5:
            f.unlink()  # 与上一保留帧近重复，删除
            continue
        prev_hash = h
        rows.append((f.name, round(i * interval, 1), round(s, 1)))
    return rows


def analyze_audio(src: Path, out: Path):
    wav = out / "_audio22k.wav"
    subprocess.run(["ffmpeg", "-y", "-i", str(src), "-vn", "-ac", "1",
                    "-ar", "22050", str(wav)], capture_output=True)
    y, sr = librosa.load(str(wav), sr=22050)
    hop = 512
    duration = float(len(y) / sr)

    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop)
    beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=hop)
    bpm = float(np.atleast_1d(tempo)[0])

    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    rtime = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop)
    # 按 1s 窗聚合能量
    per_sec = []
    for s0 in range(int(duration) + 1):
        m = (rtime >= s0) & (rtime < s0 + 1)
        per_sec.append(round(float(rms[m].mean()), 4) if m.any() else 0.0)
    rmax = max(per_sec) if per_sec else 1.0

    # 停顿/留白：能量 < 12% 峰值，持续 >=0.4s
    pauses, run = [], []
    for s0, v in enumerate(per_sec):
        low = v < 0.12 * rmax
        if low:
            run.append(s0)
        else:
            if len(run) >= 1 and (len(r)) >= 1:
                pass
            if len(run) >= 1:
                # 0.4s 粒度按秒采样，>=1s 才算明显留白；句读级更短停顿另由差值体现
                if run[-1] - run[0] + 1 >= 1:
                    pauses.append([run[0], run[-1] + 1])
            run = []
    if run and run[-1] - run[0] + 1 >= 1:
        pauses.append([run[0], run[-1] + 1])

    # 能量突变（拟音/重音候选）：0.5s 窗 log 能量一阶差分 top 峰值
    half = []
    for c in np.arange(0.25, duration, 0.5):
        m = (rtime >= c - 0.25) & (rtime < c + 0.25)
        half.append((float(c), float(rms[m].mean()) if m.any() else 1e-4))
    events = []
    for k in range(1, len(half) - 1):
        t0, v0 = half[k - 1]
        t1, v1 = half[k]
        if v0 > 1e-4 and v1 / v0 > 1.6 and v1 > 0.25 * rmax:
            events.append([round(t1, 2), round(v1 / v0, 2)])
    events = sorted(events, key=lambda x: -x[1])[:10]
    events = sorted(events, key=lambda x: x[0])

    # 频段能量占比（全曲 + 6 段时间窗）
    S = np.abs(librosa.stft(y, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    def band_ratio(seg):
        e = seg.sum(axis=1)
        lo = e[freqs < 250].sum()
        mi = e[(freqs >= 250) & (freqs < 2000)].sum()
        hi = e[freqs >= 2000].sum()
        tot = lo + mi + hi + 1e-9
        return [round(float(lo / tot), 3), round(float(mi / tot), 3),
                round(float(hi / tot), 3)]
    overall = band_ratio(S)
    windows = []
    ncol = S.shape[1]
    for w in range(6):
        c0, c1 = int(w * ncol / 6), int((w + 1) * ncol / 6)
        windows.append(band_ratio(S[:, c0:c1]))

    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop)
    pc = chroma.mean(axis=1)
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    top_pc = [names[i] for i in np.argsort(pc)[::-1][:3]]

    return {
        "duration_sec": round(duration, 2),
        "bpm_estimated": round(bpm, 1),
        "beat_count": int(len(beat_times)),
        "beat_times_sample": [round(float(t), 2) for t in beat_times[:40]],
        "rms_per_sec": per_sec,
        "rms_peak": round(float(rmax), 4),
        "pauses_lowenergy_sec": pauses,
        "energy_burst_candidates": events,
        "band_energy_ratio_low_mid_high": overall,
        "band_ratio_6windows": windows,
        "chroma_top3_pitchclass_lowconfidence": top_pc,
        "_note": "BPM/节拍为算法估算；频段占比非声源分离；chroma主音低可信。乐器/情绪/拟音须人工复听，勿仅凭本文件断言。",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out_dir")
    ap.add_argument("--interval", type=int, default=None,
                    help="抽帧间隔秒；默认长视频(>90s)5s、短视频3s")
    args = ap.parse_args()
    src = Path(args.video).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    dur = probe_duration(src)
    interval = args.interval or (5 if dur > 90 else 3)
    rows = extract_frames(src, out / "frames", interval)
    with open(out / "frames_manifest.csv", "w", encoding="utf-8") as f:
        f.write("file,t_sec,sharpness\n")
        for r in rows:
            f.write(",".join(map(str, r)) + "\n")
    feats = analyze_audio(src, out)
    feats["frame_interval_sec"] = interval
    feats["frames_kept"] = len(rows)
    json.dump(feats, open(out / "audio_features.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"duration={dur:.1f}s interval={interval}s frames_kept={len(rows)} "
          f"bpm~{feats['bpm_estimated']} bursts={len(feats['energy_burst_candidates'])} "
          f"pauses={len(feats['pauses_lowenergy_sec'])}")
    print("OUT", out)


if __name__ == "__main__":
    main()
