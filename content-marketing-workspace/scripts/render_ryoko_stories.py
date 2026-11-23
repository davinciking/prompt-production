#!/usr/bin/env python3
"""
Ace 3-Frame Day-of-Drop Instagram Story Funnel Renderer (1080x1920, 9:16)
Pilot 01: The Indie Streetwear Coup (Ryoko Rain)

Produces all 3 ready-to-upload Instagram Story assets at ZERO Flow credits:
  - Frame 1 (09:30 AM): story_01_poll_0930am.png      (Static 1080x1920 + open native Poll Sticker zone)
  - Frame 2 (01:15 PM): story_02_macro_0115pm.mp4     (Animated 8s macro textile video + locked Ace voice + open Question Sticker zone)
  - Frame 3 (05:00 PM): story_03_conversion_0500pm.mp4 (Animated 8s Slide 8 showcase + circular Ace PiP video + open Feed Link Sticker zone)
"""

from __future__ import annotations

import base64
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
RENDERS_DIR = WORKSPACE_DIR / "renders" / "ryoko-rain-indie-coup"
STORIES_DIR = RENDERS_DIR / "stories"
ASSETS_DIR = WORKSPACE_DIR / "assets" / "ace-references"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FFMPEG = "/opt/homebrew/bin/ffmpeg"


def img_data_uri(path: Path) -> str:
    if not path.exists():
        sys.exit(f"Missing required asset: {path}")
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    ext = path.suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64,{b64}"


def run(cmd: list[str]) -> None:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"Command failed:\n{' '.join(cmd)}\n{res.stderr}")


def render_html_to_png(html: str, out_png: Path, tmp_dir: Path, transparent: bool = False) -> None:
    chrome_profile = tmp_dir / "chrome_profile"
    chrome_profile.mkdir(parents=True, exist_ok=True)
    html_path = tmp_dir / f"{out_png.stem}.html"
    raw_png = tmp_dir / f"raw_{out_png.name}"
    html_path.write_text(html, encoding="utf-8")

    cmd = [
        CHROME_BIN,
        "--headless=new",
        f"--user-data-dir={chrome_profile}",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--window-size=1080,2020",
        "--force-device-scale-factor=1",
    ]
    if transparent:
        cmd.append("--default-background-color=00000000")
    cmd.extend([f"--screenshot={raw_png}", f"file://{html_path}"])
    run(cmd)

    # Crop exact 1080x1920 from top-left (avoids macOS headless Chrome titlebar wrap)
    run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw_png),
         "-vf", "crop=1080:1920:0:0", str(out_png)])


COMMON_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  width: 1080px;
  height: 1920px;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "SF Pro Display", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.mono {
  font-family: "SF Mono", "Menlo", "Monaco", "Courier New", monospace;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.pill {
  display: inline-block;
  padding: 10px 18px;
  border-radius: 8px;
  font-size: 20px;
  font-weight: 800;
}
"""


def build_frame_1(bg_path: Path, tmp_dir: Path) -> Path:
    bg_uri = img_data_uri(bg_path)
    out_png = STORIES_DIR / "story_01_poll_0930am.png"
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON_CSS}</style></head>
    <body style="background:#0E0E10; color:#F4EFE6;">
      <div style="width:1080px; height:1920px; position:relative; overflow:hidden;">
        <img src="{bg_uri}" style="width:100%; height:100%; object-fit:cover; object-position:center center;" />
        <!-- Cinematic top & bottom scrims for crisp mobile readability -->
        <div style="position:absolute; inset:0; background:linear-gradient(to bottom, rgba(10,11,13,0.88) 0%, rgba(10,11,13,0.42) 34%, rgba(10,11,13,0.28) 58%, rgba(10,11,13,0.86) 100%);"></div>

        <!-- Upper Safe Zone Copy (below IG story progress bar & profile header: starts y=220) -->
        <div style="position:absolute; top:220px; left:68px; right:68px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:26px;">
            <span class="pill mono" style="background:#FF5500; color:#FFFFFF;">MORNING DISPATCH</span>
            <span class="pill mono" style="background:rgba(14,14,16,0.78); border:1.5px solid rgba(214,180,108,0.65); color:#E5C883;">@DOCTORACEBOOGIE</span>
          </div>

          <div style="font-size:58px; font-weight:900; line-height:1.08; letter-spacing:-0.02em; color:#FFFFFF; text-shadow:0 4px 20px rgba(0,0,0,0.85); margin-bottom:22px;">
            The NBA tunnel walk changed forever this morning.
          </div>

          <div style="background:rgba(14,14,16,0.78); border-left:6px solid #FF5500; border-radius:10px; padding:22px 26px; font-size:30px; line-height:1.38; color:#F4EFE6; backdrop-filter:blur(6px);">
            European luxury logos are getting benched for <strong style="color:#E5C883;">grassroots, hooper-owned indie labels.</strong>
          </div>
        </div>

        <!-- Clean Lower-Third Framing for Native IG Two-Option Poll Sticker (y=1240..1620 kept open) -->
        <div style="position:absolute; bottom:210px; left:68px; right:68px; text-align:center;">
          <div class="mono" style="font-size:21px; font-weight:800; color:#E5C883; margin-bottom:14px; text-shadow:0 2px 12px rgba(0,0,0,0.9);">
            WHICH LANE WINS THE 2026 TUNNEL? VOTE BELOW
          </div>
          <div style="height:210px; border:1.5px dashed rgba(244,239,230,0.22); border-radius:20px; background:rgba(14,14,16,0.30);"></div>
        </div>
      </div>
    </body></html>"""
    render_html_to_png(html, out_png, tmp_dir, transparent=False)
    print(f"Rendered Story Frame 1 -> {out_png}")
    return out_png


def build_frame_2(tmp_dir: Path) -> Path:
    src_video = RENDERS_DIR / "shot4_ace_locked.mp4"
    if not src_video.exists():
        sys.exit(f"Missing Shot 4 macro video: {src_video}")

    overlay_png = tmp_dir / "story_02_overlay.png"
    out_mp4 = STORIES_DIR / "story_02_macro_0115pm.mp4"

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON_CSS}</style></head>
    <body style="background:transparent;">
      <div style="width:1080px; height:1920px; position:relative;">
        <!-- Subtle top & bottom gradient scrims so the macro weave stays unobstructed in the center -->
        <div style="position:absolute; top:0; left:0; right:0; height:760px; background:linear-gradient(to bottom, rgba(10,11,13,0.90) 0%, rgba(10,11,13,0.70) 68%, rgba(10,11,13,0) 100%);"></div>
        <div style="position:absolute; bottom:0; left:0; right:0; height:480px; background:linear-gradient(to top, rgba(10,11,13,0.88) 0%, rgba(10,11,13,0.45) 55%, rgba(10,11,13,0) 100%);"></div>

        <!-- Upper Safe Zone Copy -->
        <div style="position:absolute; top:210px; left:64px; right:64px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <span class="pill mono" style="background:rgba(214,180,108,0.20); border:1.5px solid #E5C883; color:#E5C883;">TEXTILE DEEP-DIVE</span>
            <span class="pill mono" style="background:rgba(14,14,16,0.75); color:#F4EFE6;">320GSM SPEC</span>
          </div>

          <div style="font-size:48px; font-weight:900; line-height:1.12; color:#FFFFFF; text-shadow:0 4px 16px rgba(0,0,0,0.85); margin-bottom:18px;">
            No paid agency seeding.<br/><span style="color:#FF5500;">No PR gifting suites.</span>
          </div>

          <div style="background:rgba(14,14,16,0.76); border-left:5px solid #E5C883; border-radius:10px; padding:18px 22px; font-size:26px; line-height:1.38; color:#F4EFE6;">
            Just former college hooper <strong>Garrett James</strong> cold-DMing players with Japanese kimono silhouettes and <strong>320gsm cotton-lined mesh</strong>.
          </div>
        </div>

        <!-- Bottom subtle guide leaving room for Native IG Question Sticker -->
        <div style="position:absolute; bottom:185px; left:68px; right:68px; text-align:center;">
          <div class="mono" style="font-size:19px; font-weight:800; color:#E5C883; text-shadow:0 2px 10px rgba(0,0,0,0.9);">
            DROP YOUR FAVORITE INDIE LABEL IN THE QUESTION BOX &darr;
          </div>
        </div>
      </div>
    </body></html>"""
    render_html_to_png(html, overlay_png, tmp_dir, transparent=True)

    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(src_video),
        "-i", str(overlay_png),
        "-filter_complex", "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1[bg];[bg][1:v]overlay=0:0[vout]",
        "-map", "[vout]", "-map", "0:a:0",
        "-af", "aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=9",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
        str(out_mp4),
    ])
    print(f"Rendered Story Frame 2 -> {out_mp4}")
    return out_mp4


def build_frame_3(tmp_dir: Path) -> Path:
    slide8_png = RENDERS_DIR / "carousel" / "slide_08_directory_cta.png"
    ace_pip_video = RENDERS_DIR / "shot6_ace_locked.mp4"
    if not slide8_png.exists():
        sys.exit(f"Missing Carousel Slide 8: {slide8_png}")
    if not ace_pip_video.exists():
        sys.exit(f"Missing Shot 6 Ace video: {ace_pip_video}")

    bg_png = tmp_dir / "story_03_bg.png"
    ring_png = tmp_dir / "story_03_pip_ring.png"
    out_mp4 = STORIES_DIR / "story_03_conversion_0500pm.mp4"

    slide8_uri = img_data_uri(slide8_png)

    # Background canvas with Slide 8 showcase + top copy + lower-left space for native Feed Link Sticker
    html_bg = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON_CSS}</style></head>
    <body style="background:#0E0E10; color:#F4EFE6;">
      <div style="width:1080px; height:1920px; position:relative; background:radial-gradient(circle at 50% 45%, #23252A 0%, #0E0E10 75%); padding:205px 60px 180px 60px; display:flex; flex-direction:column;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
          <span class="pill mono" style="background:#FF5500; color:#FFFFFF;">DROP LIVE ON FEED</span>
          <span class="pill mono" style="background:rgba(214,180,108,0.16); border:1.5px solid #E5C883; color:#E5C883;">@DOCTORACEBOOGIE</span>
        </div>

        <div style="font-size:48px; font-weight:900; line-height:1.10; color:#FFFFFF; margin-bottom:14px;">
          The complete 2026 Athlete Indie Directory is live on the feed.
        </div>

        <div style="font-size:25px; line-height:1.36; color:rgba(244,239,230,0.86); margin-bottom:28px;">
          5 brands replacing corporate streetwear + the exact silhouette blueprint <strong style="color:#E5C883;">LeBron and SGA</strong> use.
        </div>

        <!-- Framed Preview of Carousel Slide 8 -->
        <div style="width:820px; height:960px; margin:0 auto; border-radius:18px; overflow:hidden; border:2px solid rgba(214,180,108,0.55); box-shadow:0 28px 65px rgba(0,0,0,0.72); position:relative;">
          <img src="{slide8_uri}" style="width:100%; height:100%; object-fit:cover; object-position:top center;" />
        </div>

        <!-- Lower-left cue leaving clean room for Native IG Feed Post Link Sticker (right side holds Ace PiP circle) -->
        <div style="position:absolute; left:64px; bottom:215px; width:560px;">
          <div style="background:rgba(255,85,0,0.18); border:1.5px solid #FF5500; border-radius:14px; padding:20px 24px;">
            <div class="mono" style="font-size:17px; font-weight:800; color:#FF5500; margin-bottom:8px;">TAP FEED LINK STICKER</div>
            <div style="font-size:27px; font-weight:800; color:#FFFFFF;">Tap to save the cheat sheet</div>
          </div>
        </div>
      </div>
    </body></html>"""
    render_html_to_png(html_bg, bg_png, tmp_dir, transparent=False)

    # Gold ring border overlay for the 360x360 circular Ace PiP at (x=665, y=1350)
    html_ring = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{COMMON_CSS}</style></head>
    <body style="background:transparent;">
      <div style="width:1080px; height:1920px; position:relative;">
        <div style="position:absolute; left:660px; top:1345px; width:370px; height:370px; border-radius:50%; border:6px solid #E5C883; box-shadow:0 16px 40px rgba(0,0,0,0.75);"></div>
        <div style="position:absolute; left:725px; top:1726px; width:240px; text-align:center; background:rgba(14,14,16,0.88); border:1px solid rgba(214,180,108,0.6); border-radius:999px; padding:6px 14px; font-size:17px; font-weight:800; color:#E5C883;" class="mono">ACE LIVE BRIEF</div>
      </div>
    </body></html>"""
    render_html_to_png(html_ring, ring_png, tmp_dir, transparent=True)

    # Composite circular Ace studio PiP (360x360 centered on Ace's head/shades/chains) onto Slide 8 background
    filter_complex = (
        "[1:v]fps=30,crop=680:680:20:140,scale=360:360,format=yuva420p,"
        "geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':"
        "a='if(lte(pow(X-180,2)+pow(Y-180,2),pow(178,2)),255,0)'[pip];"
        "[0:v][pip]overlay=665:1350:shortest=1[with_pip];"
        "[with_pip][2:v]overlay=0:0:shortest=1[vout]"
    )
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(bg_png),
        "-i", str(ace_pip_video),
        "-loop", "1", "-i", str(ring_png),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "1:a:0",
        "-af", "aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=9",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart",
        "-shortest",
        str(out_mp4),
    ])
    print(f"Rendered Story Frame 3 -> {out_mp4}")
    return out_mp4


def main() -> None:
    STORIES_DIR.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path("/tmp/ace_stories_build")
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        frame1_bg = ASSETS_DIR / "story-01-tunnel-contrast-bg.jpg"
        if frame1_bg.exists():
            build_frame_1(frame1_bg, tmp_dir)
        else:
            print(f"[Pending] Frame 1 background not yet saved at {frame1_bg}; skipping Frame 1 for now.")
        build_frame_2(tmp_dir)
        build_frame_3(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
