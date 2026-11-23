#!/usr/bin/env python3
"""
Ace Signature Vocal Chain (Option 1 — Real Human Mic -> Studio Character Master)
================================================================================
Turns raw external-mic or voice-memo recordings into a locked, broadcast-ready
Ace baritone vocal track at $0/mo, 100% offline via ffmpeg.

Presets:
  1. natural_warm        (0.0 st)  : Pure studio polish on your natural voice
  2. ace_baritone_subtle (-1.0 st) : Subtle deeper character weight + radio warmth (Recommended)
  3. ace_baritone_deep   (-2.0 st) : Distinct deeper animated baritone register

Usage:
  # 1. Audition all 3 presets side-by-side on a 15s mic test:
  python3.11 content-marketing-workspace/scripts/ace_vocal_chain.py \
      --input /path/to/raw_mic_test.m4a --audition

  # 2. Master a full take with your locked preset:
  python3.11 content-marketing-workspace/scripts/ace_vocal_chain.py \
      --input /path/to/take.wav --preset ace_baritone_subtle --output /path/to/ace_master.wav

  # 3. Master + directly mux onto a silent video clip:
  python3.11 content-marketing-workspace/scripts/ace_vocal_chain.py \
      --input /path/to/take.wav --preset ace_baritone_subtle \
      --mux-video /path/to/silent_clip.mp4 --output /path/to/final_clip.mp4
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

FFMPEG = "/opt/homebrew/bin/ffmpeg"
FFPROBE = "/opt/homebrew/bin/ffprobe"


@dataclass(frozen=True)
class VocalPreset:
    name: str
    description: str
    pitch_semitones: float
    highpass_hz: int
    denoise_nf: int        # afftdn noise floor in dB (negative; 0 disables)
    warmth_db: float       # +dB at 115 Hz (chest warmth)
    mud_cut_db: float      # -dB at 270 Hz (boxy room mud cut)
    presence_db: float     # +dB at 3200 Hz (crisp intelligibility on phone speakers)
    sibilance_cut_db: float  # -dB at 6800 Hz (gentle de-ess)
    air_db: float          # +dB at 10500 Hz (studio sheen)
    comp_threshold_db: float
    comp_ratio: float
    target_lufs: float
    rasp_cut_low_db: float = 0.0    # optional gentle dip at 2100 Hz to smooth throat grit
    rasp_cut_high_db: float = 0.0   # optional gentle dip at 4800 Hz to smooth harsh rasp
    comp_attack_ms: float = 8.0
    comp_release_ms: float = 110.0
    pace_tempo: float = 1.0         # >1.0 tightens pacing without changing pitch
    trim_pauses_sec: float = 0.0    # >0 caps internal pauses to N seconds


PRESETS: dict[str, VocalPreset] = {
    "ace_natural_signature": VocalPreset(
        name="ace_natural_signature",
        description="0.0 st — warmer/brighter broadcast EQ, 15% smoother rasp, tighter natural pacing (1.04x + trimmed gaps)",
        pitch_semitones=0.0,
        highpass_hz=72,
        denoise_nf=-28,
        warmth_db=3.6,
        mud_cut_db=-3.0,
        presence_db=3.4,
        sibilance_cut_db=-2.8,
        air_db=3.4,
        comp_threshold_db=-18.5,
        comp_ratio=2.8,
        target_lufs=-14.0,
        rasp_cut_low_db=-1.6,
        rasp_cut_high_db=-2.0,
        comp_attack_ms=16.0,
        comp_release_ms=140.0,
        pace_tempo=1.04,
        trim_pauses_sec=0.28,
    ),
    "ace_natural_snappy": VocalPreset(
        name="ace_natural_snappy",
        description="0.0 st — same warm/bright smooth EQ with punchier short-form Reel pacing (1.07x + tighter gaps)",
        pitch_semitones=0.0,
        highpass_hz=72,
        denoise_nf=-28,
        warmth_db=3.6,
        mud_cut_db=-3.0,
        presence_db=3.4,
        sibilance_cut_db=-2.8,
        air_db=3.4,
        comp_threshold_db=-18.5,
        comp_ratio=2.8,
        target_lufs=-14.0,
        rasp_cut_low_db=-1.6,
        rasp_cut_high_db=-2.0,
        comp_attack_ms=16.0,
        comp_release_ms=140.0,
        pace_tempo=1.07,
        trim_pauses_sec=0.22,
    ),
    "natural_warm": VocalPreset(
        name="natural_warm",
        description="0.0 semitones — pure studio broadcast polish on your natural voice",
        pitch_semitones=0.0,
        highpass_hz=75,
        denoise_nf=-28,
        warmth_db=2.5,
        mud_cut_db=-2.8,
        presence_db=2.8,
        sibilance_cut_db=-2.2,
        air_db=1.8,
        comp_threshold_db=-18.0,
        comp_ratio=3.2,
        target_lufs=-14.0,
    ),
    "ace_baritone_subtle": VocalPreset(
        name="ace_baritone_subtle",
        description="-1.0 semitones — subtle deeper Ace baritone swagger + radio chest warmth",
        pitch_semitones=-1.0,
        highpass_hz=70,
        denoise_nf=-28,
        warmth_db=3.2,
        mud_cut_db=-3.2,
        presence_db=3.2,
        sibilance_cut_db=-2.5,
        air_db=2.0,
        comp_threshold_db=-18.0,
        comp_ratio=3.5,
        target_lufs=-14.0,
    ),
    "ace_baritone_deep": VocalPreset(
        name="ace_baritone_deep",
        description="-2.0 semitones — distinctly deeper 3D animated character voice",
        pitch_semitones=-2.0,
        highpass_hz=68,
        denoise_nf=-28,
        warmth_db=3.5,
        mud_cut_db=-3.8,
        presence_db=3.6,
        sibilance_cut_db=-2.5,
        air_db=2.2,
        comp_threshold_db=-17.5,
        comp_ratio=3.8,
        target_lufs=-14.0,
    ),
}


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"Command failed:\n{' '.join(cmd)}\n\nSTDERR:\n{res.stderr}")
    return res


def build_base_filter_chain(
    preset: VocalPreset,
    pitch_override: float | None = None,
    disable_denoise: bool = False,
) -> str:
    semitones = preset.pitch_semitones if pitch_override is None else pitch_override
    filters: list[str] = [
        # 1. Normalize sample rate & mono speech bus cleanly
        "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono",
        # 2. Cut low-end rumble / mic stand thumps
        f"highpass=f={preset.highpass_hz}:poles=2",
    ]

    # 3. Gentle FFT room noise suppression (safe for treated or semi-treated rooms)
    if not disable_denoise and preset.denoise_nf < 0:
        filters.append(f"afftdn=nf={preset.denoise_nf}:tn=1")

    # 3b. Optional automatic pause tightening (keeps natural breath, trims long dead air cleanly)
    if preset.trim_pauses_sec > 0.0:
        filters.append(
            f"silenceremove=stop_periods=-1:stop_duration={preset.trim_pauses_sec:.2f}"
            f":stop_threshold=-44dB:detection=rms:window=0.05"
        )

    # 4. Optional pitch shift (tempo-preserved via asetrate + atempo) and/or pace lift
    if abs(semitones) > 0.01:
        factor = math.pow(2.0, semitones / 12.0)
        new_rate = round(48000 * factor)
        tempo = (1.0 / factor) * preset.pace_tempo
        filters.append(f"asetrate={new_rate}")
        filters.append("aresample=48000")
        filters.append(f"atempo={tempo:.6f}")
    elif abs(preset.pace_tempo - 1.0) > 0.005:
        filters.append(f"atempo={preset.pace_tempo:.6f}")

    # 5. Ace Broadcast EQ Curve (chest warmth, boxy mud cut, optional 15% rasp smoothing, presence, de-ess, silky air)
    filters.extend([
        f"equalizer=f=120:t=q:w=1.0:g={preset.warmth_db}",
        f"equalizer=f=285:t=q:w=1.4:g={preset.mud_cut_db}",
    ])
    if abs(preset.rasp_cut_low_db) > 0.01:
        filters.append(f"equalizer=f=2100:t=q:w=1.8:g={preset.rasp_cut_low_db}")
    filters.append(f"equalizer=f=3400:t=q:w=1.25:g={preset.presence_db}")
    if abs(preset.rasp_cut_high_db) > 0.01:
        filters.append(f"equalizer=f=4800:t=q:w=2.0:g={preset.rasp_cut_high_db}")
    filters.extend([
        f"equalizer=f=6800:t=q:w=2.2:g={preset.sibilance_cut_db}",
        f"equalizer=f=10500:t=q:w=0.85:g={preset.air_db}",
        # 6. Smooth optical-style voiceover compression + soft peak safety limiter
        f"acompressor=threshold={preset.comp_threshold_db}dB:ratio={preset.comp_ratio}:attack={preset.comp_attack_ms}:release={preset.comp_release_ms}:knee=4:makeup=3.0",
        "alimiter=limit=-1.2dB:attack=3:release=50:level=disabled",
    ])
    return ",".join(filters)


def measure_loudnorm(input_path: Path, base_chain: str, target_lufs: float) -> dict[str, str]:
    """Two-pass EBU R128 loudness analysis for accurate, distortion-free mastering."""
    analyze_filter = f"{base_chain},loudnorm=I={target_lufs}:TP=-1.5:LRA=8:print_format=json"
    res = run_cmd([
        FFMPEG, "-hide_banner", "-i", str(input_path),
        "-af", analyze_filter,
        "-f", "null", "-",
    ])
    matches = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr, flags=re.DOTALL)
    if not matches:
        return {}
    return json.loads(matches[-1])


def process_voice(
    input_path: Path,
    output_path: Path,
    preset: VocalPreset,
    pitch_override: float | None = None,
    disable_denoise: bool = False,
) -> Path:
    base_chain = build_base_filter_chain(
        preset, pitch_override=pitch_override, disable_denoise=disable_denoise
    )
    stats = measure_loudnorm(input_path, base_chain, preset.target_lufs)

    if stats and stats.get("input_i") not in (None, "-inf"):
        loudnorm_pass2 = (
            f"loudnorm=I={preset.target_lufs}:TP=-1.5:LRA=8:linear=true"
            f":measured_I={stats['input_i']}"
            f":measured_LRA={stats['input_lra']}"
            f":measured_TP={stats['input_tp']}"
            f":measured_thresh={stats['input_thresh']}"
            f":offset={stats['target_offset']}"
        )
    else:
        loudnorm_pass2 = f"loudnorm=I={preset.target_lufs}:TP=-1.5:LRA=8"

    full_chain = f"{base_chain},{loudnorm_pass2},aresample=48000,pan=stereo|c0=c0|c1=c0"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ext = output_path.suffix.lower()
    if ext == ".mp3":
        codec_args = ["-c:a", "libmp3lame", "-b:a", "256k"]
    elif ext == ".m4a":
        codec_args = ["-c:a", "aac", "-b:a", "256k"]
    else:
        codec_args = ["-c:a", "pcm_s24le"]

    run_cmd([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(input_path),
        "-af", full_chain,
        "-ar", "48000", "-ac", "2",
        *codec_args,
        str(output_path),
    ])
    return output_path


def mux_onto_video(video_path: Path, mastered_audio: Path, output_mp4: Path) -> Path:
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    run_cmd([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(video_path),
        "-i", str(mastered_audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-shortest", "-movflags", "+faststart",
        str(output_mp4),
    ])
    return output_mp4


def main() -> None:
    parser = argparse.ArgumentParser(description="Ace Signature Vocal Chain (Option 1)")
    parser.add_argument("--input", required=True, type=Path, help="Raw mic recording (.wav, .m4a, .mp3, .aiff)")
    parser.add_argument(
        "--preset",
        default="ace_natural_signature",
        choices=list(PRESETS.keys()),
        help="Vocal preset (default: ace_natural_signature)",
    )
    parser.add_argument(
        "--audition",
        action="store_true",
        help="Render all 3 presets side-by-side so you can pick Ace's locked voice",
    )
    parser.add_argument("--pitch-semitones", type=float, default=None, help="Optional custom pitch shift override")
    parser.add_argument("--no-denoise", action="store_true", help="Skip FFT room denoise (for studio booth recordings)")
    parser.add_argument("--mux-video", type=Path, default=None, help="Optional video clip to mux mastered voice onto")
    parser.add_argument("--output", type=Path, default=None, help="Output file (or folder when using --audition)")
    args = parser.parse_args()

    if not args.input.exists():
        sys.exit(f"Input audio not found: {args.input}")

    if args.audition:
        out_dir = args.output or (args.input.parent / f"{args.input.stem}_ace_auditions")
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"Auditioning 3 Ace Vocal Chain presets on: {args.input.name}")
        for idx, (name, preset) in enumerate(PRESETS.items(), start=1):
            out_file = out_dir / f"{idx:02d}_{name}.wav"
            process_voice(args.input, out_file, preset, disable_denoise=args.no_denoise)
            print(f"  [{idx}] {out_file}  ({preset.description})")
        return

    preset = PRESETS[args.preset]
    if args.mux_video:
        if not args.mux_video.exists():
            sys.exit(f"Video not found: {args.mux_video}")
        tmp_wav = Path("/tmp") / f"{args.input.stem}_{preset.name}.wav"
        process_voice(
            args.input, tmp_wav, preset,
            pitch_override=args.pitch_semitones,
            disable_denoise=args.no_denoise,
        )
        out_mp4 = args.output or args.mux_video.with_name(f"{args.mux_video.stem}_ace_voice.mp4")
        mux_onto_video(args.mux_video, tmp_wav, out_mp4)
        tmp_wav.unlink(missing_ok=True)
        print(f"Muxed Ace Vocal Chain ({preset.name}) -> {out_mp4}")
    else:
        out_wav = args.output or args.input.with_name(f"{args.input.stem}_{preset.name}.wav")
        process_voice(
            args.input, out_wav, preset,
            pitch_override=args.pitch_semitones,
            disable_denoise=args.no_denoise,
        )
        print(f"Mastered Ace Vocal Chain ({preset.name}) -> {out_wav}")


if __name__ == "__main__":
    main()
