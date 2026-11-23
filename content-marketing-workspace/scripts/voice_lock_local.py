#!/usr/bin/env python3
"""
Ace Free Local Voice-Lock Utility (100% Offline on Apple Silicon Mac — $0/mo)

Proven Studio Pipeline:
  1. Demucs (`htdemucs`) isolates pure dry vocals from BOTH the reference audio
     (`ace-voice-clean-vocal.wav`) AND every incoming Google Flow clip (so hidden
     Flow background music/beats never corrupt voice conversion).
  2. Seed-VC 44.1 kHz F0 Pitch-Locked DiT (`tools/seed-vc/inference.py` with
     `--f0-condition True --auto-f0-adjust True`) maps the source speech cleanly
     onto Ace's exact baritone pitch register and vocal timbre at 44.1 kHz studio
     resolution while keeping 100% frame-accurate lip-sync timing.
  3. Loudness-normalizes to -14 LUFS and muxes cleanly onto the exact original
     video frames.

Usage:
  # One-time reference isolation (already cached at assets/ace-references/ace-voice-clean-vocal.wav):
  python3 content-marketing-workspace/scripts/voice_lock_local.py isolate-reference

  # Voice-lock any Flow clip completely offline ($0):
  python3 content-marketing-workspace/scripts/voice_lock_local.py convert \
    --input content-marketing-workspace/renders/ryoko-rain-indie-coup/part1.mp4
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
SEED_VC_DIR = WORKSPACE_DIR / "tools" / "seed-vc"
VENV_PYTHON = SEED_VC_DIR / ".venv" / "bin" / "python"
REF_MP3 = WORKSPACE_DIR / "assets" / "ace-references" / "ace-voice-master-sample.mp3"
CLEAN_VOCAL_WAV = WORKSPACE_DIR / "assets" / "ace-references" / "ace-voice-clean-vocal.wav"


def require_ffmpeg() -> str:
    for candidate in ("/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "ffmpeg"):
        res = subprocess.run(["test", "-x", candidate] if "/" in candidate else ["which", candidate], capture_output=True)
        if res.returncode == 0:
            return candidate
    sys.exit("Error: ffmpeg not found. Install it with: brew install ffmpeg")


def run_ffmpeg(args: list[str]) -> None:
    ffmpeg = require_ffmpeg()
    res = subprocess.run([ffmpeg, "-y", "-hide_banner", "-loglevel", "error", *args], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{res.stderr}")


def ensure_venv() -> None:
    if not VENV_PYTHON.exists():
        sys.exit(f"Seed-VC virtualenv not found at {VENV_PYTHON}. Run setup first.")


def isolate_vocals_demucs(src_audio: Path, out_wav: Path, sample_rate: int = 44100) -> Path:
    """Strip any background music/beats from an audio/video file using Demucs htdemucs."""
    ensure_venv()
    tmp_sep = Path("/tmp") / f"ace_demucs_{src_audio.stem}"
    tmp_sep.mkdir(parents=True, exist_ok=True)
    stereo_wav = tmp_sep / f"{src_audio.stem}_in.wav"

    try:
        run_ffmpeg(["-i", str(src_audio), "-vn", "-ac", "2", "-ar", "44100", str(stereo_wav)])
        res = subprocess.run(
            [
                str(VENV_PYTHON), "-m", "demucs",
                "--two-stems=vocals",
                "-n", "htdemucs",
                "-o", str(tmp_sep),
                str(stereo_wav),
            ],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            sys.exit(f"Demucs vocal separation failed:\n{res.stdout}\n{res.stderr}")

        matches = list(tmp_sep.rglob("vocals.wav"))
        if not matches:
            sys.exit(f"Could not locate vocals.wav under {tmp_sep}")
        vocals_wav = matches[0]

        out_wav.parent.mkdir(parents=True, exist_ok=True)
        run_ffmpeg([
            "-i", str(vocals_wav),
            "-ac", "1",
            "-ar", str(sample_rate),
            "-af", "highpass=f=70",
            str(out_wav),
        ])
    finally:
        shutil.rmtree(tmp_sep, ignore_errors=True)

    return out_wav


def isolate_reference(src_audio: Path = REF_MP3, out_wav: Path = CLEAN_VOCAL_WAV) -> Path:
    if not src_audio.exists():
        sys.exit(f"Reference audio not found: {src_audio}")
    print(f"Isolating Ace's pure vocal from {src_audio.name} using Demucs...")
    isolate_vocals_demucs(src_audio, out_wav, sample_rate=44100)
    print(f"Clean isolated Ace vocal reference saved -> {out_wav}")
    return out_wav


def convert_clip_local(
    input_video: Path,
    output_video: Path | None = None,
    target_voice: Path = CLEAN_VOCAL_WAV,
    diffusion_steps: int = 50,
    cfg_rate: float = 0.7,
    semi_tone_shift: int = 0,
) -> Path:
    ensure_venv()
    if not input_video.exists():
        sys.exit(f"Input video not found: {input_video}")
    if not target_voice.exists():
        target_voice = isolate_reference(REF_MP3, target_voice)

    out_path = output_video or input_video.with_name(f"{input_video.stem}_voiced{input_video.suffix}")
    tmp_dir = Path("/tmp") / f"ace_vc_{input_video.stem}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    src_vocal_wav = tmp_dir / f"{input_video.stem}_clean_vocal.wav"
    vc_out_dir = tmp_dir / "vc_out"
    vc_out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Strip any hidden background beat from Flow clip so only pure dry speech enters Seed-VC
        print(f"1/3 Isolating clean dry speech from {input_video.name} with Demucs...")
        isolate_vocals_demucs(input_video, src_vocal_wav, sample_rate=44100)

        # 2. Run 44.1 kHz F0 pitch-locked Seed-VC conversion
        print(f"2/3 Running 44.1 kHz F0 pitch-locked Seed-VC on {input_video.name} (steps={diffusion_steps})...")
        env = os.environ.copy()
        env["MPLCONFIGDIR"] = "/tmp/mpl-cache"
        cmd = [
            str(VENV_PYTHON),
            str(SEED_VC_DIR / "inference.py"),
            "--source", str(src_vocal_wav.resolve()),
            "--target", str(target_voice.resolve()),
            "--output", str(vc_out_dir.resolve()),
            "--diffusion-steps", str(diffusion_steps),
            "--length-adjust", "1.0",
            "--inference-cfg-rate", str(cfg_rate),
            "--f0-condition", "True",
            "--auto-f0-adjust", "True",
            "--semi-tone-shift", str(semi_tone_shift),
            "--fp16", "False",
        ]
        res = subprocess.run(cmd, cwd=str(SEED_VC_DIR), env=env, capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"Seed-VC 44kHz F0 failed:\n{res.stdout}\n{res.stderr}")

        wavs = sorted(vc_out_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not wavs:
            sys.exit(f"Seed-VC produced no output WAV in {vc_out_dir}:\n{res.stdout}\n{res.stderr}")
        converted_wav = wavs[0]

        # 3. Loudness-normalize (-14 LUFS) & mux Ace's 44.1 kHz locked voice onto the exact video frames
        print(f"3/3 Muxing locked Ace voice onto {input_video.name}...")
        run_ffmpeg([
            "-i", str(input_video),
            "-i", str(converted_wav),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-af", "aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=9",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-ac", "2",
            "-shortest",
            str(out_path),
        ])
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"Local 44.1 kHz voice-locked video saved -> {out_path}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Ace Free Local Voice-Lock Utility (Demucs + 44.1kHz F0 Seed-VC)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_iso = sub.add_parser("isolate-reference", help="Strip background beat from Ace reference MP3 using Demucs")
    p_iso.add_argument("--source", default=str(REF_MP3))
    p_iso.add_argument("--output", default=str(CLEAN_VOCAL_WAV))

    p_conv = sub.add_parser("convert", help="Convert a video clip's speech to Ace's exact locked voice locally")
    p_conv.add_argument("--input", required=True)
    p_conv.add_argument("--output", default=None)
    p_conv.add_argument("--target", default=str(CLEAN_VOCAL_WAV))
    p_conv.add_argument("--steps", type=int, default=50)
    p_conv.add_argument("--cfg-rate", type=float, default=0.7)
    p_conv.add_argument("--semi-tone-shift", type=int, default=0)

    args = parser.parse_args()
    if args.command == "isolate-reference":
        isolate_reference(Path(args.source), Path(args.output))
    elif args.command == "convert":
        convert_clip_local(
            Path(args.input),
            Path(args.output) if args.output else None,
            Path(args.target),
            diffusion_steps=args.steps,
            cfg_rate=args.cfg_rate,
            semi_tone_shift=args.semi_tone_shift,
        )


if __name__ == "__main__":
    main()
