# Prompt Production

Collaborative AI content production, social trend scraping, and Google Flow video script workspace built for **Google Antigravity**.

---

## Repository Structure

```text
prompt-production/
├── README.md                                           # Project overview & collaboration guide
├── .agents/                                            # Root Antigravity customizations (auto-loaded)
│   ├── rules/
│   │   └── AGENTS.md                                   # Synthesis & source citation rules
│   └── skills/
│       ├── content-marketer/SKILL.md                   # Content marketing & omnichannel distribution skill
│       └── web-social-scraper/SKILL.md                 # 4-step web & social trend scraping workflow
│
├── content-marketing-workspace/                        # Ace Content Strategy & Production Hub
│   ├── ace-ig-tiktok-campaign.md                       # 4-week Instagram & TikTok growth playbook for Ace
│   ├── week1-nba-tunnel-scripts-google-flow.md         # Word-for-word Week 1 scripts & Google Flow prompts
│   └── scraped-trends/                                 # Shared trend intelligence folder
│       ├── nba-tunnel-fashion.md                       # Raw multi-platform scraper output
│       └── nba-tunnel-intelligence-briefing.md         # Synthesized subreddit & fashion media briefing
│
└── web-social-scraper/                                 # Multi-Platform Scraping Engine
    ├── README.md                                       # Scraper documentation & architecture
    └── scripts/
        └── scrape_sources.py                           # Zero-dependency Python 3 scraper CLI
```

---

## Quick Start for Collaborators

1. **Clone the repository:**
   ```bash
   git clone https://github.com/davinciking/prompt-production.git
   cd prompt-production
   ```
2. **Open in Google Antigravity:**
   Set the root `prompt-production` folder (or `content-marketing-workspace`) as your active workspace. Antigravity will automatically discover the `content-marketer` and `web-social-scraper` skills inside `.agents/skills/`.
3. **Run a live trend scrape into `scraped-trends/`:**
   ```bash
   python3 web-social-scraper/scripts/scrape_sources.py \
     --query "NBA tunnel fashion streetwear" \
     --platforms reddit bluesky mastodon news \
     --limit 10 \
     --format markdown \
     --out content-marketing-workspace/scraped-trends/latest-trends.md
   ```
