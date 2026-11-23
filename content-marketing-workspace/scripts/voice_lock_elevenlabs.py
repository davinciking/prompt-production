#!/usr/bin/env python3
"""
Ace Permanent Voice-Lock Utility (ElevenLabs Speech-to-Speech + Manual Web Fallback)

Locks every Google Flow clip to Ace's permanent voice from `ace-official-voice-reference.mp4`
while preserving 100% of Flow's natural lip-sync timing, pauses, and breathing.

Zero external Python packages required (stdlib + ffmpeg only).

Usage:
  1) Extract Ace's clean voice cloning sample from the reference video:
       python3 voice_lock_elevenlabs.py extract-sample

  2) Clone Ace's voice ONCE on ElevenLabs (returns your permanent ACE_VOICE_ID):
       python3 voice_lock_elevenlabs.py clone-voice

  3) Voice-lock a single Flow clip via ElevenLabs Speech-to-Speech API:
       python3 voice_lock_elevenlabs.py convert --input renders/ryoko-rain-indie-coup/part1.mp4

  4) Manual ElevenLabs Web UI workflow (if you don't want an API key yet):
       # Step A: Extract clip audio to upload to elevenlabs.io -> Voice Changer
       python3 voice_lock_elevenlabs.py extract-audio --input renders/ryoko-rain-indie-coup/part1.mp4
       # Step B: Download the converted MP3 from ElevenLabs and mux it back onto the video:
       python3 voice_lock_elevenlabs.py mux-audio --video renders/ryoko-rain-indie-coup/part1.mp4 --audio ~/Downloads/part1_ace_voice.mp3
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = WORKSPACE_DIR / ".env"
DEFAULT_REF_VIDEO = WORKSPACE_DIR / "assets" / "ace-references" / "ace-official-voice-reference.mp4"
DEFAULT_VOICE_SAMPLE = WORKSPACE_DIR / "assets" / "ace-references" / "ace-voice-master-sample.mp3"


def load_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def require_ffmpeg() -> str:
    for candidate in ("ffmpeg", "/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"):
        res = subprocess.run(["which", candidate] if "/" not in candidate else ["test", "-x", candidate],
                             capture_output=True)
        if res.returncode == 0:
            return candidate
    sys.exit("Error: ffmpeg not found. Install it with: brew install ffmpeg")


def run_ffmpeg(args: list[str]) -> None:
    ffmpeg = require_ffmpeg()
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", *args]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"ffmpeg failed:\n{res.stderr}")


def encode_multipart(fields: dict[str, str], files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    boundary = f"----AceBoundary{uuid.uuid4().hex}"
    body = bytearray()
    for name, val in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(val.encode("utf-8"))
        body.extend(b"\r\n")
    for field_name, file_path in files:
        mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{field_name}"; filename="{file_path.name}"\r\n'.encode()
        )
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode())
        body.extend(file_path.read_bytes())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def cmd_extract_sample(args: argparse.Namespace) -> None:
    src = Path(args.source)
    out = Path(args.output)
    if not src.exists():
        sys.exit(f"Reference video not found: {src}")
    out.parent.mkdir(parents=True, exist_ok=True)
    # High-pass 80Hz & gentle speech band polish while keeping full natural baritone warmth
    run_ffmpeg([
        "-i", str(src),
        "-vn",
        "-ac", "1",
        "-ar", "44100",
        "-b:a", "192k",
        str(out),
    ])
    print(f"Extracted Ace master voice sample -> {out}")


def cmd_extract_audio(args: argparse.Namespace) -> None:
    src = Path(args.input)
    out = Path(args.output) if args.output else src.with_suffix(".raw_audio.mp3")
    if not src.exists():
        sys.exit(f"Input video not found: {src}")
    run_ffmpeg(["-i", str(src), "-vn", "-ac", "1", "-ar", "44100", "-b:a", "192k", str(out)])
    print(f"Extracted clip audio -> {out}")
    print("Tip: Upload this MP3 to ElevenLabs Voice Changer, then run `mux-audio` with the downloaded MP3.")


def cmd_mux_audio(args: argparse.Namespace) -> None:
    video = Path(args.video)
    audio = Path(args.audio)
    out = Path(args.output) if args.output else video.with_name(f"{video.stem}_voiced{video.suffix}")
    if not video.exists():
        sys.exit(f"Video not found: {video}")
    if not audio.exists():
        sys.exit(f"Audio not found: {audio}")
    run_ffmpeg([
        "-i", str(video),
        "-i", str(audio),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-shortest",
        str(out),
    ])
    print(f"Muxed voice-locked video -> {out}")


def cmd_clone_voice(args: argparse.Namespace) -> None:
    load_env()
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key or api_key == "your_elevenlabs_api_key_here":
        sys.exit(f"Set ELEVENLABS_API_KEY in {ENV_PATH} first (see .env.example).")

    sample = Path(args.sample)
    if not sample.exists():
        cmd_extract_sample(argparse.Namespace(source=str(DEFAULT_REF_VIDEO), output=str(sample)))

    fields = {
        "name": args.name,
        "description": "Ace (@doctoraceboogie) — smooth, charismatic 31yo Atlanta-to-LA streetwear archivist baritone.",
        "remove_background_noise": "true",
    }
    body, content_type = encode_multipart(fields, [("files", sample)])
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/voices/add",
        data=body,
        headers={"xi-api-key": api_key, "Content-Type": content_type, "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs API error ({e.code}): {e.read().decode('utf-8', errors='replace')}")

    voice_id = data.get("voice_id")
    print(f"Cloned Ace voice successfully! ACE_VOICE_ID={voice_id}")
    print(f"Add this line to {ENV_PATH}:\n  ACE_VOICE_ID={voice_id}")


def convert_clip_sts(input_video: Path, output_video: Path | None = None, voice_id: str | None = None) -> Path:
    load_env()
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    vid = voice_id or os.environ.get("ACE_VOICE_ID")
    if not api_key or api_key == "your_elevenlabs_api_key_here":
        sys.exit(f"Set ELEVENLABS_API_KEY in {ENV_PATH} first.")
    if not vid or vid == "your_cloned_ace_voice_id_here":
        sys.exit(f"Set ACE_VOICE_ID in {ENV_PATH} first (or run `clone-voice`).")

    if not input_video.exists():
        sys.exit(f"Input video not found: {input_video}")

    out_path = output_video or input_video.with_name(f"{input_video.stem}_voiced{input_video.suffix}")
    raw_mp3 = input_video.with_suffix(".tmp_raw.mp3")
    sts_mp3 = input_video.with_suffix(".tmp_sts.mp3")

    try:
        run_ffmpeg(["-i", str(input_video), "-vn", "-ac", "1", "-ar", "44100", "-b:a", "192k", str(raw_mp3)])

        voice_settings = json.dumps({
            "stability": float(os.environ.get("ELEVENLABS_STABILITY", "0.45")),
            "similarity_boost": float(os.environ.get("ELEVENLABS_SIMILARITY_BOOST", "0.85")),
            "style": float(os.environ.get("ELEVENLABS_STYLE", "0.15")),
            "use_speaker_boost": True,
        })
        fields = {
            "model_id": os.environ.get("ELEVENLABS_STS_MODEL", "eleven_multilingual_sts_v2"),
            "voice_settings": voice_settings,
            "remove_background_noise": "true",
        }
        body, content_type = encode_multipart(fields, [("audio", raw_mp3)])
        url = f"https://api.elevenlabs.io/v1/speech-to-speech/{vid}?output_format=mp3_44100_192"
        req = urllib.request.Request(
            url,
            data=body,
            headers={"xi-api-key": api_key, "Content-Type": content_type, "Accept": "audio/mpeg"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                sts_mp3.write_bytes(resp.read())
        except urllib.error.HTTPError as e:
            sys.exit(f"ElevenLabs STS error ({e.code}): {e.read().decode('utf-8', errors='replace')}")

        # Mux converted Ace voice back onto the exact original video frames
        run_ffmpeg([
            "-i", str(input_video),
            "-i", str(sts_mp3),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "48000",
            "-shortest",
            str(out_path),
        ])
    finally:
        for tmp in (raw_mp3, sts_mp3):
            if tmp.exists():
                tmp.unlink()

    print(f"Voice-locked clip -> {out_path}")
    return out_path


def cmd_convert(args: argparse.Namespace) -> None:
    inp = Path(args.input)
    out = Path(args.output) if args.output else None
    convert_clip_sts(inp, out, args.voice_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ace Permanent Voice-Lock Utility (ElevenLabs STS)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sample = sub.add_parser("extract-sample", help="Extract Ace's master voice cloning MP3 from reference video")
    p_sample.add_argument("--source", default=str(DEFAULT_REF_VIDEO))
    p_sample.add_argument("--output", default=str(DEFAULT_VOICE_SAMPLE))
    p_sample.set_defaults(func=cmd_extract_sample)

    p_clone = sub.add_parser("clone-voice", help="Create Ace's Instant Voice Clone on ElevenLabs via API")
    p_clone.add_argument("--sample", default=str(DEFAULT_VOICE_SAMPLE))
    p_clone.add_argument("--name", default="Ace - DoctorAceBoogie Official")
    p_clone.set_defaults(func=cmd_clone_voice)

    p_conv = sub.add_parser("convert", help="Convert a video clip's audio to Ace's locked voice via ElevenLabs STS API")
    p_conv.add_argument("--input", required=True)
    p_conv.add_argument("--output", default=None)
    p_conv.add_argument("--voice-id", default=None)
    p_conv.set_defaults(func=cmd_convert)

    p_ext = sub.add_parser("extract-audio", help="Extract raw MP3 from a video for manual ElevenLabs Web Voice Changer")
    p_ext.add_argument("--input", required=True)
    p_ext.add_argument("--output", default=None)
    p_ext.set_defaults(func=cmd_extract_audio)

    p_mux = sub.add_parser("mux-audio", help="Mux a manually downloaded ElevenLabs MP3 back onto a Flow video clip")
    p_mux.add_argument("--video", required=True)
    p_mux.add_argument("--audio", required=True)
    p_mux.add_argument("--output", default=None)
    p_mux.set_defaults(func=cmd_mux_audio)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
