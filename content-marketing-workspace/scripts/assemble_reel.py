#!/usr/bin/env python3
"""
Ace Reel / TikTok / YouTube Shorts Auto-Assembler (Step 4)

Stitches downloaded Google Flow clips into a crisp 1080x1920 (9:16, 30fps, H.264/AAC)
vertical master, optionally applies ElevenLabs Speech-to-Speech voice locking, burns in
safe-zone On-Screen Text from `shots.json`, and optionally mixes a subtle background beat.

Usage:
  # Assemble from shots.json in a render folder:
  python3 assemble_reel.py --dir content-marketing-workspace/renders/ryoko-rain-indie-coup

  # Assemble + automatically run ElevenLabs Speech-to-Speech voice lock on every clip first:
  python3 assemble_reel.py --dir content-marketing-workspace/renders/ryoko-rain-indie-coup --voice-lock

  # Assemble specific clips directly (e.g., Part 1 15s test) with optional beat track:
  python3 assemble_reel.py --clips part1.mp4 --out test_part1_master.mp4 --voice-lock --music beat.mp3
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import textwrap
from pathlib import Path

from voice_lock_elevenlabs import convert_clip_sts, require_ffmpeg
from voice_lock_local import convert_clip_local

CAPTION_BIN = Path(__file__).resolve().parent / "render_caption_png"
CAPTION_SCRIPT = Path(__file__).resolve().parent / "render_caption_png.swift"


def probe_duration(video_path: Path) -> float:
    ffprobe = "ffprobe"
    for candidate in ("ffprobe", "/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe"):
        res = subprocess.run(["which", candidate] if "/" not in candidate else ["test", "-x", candidate],
                             capture_output=True)
        if res.returncode == 0:
            ffprobe = candidate
            break
    res = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return 8.0
    try:
        return float(res.stdout.strip())
    except ValueError:
        return 8.0


def normalize_and_caption_clip(
    src: Path,
    dst: Path,
    headline: str | None = None,
    sub_badge: str | None = None,
) -> None:
    ffmpeg = require_ffmpeg()
    base_vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1"
    af = "aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=9"

    overlay_png: Path | None = None
    try:
        if headline or sub_badge:
            overlay_png = dst.with_suffix(".caption.png")
            if CAPTION_BIN.exists():
                cap_cmd = [str(CAPTION_BIN), str(overlay_png), headline or "", sub_badge or ""]
            else:
                cap_cmd = ["swift", "-module-cache-path", "/tmp/swift-cache", str(CAPTION_SCRIPT), str(overlay_png), headline or "", sub_badge or ""]
            res_sw = subprocess.run(cap_cmd, capture_output=True, text=True)
            if res_sw.returncode != 0:
                sys.exit(f"Caption PNG render failed:\n{res_sw.stderr}")

            cmd = [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(src),
                "-i", str(overlay_png),
                "-filter_complex", f"[0:v]{base_vf}[v0];[v0][1:v]overlay=0:0[vout]",
                "-map", "[vout]", "-map", "0:a:0?",
                "-af", af,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                str(dst),
            ]
        else:
            cmd = [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(src),
                "-vf", base_vf,
                "-af", af,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                str(dst),
            ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"Failed processing {src.name}:\n{res.stderr}")
    finally:
        if overlay_png and overlay_png.exists():
            overlay_png.unlink()


def concat_clips(clips: list[Path], out_path: Path, music_path: Path | None = None, music_db: float = -22.0) -> None:
    ffmpeg = require_ffmpeg()
    concat_file = out_path.with_suffix(".concat.txt")
    stitched_no_music = out_path.with_suffix(".nomusic.mp4") if music_path else out_path

    try:
        concat_file.write_text("\n".join(f"file '{c.resolve()}'" for c in clips) + "\n", encoding="utf-8")
        cmd = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
            str(stitched_no_music),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"Concat failed:\n{res.stderr}")

        if music_path:
            if not music_path.exists():
                sys.exit(f"Music file not found: {music_path}")
            dur = probe_duration(stitched_no_music)
            fade_start = max(0.0, dur - 1.5)
            filter_complex = (
                f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{dur:.2f},"
                f"volume={music_db}dB,afade=t=out:st={fade_start:.2f}:d=1.5[bg];"
                f"[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]"
            )
            cmd_mix = [
                ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(stitched_no_music),
                "-i", str(music_path),
                "-filter_complex", filter_complex,
                "-map", "0:v:0", "-map", "[aout]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                str(out_path),
            ]
            res = subprocess.run(cmd_mix, capture_output=True, text=True)
            if res.returncode != 0:
                sys.exit(f"Music mix failed:\n{res.stderr}")
    finally:
        if concat_file.exists():
            concat_file.unlink()
        if music_path and stitched_no_music.exists():
            stitched_no_music.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ace 1080x1920 Reel / TikTok / Shorts Auto-Assembler")
    parser.add_argument("--dir", help="Render folder containing shots.json and clip_XX.mp4 files")
    parser.add_argument("--clips", nargs="+", help="Explicit list of video clip paths (overrides shots.json)")
    parser.add_argument("--out", help="Output final MP4 path")
    parser.add_argument("--voice-lock", action="store_true", help="Run ElevenLabs Speech-to-Speech voice lock on each clip")
    parser.add_argument("--local-voice-lock", action="store_true", help="Run FREE local Seed-VC v2 voice lock on Apple Silicon")
    parser.add_argument("--no-captions", action="store_true", help="Skip burning in safe-zone On-Screen Text")
    parser.add_argument("--music", help="Optional background instrumental beat MP3/WAV")
    parser.add_argument("--music-db", type=float, default=-22.0, help="Background beat volume in dB (default: -22)")
    args = parser.parse_args()

    work_items: list[tuple[Path, str | None, str | None]] = []

    if args.clips:
        for c in args.clips:
            p = Path(c)
            if not p.exists():
                sys.exit(f"Clip not found: {p}")
            work_items.append((p, None, None))
        out_path = Path(args.out) if args.out else Path(args.clips[0]).with_name("final-reel-1080x1920.mp4")
    elif args.dir:
        render_dir = Path(args.dir)
        manifest_path = render_dir / "shots.json"
        if not manifest_path.exists():
            sys.exit(f"shots.json not found in {render_dir}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for shot in manifest.get("shots", []):
            clip_path = render_dir / shot["clip_file"]
            voiced_candidate = clip_path.with_name(f"{clip_path.stem}_voiced{clip_path.suffix}")
            chosen = voiced_candidate if (voiced_candidate.exists() and not args.voice_lock) else clip_path
            if not chosen.exists():
                print(f"[Skip] Missing {clip_path.name} — download from Google Flow into {render_dir}")
                continue
            headline = None if args.no_captions else shot.get("on_screen_text")
            badge = None if args.no_captions else shot.get("sub_badge")
            work_items.append((chosen, headline, badge))
        if not work_items:
            sys.exit(f"No clips found yet in {render_dir}. Download clip_01.mp4..clip_06.mp4 from Flow first.")
        out_path = Path(args.out) if args.out else render_dir / f"{manifest.get('slug', 'ace')}-master-1080x1920.mp4"
    else:
        sys.exit("Provide either --dir <render_folder> or --clips <clip1.mp4 ...>")

    tmp_dir = out_path.parent / ".assemble_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    processed: list[Path] = []

    try:
        for idx, (clip, headline, badge) in enumerate(work_items, start=1):
            source_for_render = clip
            if args.local_voice_lock:
                print(f"[{idx}/{len(work_items)}] Local free voice-locking {clip.name} via Seed-VC v2...")
                source_for_render = convert_clip_local(clip)
            elif args.voice_lock:
                print(f"[{idx}/{len(work_items)}] Voice-locking {clip.name} via ElevenLabs Speech-to-Speech...")
                source_for_render = convert_clip_sts(clip)
            norm_path = tmp_dir / f"seg_{idx:02d}.mp4"
            print(f"[{idx}/{len(work_items)}] Formatting 1080x1920 + safe-zone captions for {source_for_render.name}...")
            normalize_and_caption_clip(source_for_render, norm_path, headline=headline, sub_badge=badge)
            processed.append(norm_path)

        print(f"Stitching {len(processed)} segment(s) -> {out_path} ...")
        concat_clips(processed, out_path, Path(args.music) if args.music else None, args.music_db)
        print(f"DONE! Ready to post (IG Reels / TikTok / YouTube Shorts): {out_path}")
    finally:
        for f in tmp_dir.glob("*"):
            f.unlink()
        if tmp_dir.exists():
            tmp_dir.rmdir()


if __name__ == "__main__":
    main()
