#!/usr/bin/env python3
"""
Ace Editorial 8-Slide Instagram Carousel Renderer (1080x1350, 4:5 Portrait)
Pilot 01: The Indie Streetwear Coup (Ryoko Rain & Athlete-Owned Indie Labels)

Renders 8 pixel-sharp editorial PNG slides via headless Chrome using Ace's
locked visual kit + exact copy/specs from `athlete-indie-labels-ryoko-rain-post.md`.
"""

from __future__ import annotations

import base64
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = WORKSPACE_DIR / "assets" / "ace-references"
OUT_DIR = WORKSPACE_DIR / "renders" / "ryoko-rain-indie-coup" / "carousel"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def img_data_uri(path: Path) -> str:
    if not path.exists():
        sys.exit(f"Missing required visual asset: {path}")
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    ext = path.suffix.lower().lstrip(".")
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    return f"data:image/{mime};base64,{b64}"


BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  width: 1080px;
  height: 1350px;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "SF Pro Display", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.slide {
  width: 1080px;
  height: 1350px;
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 58px 64px 52px 64px;
  overflow: hidden;
}
.dark { background: #141517; color: #F4EFE6; }
.parchment { background: #F4EFE6; color: #121315; }
.mono {
  font-family: "SF Mono", "Menlo", "Monaco", "Courier New", monospace;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 22px;
  border-bottom: 1.5px solid rgba(244, 239, 230, 0.16);
  margin-bottom: 32px;
  flex-shrink: 0;
}
.parchment .topbar { border-bottom-color: rgba(18, 19, 21, 0.16); }
.pill {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 19px;
  font-weight: 700;
  background: #FF5500;
  color: #FFFFFF;
}
.pill-gold {
  background: rgba(214, 180, 108, 0.16);
  border: 1.5px solid rgba(214, 180, 108, 0.65);
  color: #E5C883;
}
.pill-dark {
  background: #121315;
  color: #F4EFE6;
}
.slide-num {
  font-size: 20px;
  font-weight: 700;
  opacity: 0.72;
}
.footer {
  margin-top: auto;
  padding-top: 22px;
  border-top: 1.5px solid rgba(244, 239, 230, 0.16);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 19px;
  font-weight: 600;
  opacity: 0.78;
  flex-shrink: 0;
}
.parchment .footer { border-top-color: rgba(18, 19, 21, 0.16); }
.accent { color: #FF5500; }
.gold { color: #D6B46C; }
.h1 {
  font-size: 66px;
  font-weight: 900;
  line-height: 1.03;
  letter-spacing: -0.025em;
  text-transform: uppercase;
}
.h2 {
  font-size: 50px;
  font-weight: 900;
  line-height: 1.08;
  letter-spacing: -0.02em;
}
.sub {
  font-size: 26px;
  line-height: 1.38;
  font-weight: 400;
  opacity: 0.85;
}
"""


def build_slides() -> list[tuple[str, str]]:
    ace_portrait = img_data_uri(ASSETS_DIR / "ace-ryoko-shot1-fixed-keyframe.jpg")
    ace_fullbody = img_data_uri(ASSETS_DIR / "ace-ryoko-shot5-fixed-keyframe.jpg")
    ryoko_macro = img_data_uri(ASSETS_DIR / "ryoko-rain-kimono-macro.jpg")
    htg_flatlay = img_data_uri(ASSETS_DIR / "carousel-honor-the-gift.jpg")
    bode_flatlay = img_data_uri(ASSETS_DIR / "carousel-bode-heirloom.jpg")

    slides: list[tuple[str, str]] = []

    # SLIDE 1: Cover Hook
    s1 = f"""
    <div class="slide dark" style="padding:0; background:#0E0E10;">
      <div style="display:grid; grid-template-columns: 1fr 1fr; height: 750px; flex-shrink:0; position:relative; overflow:hidden;">
        <div style="position:relative; overflow:hidden; border-right:2px solid #0E0E10;">
          <img src="{ace_portrait}" style="width:100%; height:100%; object-fit:cover; object-position:center 18%;" />
          <div style="position:absolute; inset:0; background:linear-gradient(to bottom, rgba(14,14,16,0.25) 0%, rgba(14,14,16,0) 35%, rgba(14,14,16,0.92) 100%);"></div>
        </div>
        <div style="position:relative; overflow:hidden;">
          <img src="{ryoko_macro}" style="width:100%; height:100%; object-fit:cover; object-position:center center;" />
          <div style="position:absolute; inset:0; background:linear-gradient(to bottom, rgba(14,14,16,0.25) 0%, rgba(14,14,16,0) 35%, rgba(14,14,16,0.92) 100%);"></div>
        </div>
        <div style="position:absolute; top:44px; left:54px; right:54px; display:flex; justify-content:space-between; align-items:center;">
          <span class="pill pill-gold mono">ACE ARCHIVE REPORT // VOL. 14</span>
          <span class="pill mono" style="background:rgba(14,14,16,0.82); border:1px solid rgba(255,255,255,0.25);">01 / 08</span>
        </div>
      </div>

      <div style="flex:1; padding: 14px 62px 48px 62px; display:flex; flex-direction:column; justify-content:space-between;">
        <div>
          <div class="mono accent" style="font-size:21px; font-weight:800; margin-bottom:14px;">2026 NBA TUNNEL FORECAST // THE INDIE COUP</div>
          <div class="h1" style="font-size:62px; color:#F4EFE6; margin-bottom:20px;">WHY NBA STARS DITCHED LUXURY LOGOS FOR INDIE LABELS</div>
          <div class="sub" style="font-size:26px; color:rgba(244,239,230,0.82); max-width:920px;">
            The death of tunnel logomania — and the rise of athlete-owned cut-and-sew craft led by <strong style="color:#E5C883;">Ryoko Rain</strong>, <strong style="color:#E5C883;">Honor The Gift</strong>, and <strong style="color:#E5C883;">Bode</strong>.
          </div>
        </div>

        <div class="footer" style="border-top-color:rgba(244,239,230,0.18);">
          <span class="mono">@DOCTORACEBOOGIE</span>
          <span class="mono" style="color:#FF5500; font-weight:800;">SWIPE FOR THE 5-BRAND DIRECTORY &rarr;</span>
        </div>
      </div>
    </div>
    """
    slides.append(("slide_01_cover.png", s1))

    # SLIDE 2: The Macro Shift
    s2 = """
    <div class="slide parchment">
      <div class="topbar">
        <span class="pill pill-dark mono">01 // THE MACRO SHIFT</span>
        <span class="slide-num mono">02 / 08</span>
      </div>

      <div class="h2" style="font-size:56px; margin-bottom:28px; text-transform:uppercase; line-height:1.04;">
        THE CORPORATE TUNNEL <span class="accent">BURNOUT</span>
      </div>

      <div style="display:flex; flex-direction:column; gap:22px; margin-bottom:34px;">
        <div style="background:#FFFFFF; border:1.5px solid rgba(18,19,21,0.12); border-left:7px solid #121315; padding:24px 28px; border-radius:10px;">
          <div class="mono" style="font-size:17px; font-weight:800; color:#666; margin-bottom:8px;">EIGHT SEASONS OF AGENCY BILLBOARDS</div>
          <div style="font-size:25px; line-height:1.38; color:#18191C;">
            NBA pre-game tunnels operated as paid runway billboards for Paris and Milan conglomerates—outfitting athletes in <strong>$3,500 synthetic monograms</strong> cut for skinny catwalks, not athletic builds.
          </div>
        </div>

        <div style="background:#FFFFFF; border:1.5px solid rgba(18,19,21,0.12); border-left:7px solid #FF5500; padding:24px 28px; border-radius:10px;">
          <div class="mono accent" style="font-size:17px; font-weight:800; margin-bottom:8px;">THE 2026 BREAKING POINT</div>
          <div style="font-size:25px; line-height:1.38; color:#18191C;">
            Logomania hit peak fatigue. When anyone with a stylist contract gets loaned the same monogram tracksuit, <strong>the logo holds zero cultural weight</strong>.
          </div>
        </div>
      </div>

      <div style="background:#141517; color:#F4EFE6; border-radius:14px; padding:32px 34px; margin-bottom:26px;">
        <div class="mono gold" style="font-size:18px; font-weight:800; margin-bottom:22px;">THE STATUS SIGNAL FLIP // 2018 VS. 2026</div>
        <div style="display:grid; grid-template-columns: 1fr 70px 1fr; align-items:center; gap:10px;">
          <div style="background:rgba(255,255,255,0.06); padding:22px; border-radius:10px; border:1px solid rgba(255,255,255,0.12);">
            <div class="mono" style="font-size:26px; font-weight:900; color:#8A8F99; margin-bottom:8px;">2018 ERA</div>
            <div style="font-size:22px; line-height:1.35; color:#C4C8D0;">Peak monogram hype. Loud corporate chest logos. Agency-seeded PR loans.</div>
          </div>
          <div style="text-align:center; font-size:44px; font-weight:900; color:#FF5500;">&rarr;</div>
          <div style="background:rgba(255,85,0,0.12); padding:22px; border-radius:10px; border:1.5px solid #FF5500;">
            <div class="mono accent" style="font-size:26px; font-weight:900; margin-bottom:8px;">2026 ERA</div>
            <div style="font-size:22px; line-height:1.35; color:#F4EFE6;"><strong>Understated textile scarcity.</strong> Direct founder-to-athlete DMs. Heavyweight craft.</div>
          </div>
        </div>
      </div>

      <div style="border-left:5px solid #121315; padding:12px 22px; font-size:24px; font-weight:700; font-style:italic; color:#1E1F22;">
        &ldquo;Clout is rented; quality is owned. Status moved from how much you spent to who actually cut the pattern.&rdquo;
      </div>

      <div class="footer">
        <span class="mono">@DOCTORACEBOOGIE // ACE ARCHIVE</span>
        <span class="mono accent">01: RYOKO RAIN NEXT &rarr;</span>
      </div>
    </div>
    """
    slides.append(("slide_02_macro_shift.png", s2))

    # SLIDE 3: Spotlight 01 — Ryoko Rain
    s3 = f"""
    <div class="slide dark" style="padding:0;">
      <div style="height:540px; flex-shrink:0; position:relative; overflow:hidden;">
        <img src="{ryoko_macro}" style="width:100%; height:100%; object-fit:cover; object-position:center center;" />
        <div style="position:absolute; inset:0; background:linear-gradient(to bottom, rgba(20,21,23,0.4) 0%, rgba(20,21,23,0.05) 45%, rgba(20,21,23,1) 100%);"></div>
        <div style="position:absolute; top:44px; left:58px; right:58px; display:flex; justify-content:space-between; align-items:center;">
          <span class="pill mono">BRAND 01 // ORANGE COUNTY, CA</span>
          <span class="pill mono" style="background:rgba(14,14,16,0.82); border:1px solid rgba(255,255,255,0.22);">03 / 08</span>
        </div>
      </div>

      <div style="flex:1; padding:12px 62px 48px 62px; display:flex; flex-direction:column;">
        <div class="mono gold" style="font-size:20px; font-weight:800; margin-bottom:8px;">THE HOOPER&rsquo;S KIMONO // FOUNDED 2021</div>
        <div class="h2" style="font-size:56px; margin-bottom:20px; text-transform:uppercase;">RYOKO RAIN</div>
        <div style="font-size:24px; line-height:1.4; color:rgba(244,239,230,0.86); margin-bottom:26px;">
          Founded by former college hooper <strong>Garrett James</strong> and named after the middle names of his two daughters. Built purely through cold DMs and direct athlete relationships—<strong>zero PR agencies, zero paid seeding</strong>.
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-bottom:22px;">
          <div style="background:#1E1F22; border:1px solid rgba(244,239,230,0.12); border-radius:12px; padding:22px;">
            <div class="mono accent" style="font-size:17px; font-weight:800; margin-bottom:10px;">THE ATHLETE CO-SIGNS</div>
            <div style="font-size:21px; line-height:1.45; color:#E8E4DC;">
              &bull; <strong>LeBron James:</strong> Playoff shootarounds<br/>
              &bull; <strong>Jayson Tatum:</strong> Pre-game tunnel layers<br/>
              &bull; <strong>A&rsquo;ja Wilson:</strong> WNBA crossover<br/>
              &bull; <strong>Milestone:</strong> CourtSide Melbourne debut
            </div>
          </div>
          <div style="background:#1E1F22; border:1px solid rgba(244,239,230,0.12); border-radius:12px; padding:22px;">
            <div class="mono gold" style="font-size:17px; font-weight:800; margin-bottom:10px;">GARMENT ARCHITECTURE</div>
            <div style="font-size:21px; line-height:1.45; color:#E8E4DC;">
              &bull; <strong>Hero:</strong> Unlined Kimono Chore Overshirt<br/>
              &bull; <strong>Price:</strong> $165&ndash;$195<br/>
              &bull; <strong>Spec:</strong> 320gsm double-layer mesh shorts lined in 100% combed cotton jersey
            </div>
          </div>
        </div>

        <div class="footer">
          <span class="mono">@DOCTORACEBOOGIE // HEAVYWEIGHT SPEC</span>
          <span class="mono accent">02: HONOR THE GIFT &rarr;</span>
        </div>
      </div>
    </div>
    """
    slides.append(("slide_03_ryoko_rain.png", s3))

    # SLIDE 4: Spotlight 02 — Honor The Gift
    s4 = f"""
    <div class="slide dark" style="padding:0;">
      <div style="height:540px; flex-shrink:0; position:relative; overflow:hidden;">
        <img src="{htg_flatlay}" style="width:100%; height:100%; object-fit:cover; object-position:center 28%;" />
        <div style="position:absolute; inset:0; background:linear-gradient(to bottom, rgba(20,21,23,0.4) 0%, rgba(20,21,23,0.05) 45%, rgba(20,21,23,1) 100%);"></div>
        <div style="position:absolute; top:44px; left:58px; right:58px; display:flex; justify-content:space-between; align-items:center;">
          <span class="pill mono">BRAND 02 // LOS ANGELES, CA</span>
          <span class="pill mono" style="background:rgba(14,14,16,0.82); border:1px solid rgba(255,255,255,0.22);">04 / 08</span>
        </div>
      </div>

      <div style="flex:1; padding:12px 62px 48px 62px; display:flex; flex-direction:column;">
        <div class="mono gold" style="font-size:20px; font-weight:800; margin-bottom:8px;">INNER-CITY RAW WORKWEAR // FOUNDED 2016</div>
        <div class="h2" style="font-size:56px; margin-bottom:20px; text-transform:uppercase;">HONOR THE GIFT</div>
        <div style="font-size:24px; line-height:1.4; color:rgba(244,239,230,0.86); margin-bottom:26px;">
          Founded by 9-time NBA All-Star <strong>Russell Westbrook</strong>. Rather than cash-grab celebrity licensing, Westbrook hired experienced denim patternmakers to engineer <strong>boxy torso crops that never pull at broad athletic lats</strong>.
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-bottom:22px;">
          <div style="background:#1E1F22; border:1px solid rgba(244,239,230,0.12); border-radius:12px; padding:22px;">
            <div class="mono accent" style="font-size:17px; font-weight:800; margin-bottom:10px;">HERO PIECES &amp; PRICING</div>
            <div style="font-size:21px; line-height:1.45; color:#E8E4DC;">
              &bull; Raw Duck Canvas Mechanics Jacket (<strong>$140&ndash;$180</strong>)<br/>
              &bull; Heavyweight French Terry Hoodie (<strong>$110&ndash;$160</strong>)<br/>
              &bull; Double-Knee Wide Work Trousers
            </div>
          </div>
          <div style="background:#1E1F22; border:1px solid rgba(244,239,230,0.12); border-radius:12px; padding:22px;">
            <div class="mono gold" style="font-size:17px; font-weight:800; margin-bottom:10px;">TEXTILE SPECS</div>
            <div style="font-size:21px; line-height:1.45; color:#E8E4DC;">
              &bull; <strong>400&ndash;460gsm</strong> custom-milled French terry<br/>
              &bull; Distressed raw <strong>12oz duck canvas</strong><br/>
              &bull; Built to patina across years of real daily wear
            </div>
          </div>
        </div>

        <div class="footer">
          <span class="mono">@DOCTORACEBOOGIE // HEAVYWEIGHT SPEC</span>
          <span class="mono accent">03: BODE HEIRLOOM &rarr;</span>
        </div>
      </div>
    </div>
    """
    slides.append(("slide_04_honor_the_gift.png", s4))

    # SLIDE 5: Spotlight 03 — Bode
    s5 = f"""
    <div class="slide dark" style="padding:0;">
      <div style="height:540px; flex-shrink:0; position:relative; overflow:hidden;">
        <img src="{bode_flatlay}" style="width:100%; height:100%; object-fit:cover; object-position:center 35%;" />
        <div style="position:absolute; inset:0; background:linear-gradient(to bottom, rgba(20,21,23,0.4) 0%, rgba(20,21,23,0.05) 45%, rgba(20,21,23,1) 100%);"></div>
        <div style="position:absolute; top:44px; left:58px; right:58px; display:flex; justify-content:space-between; align-items:center;">
          <span class="pill mono">BRAND 03 // NEW YORK, NY</span>
          <span class="pill mono" style="background:rgba(14,14,16,0.82); border:1px solid rgba(255,255,255,0.22);">05 / 08</span>
        </div>
      </div>

      <div style="flex:1; padding:12px 62px 48px 62px; display:flex; flex-direction:column;">
        <div class="mono gold" style="font-size:20px; font-weight:800; margin-bottom:8px;">HEIRLOOM AMERICANA // ANTIQUE TEXTILES</div>
        <div class="h2" style="font-size:56px; margin-bottom:20px; text-transform:uppercase;">BODE</div>
        <div style="font-size:24px; line-height:1.4; color:rgba(244,239,230,0.86); margin-bottom:26px;">
          Founded by CFDA Menswear Designer of the Year <strong>Emily Adams Bode Aujla</strong>. Sourced from deadstock antique quilts and 19th-century domestic linens—championed by <strong>Shai Gilgeous-Alexander (SGA)</strong> to dismantle aggressive logo culture.
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:18px; margin-bottom:22px;">
          <div style="background:#1E1F22; border:1px solid rgba(244,239,230,0.12); border-radius:12px; padding:22px;">
            <div class="mono accent" style="font-size:17px; font-weight:800; margin-bottom:10px;">HERO PIECES &amp; PRICING</div>
            <div style="font-size:21px; line-height:1.45; color:#E8E4DC;">
              &bull; 1-of-1 Antique Quilt Jacket (<strong>$900&ndash;$1,600</strong>)<br/>
              &bull; Hand-Crocheted Linen Cabana (<strong>$450&ndash;$650</strong>)<br/>
              &bull; True archival scarcity—no two pieces identical
            </div>
          </div>
          <div style="background:#1E1F22; border:1px solid rgba(244,239,230,0.12); border-radius:12px; padding:22px;">
            <div class="mono gold" style="font-size:17px; font-weight:800; margin-bottom:10px;">CULTURAL IMPACT</div>
            <div style="font-size:21px; line-height:1.45; color:#E8E4DC;">
              &bull; Pre-1950s hand-embroidered textiles<br/>
              &bull; Boxy cropped hems + single-needle finishing<br/>
              &bull; Proved delicate drape beats loud hype logos
            </div>
          </div>
        </div>

        <div class="footer">
          <span class="mono">@DOCTORACEBOOGIE // ARCHIVAL LINEAGE</span>
          <span class="mono accent">CRAFT VS. CORPORATE &rarr;</span>
        </div>
      </div>
    </div>
    """
    slides.append(("slide_05_bode.png", s5))

    # SLIDE 6: The Contrast Table
    s6 = """
    <div class="slide parchment">
      <div class="topbar">
        <span class="pill pill-dark mono">04 // QUALITY BREAKDOWN</span>
        <span class="slide-num mono">06 / 08</span>
      </div>

      <div class="h2" style="font-size:48px; margin-bottom:14px; text-transform:uppercase; line-height:1.06;">
        CUT-AND-SEW CRAFT <span class="accent">VS.</span> CORPORATE SPONSORS
      </div>
      <div class="sub" style="font-size:23px; margin-bottom:28px; color:#3A3D42;">
        How to spot real garment architecture versus single-use PR placement.
      </div>

      <table style="width:100%; border-collapse:separate; border-spacing:0 12px; font-size:21px;">
        <thead>
          <tr>
            <th class="mono" style="text-align:left; padding:12px 16px; font-size:16px; color:#666; width:22%;">DIMENSION</th>
            <th class="mono" style="text-align:left; padding:14px 20px; font-size:16px; background:#141517; color:#E5C883; border-radius:8px 0 0 8px; width:40%;">GRASSROOTS INDIE (RYOKO / HTG)</th>
            <th class="mono" style="text-align:left; padding:14px 20px; font-size:16px; background:#DFD9CE; color:#4A4C50; border-radius:0 8px 8px 0; width:38%;">CORPORATE FAST FASHION</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td class="mono" style="font-weight:800; font-size:17px; padding:16px; color:#121315;">MATERIAL</td>
            <td style="background:#FFFFFF; padding:18px 20px; border-left:5px solid #2D6A4F; font-weight:600; border-radius:8px 0 0 8px; line-height:1.32;">320&ndash;450gsm slub cotton, Japanese canvas, cotton-lined mesh</td>
            <td style="background:#EAE4D9; padding:18px 20px; color:#4E5156; border-radius:0 8px 8px 0; line-height:1.32;">Virgin polyester, thin nylon blends, synthetic fleece</td>
          </tr>
          <tr>
            <td class="mono" style="font-weight:800; font-size:17px; padding:16px; color:#121315;">SILHOUETTE</td>
            <td style="background:#FFFFFF; padding:18px 20px; border-left:5px solid #2D6A4F; font-weight:600; border-radius:8px 0 0 8px; line-height:1.32;">Boxy 24&ndash;26&quot; crop, dropped shoulders, zero lat-tugging</td>
            <td style="background:#EAE4D9; padding:18px 20px; color:#4E5156; border-radius:0 8px 8px 0; line-height:1.32;">Narrow off-the-rack tube cuts that pull across shoulders</td>
          </tr>
          <tr>
            <td class="mono" style="font-weight:800; font-size:17px; padding:16px; color:#121315;">BRANDING</td>
            <td style="background:#FFFFFF; padding:18px 20px; border-left:5px solid #2D6A4F; font-weight:600; border-radius:8px 0 0 8px; line-height:1.32;">Blind debossing, tone-on-tone stitch, zero loud logos</td>
            <td style="background:#EAE4D9; padding:18px 20px; color:#4E5156; border-radius:0 8px 8px 0; line-height:1.32;">Oversized plastisol chest prints &amp; rubber badges</td>
          </tr>
          <tr>
            <td class="mono" style="font-weight:800; font-size:17px; padding:16px; color:#121315;">SEEDING</td>
            <td style="background:#FFFFFF; padding:18px 20px; border-left:5px solid #2D6A4F; font-weight:600; border-radius:8px 0 0 8px; line-height:1.32;">Direct founder-to-athlete DMs, small-batch drops</td>
            <td style="background:#EAE4D9; padding:18px 20px; color:#4E5156; border-radius:0 8px 8px 0; line-height:1.32;">Agency sponsorship contracts &amp; PR gifting suites</td>
          </tr>
          <tr>
            <td class="mono" style="font-weight:800; font-size:17px; padding:16px; color:#121315;">LIFESPAN</td>
            <td style="background:#FFFFFF; padding:18px 20px; border-left:5px solid #2D6A4F; font-weight:600; border-radius:8px 0 0 8px; line-height:1.32;">Heirloom keeper piece worn across multiple seasons</td>
            <td style="background:#EAE4D9; padding:18px 20px; color:#4E5156; border-radius:0 8px 8px 0; line-height:1.32;">Single-use tunnel photo-op, discarded after 1 wear</td>
          </tr>
        </tbody>
      </table>

      <div class="footer">
        <span class="mono">@DOCTORACEBOOGIE // TEXTILE AUDIT</span>
        <span class="mono accent">THE 4 SILHOUETTE RULES &rarr;</span>
      </div>
    </div>
    """
    slides.append(("slide_06_contrast_table.png", s6))

    # SLIDE 7: Silhouette Cheat Sheet with Locked Full-Body Ace + SVG Blueprint Callouts
    s7 = f"""
    <div class="slide dark">
      <div class="topbar">
        <span class="pill pill-gold mono">05 // SILHOUETTE BLUEPRINT</span>
        <span class="slide-num mono">07 / 08</span>
      </div>

      <div class="h2" style="font-size:48px; margin-bottom:26px; text-transform:uppercase;">
        THE 2026 TUNNEL <span class="accent">PROPORTION</span> RULES
      </div>

      <div style="display:grid; grid-template-columns: 430px 1fr; gap:30px; flex:1; align-items:stretch;">
        <div style="position:relative; border-radius:14px; overflow:hidden; border:1.5px solid rgba(214,180,108,0.45); background:#0E0E10;">
          <img src="{ace_fullbody}" style="width:100%; height:100%; object-fit:cover; object-position:center 58%;" />
          <!-- Architectural proportion overlay SVG -->
          <svg viewBox="0 0 430 960" style="position:absolute; inset:0; width:100%; height:100%;">
            <!-- 1/3 Torso Crop Bracket (aligned to Ace's olive kimono shoulder-to-hem) -->
            <line x1="26" y1="395" x2="26" y2="578" stroke="#FF5500" stroke-width="3.5" />
            <line x1="18" y1="395" x2="44" y2="395" stroke="#FF5500" stroke-width="3.5" />
            <line x1="18" y1="578" x2="44" y2="578" stroke="#FF5500" stroke-width="3.5" />
            <rect x="38" y="458" width="168" height="58" rx="6" fill="rgba(14,14,16,0.90)" stroke="#FF5500" stroke-width="1.5" />
            <text x="50" y="482" fill="#FF5500" font-family="SF Mono, Menlo, monospace" font-size="14" font-weight="800">1/3 CROP</text>
            <text x="50" y="504" fill="#F4EFE6" font-family="Helvetica Neue, Arial, sans-serif" font-size="17" font-weight="800">24.5&quot;&ndash;26.5&quot; BODY</text>

            <!-- 2/3 Leg / 9.5 Hem Bracket (aligned to waist-to-sneaker break) -->
            <line x1="26" y1="594" x2="26" y2="878" stroke="#E5C883" stroke-width="3.5" />
            <line x1="18" y1="594" x2="44" y2="594" stroke="#E5C883" stroke-width="3.5" />
            <line x1="18" y1="878" x2="44" y2="878" stroke="#E5C883" stroke-width="3.5" />
            <rect x="38" y="790" width="196" height="58" rx="6" fill="rgba(14,14,16,0.90)" stroke="#E5C883" stroke-width="1.5" />
            <text x="50" y="814" fill="#E5C883" font-family="SF Mono, Menlo, monospace" font-size="14" font-weight="800">2/3 DRAPE</text>
            <text x="50" y="836" fill="#F4EFE6" font-family="Helvetica Neue, Arial, sans-serif" font-size="17" font-weight="800">9.5&quot;&ndash;10.5&quot; HEM</text>
          </svg>
        </div>

        <div style="display:flex; flex-direction:column; justify-content:space-between; gap:16px;">
          <div style="background:#1E1F22; border:1px solid rgba(244,239,230,0.12); border-left:5px solid #FF5500; border-radius:10px; padding:20px 22px;">
            <div class="mono accent" style="font-size:16px; font-weight:800; margin-bottom:6px;">RULE 01 // 1:1.6 CROPPED RATIO</div>
            <div style="font-size:21px; line-height:1.35; color:#EAE6DE;">Keep overshirts &amp; jackets between <strong>24.5&quot; and 26.5&quot;</strong>—ending cleanly at the hip bone to elongate your leg line.</div>
          </div>

          <div style="background:#1E1F22; border:1px solid rgba(244,239,230,0.12); border-left:5px solid #D6B46C; border-radius:10px; padding:20px 22px;">
            <div class="mono gold" style="font-size:16px; font-weight:800; margin-bottom:6px;">RULE 02 // DROP-SHOULDER ROOM</div>
            <div style="font-size:21px; line-height:1.35; color:#EAE6DE;">Skip tight set-in sleeves. <strong>Kimono collars &amp; drop shoulders</strong> eliminate chest-pulling on athletic frames.</div>
          </div>

          <div style="background:#1E1F22; border:1px solid rgba(244,239,230,0.12); border-left:5px solid #FF5500; border-radius:10px; padding:20px 22px;">
            <div class="mono accent" style="font-size:16px; font-weight:800; margin-bottom:6px;">RULE 03 // 9.5&quot; HEM POOL</div>
            <div style="font-size:21px; line-height:1.35; color:#EAE6DE;">Retire tapered jeans. Run a <strong>9.5&quot;&ndash;10.5&quot; leg opening</strong> so denim pools cleanly over low-profile sneakers.</div>
          </div>

          <div style="background:#1E1F22; border:1px solid rgba(244,239,230,0.12); border-left:5px solid #D6B46C; border-radius:10px; padding:20px 22px;">
            <div class="mono gold" style="font-size:16px; font-weight:800; margin-bottom:6px;">RULE 04 // TWO HEAVY LAYERS</div>
            <div style="font-size:21px; line-height:1.35; color:#EAE6DE;">A <strong>300gsm boxy mock-neck tee</strong> under an unlined <strong>400gsm overshirt</strong> builds structure without bulk.</div>
          </div>
        </div>
      </div>

      <div class="footer">
        <span class="mono">@DOCTORACEBOOGIE // PROPORTION &gt; PRICE TAG</span>
        <span class="mono accent">5-BRAND DIRECTORY NEXT &rarr;</span>
      </div>
    </div>
    """
    slides.append(("slide_07_silhouette_rules.png", s7))

    # SLIDE 8: The 5-Brand Directory Matrix & Save Trigger
    s8 = """
    <div class="slide dark">
      <div class="topbar">
        <span class="pill mono">06 // SAVE THIS CHEAT SHEET</span>
        <span class="slide-num mono">08 / 08</span>
      </div>

      <div class="h2" style="font-size:48px; margin-bottom:10px; text-transform:uppercase;">
        THE 2026 ATHLETE <span class="gold">INDIE DIRECTORY</span>
      </div>
      <div class="sub" style="font-size:22px; margin-bottom:24px; color:rgba(244,239,230,0.78);">
        Five grassroots labels replacing corporate streetwear in NBA &amp; WNBA tunnels.
      </div>

      <table style="width:100%; border-collapse:separate; border-spacing:0 11px; font-size:20px; margin-bottom:24px;">
        <thead>
          <tr>
            <th class="mono" style="text-align:left; padding:10px 16px; font-size:15px; color:#9BA0A8;">BRAND</th>
            <th class="mono" style="text-align:left; padding:10px 14px; font-size:15px; color:#9BA0A8;">FOUNDER / CITY</th>
            <th class="mono" style="text-align:left; padding:10px 14px; font-size:15px; color:#9BA0A8;">HERO GARMENT</th>
            <th class="mono" style="text-align:right; padding:10px 16px; font-size:15px; color:#E5C883;">ENTRY</th>
          </tr>
        </thead>
        <tbody>
          <tr style="background:#1E1F22;">
            <td style="padding:18px 16px; font-weight:800; color:#FF5500; border-left:4px solid #FF5500; border-radius:8px 0 0 8px;">Ryoko Rain</td>
            <td style="padding:18px 14px; color:#DCD8D0;">Garrett James (OC, CA)</td>
            <td style="padding:18px 14px; color:#F4EFE6; font-weight:600;">Kimono Chore Jacket</td>
            <td class="mono" style="padding:18px 16px; text-align:right; color:#E5C883; font-weight:800; border-radius:0 8px 8px 0;">$145&ndash;$195</td>
          </tr>
          <tr style="background:#1E1F22;">
            <td style="padding:18px 16px; font-weight:800; color:#F4EFE6; border-left:4px solid #D6B46C; border-radius:8px 0 0 8px;">Honor The Gift</td>
            <td style="padding:18px 14px; color:#DCD8D0;">Russell Westbrook (LA)</td>
            <td style="padding:18px 14px; color:#F4EFE6; font-weight:600;">460gsm Terry Hoodie</td>
            <td class="mono" style="padding:18px 16px; text-align:right; color:#E5C883; font-weight:800; border-radius:0 8px 8px 0;">$110&ndash;$160</td>
          </tr>
          <tr style="background:#1E1F22;">
            <td style="padding:18px 16px; font-weight:800; color:#F4EFE6; border-left:4px solid #D6B46C; border-radius:8px 0 0 8px;">Bode</td>
            <td style="padding:18px 14px; color:#DCD8D0;">Emily Adams Bode (NYC)</td>
            <td style="padding:18px 14px; color:#F4EFE6; font-weight:600;">Crochet Linen Cabana</td>
            <td class="mono" style="padding:18px 16px; text-align:right; color:#E5C883; font-weight:800; border-radius:0 8px 8px 0;">$450&ndash;$950</td>
          </tr>
          <tr style="background:#1E1F22;">
            <td style="padding:18px 16px; font-weight:800; color:#F4EFE6; border-left:4px solid #D6B46C; border-radius:8px 0 0 8px;">Madhappy</td>
            <td style="padding:18px 14px; color:#DCD8D0;">Peiman / Rafelson (LA)</td>
            <td style="padding:18px 14px; color:#F4EFE6; font-weight:600;">Local Optimist Crew</td>
            <td class="mono" style="padding:18px 16px; text-align:right; color:#E5C883; font-weight:800; border-radius:0 8px 8px 0;">$140&ndash;$185</td>
          </tr>
          <tr style="background:#1E1F22;">
            <td style="padding:18px 16px; font-weight:800; color:#F4EFE6; border-left:4px solid #D6B46C; border-radius:8px 0 0 8px;">Bristol Studio</td>
            <td style="padding:18px 14px; color:#DCD8D0;">Luke Tadashi (LA)</td>
            <td style="padding:18px 14px; color:#F4EFE6; font-weight:600;">Reversible Warm-Up</td>
            <td class="mono" style="padding:18px 16px; text-align:right; color:#E5C883; font-weight:800; border-radius:0 8px 8px 0;">$165&ndash;$240</td>
          </tr>
        </tbody>
      </table>

      <div style="background:linear-gradient(135deg, rgba(255,85,0,0.18), rgba(214,180,108,0.14)); border:1.5px solid #FF5500; border-radius:14px; padding:26px 30px;">
        <div class="mono accent" style="font-size:18px; font-weight:800; margin-bottom:10px;">SAVE &amp; JOIN THE DEBATE</div>
        <div style="font-size:24px; line-height:1.38; color:#F4EFE6; margin-bottom:10px;">
          <strong>Bookmark this directory</strong> for your next rotation refresh, then drop your pick in the comments:
        </div>
        <div style="font-size:23px; font-weight:700; color:#E5C883;">
          Devin Booker&rsquo;s raw Americana workwear OR Shai&rsquo;s cropped artisanal drape?
        </div>
      </div>

      <div class="footer">
        <span class="mono">@DOCTORACEBOOGIE // WEEKLY ARCHIVE</span>
        <span class="mono gold">CLOUT IS RENTED; QUALITY IS OWNED</span>
      </div>
    </div>
    """
    slides.append(("slide_08_directory_cta.png", s8))

    return slides


def render_all() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path("/tmp/ace_carousel_build")
    chrome_profile = tmp_dir / "chrome_profile"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    chrome_profile.mkdir(parents=True, exist_ok=True)

    try:
        for fname, body_html in build_slides():
            html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{BASE_CSS}</style></head><body>{body_html}</body></html>"
            html_path = tmp_dir / f"{Path(fname).stem}.html"
            html_path.write_text(html, encoding="utf-8")
            png_path = OUT_DIR / fname
            raw_png = tmp_dir / f"raw_{fname}"
            cmd = [
                CHROME_BIN,
                "--headless=new",
                f"--user-data-dir={chrome_profile}",
                "--disable-gpu",
                "--no-sandbox",
                "--hide-scrollbars",
                "--window-size=1080,1450",
                "--force-device-scale-factor=1",
                f"--screenshot={raw_png}",
                f"file://{html_path}",
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0 or not raw_png.exists():
                sys.exit(f"Failed rendering {fname}:\n{res.stderr}")
            # Crop exact 1080x1350 from top-left (eliminates macOS headless Chrome 28px titlebar wrap)
            res_crop = subprocess.run(
                ["/opt/homebrew/bin/ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-i", str(raw_png), "-vf", "crop=1080:1350:0:0", str(png_path)],
                capture_output=True, text=True,
            )
            if res_crop.returncode != 0 or not png_path.exists():
                sys.exit(f"Failed cropping {fname}:\n{res_crop.stderr}")
            print(f"Rendered {png_path.name} ({png_path.stat().st_size // 1024} KB)")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    render_all()
