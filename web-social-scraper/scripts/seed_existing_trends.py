#!/usr/bin/env python3
"""Seed research database with existing briefings and scraped trends."""

from pathlib import Path
import re
import sys

from research_db import get_connection, insert_research_item, save_source_material

DB_PATH = Path("content-marketing-workspace/research.db")
TRENDS_DIR = Path("content-marketing-workspace/scraped-trends")


def seed_markdown_trends():
    conn = get_connection(DB_PATH)
    count = 0

    # 1. Parse nba-tunnel-fashion.md
    fashion_file = TRENDS_DIR / "nba-tunnel-fashion.md"
    if fashion_file.exists():
        content = fashion_file.read_text(encoding="utf-8")
        # Extract news items: ### [Title](URL)\n*Source | Date*\n> Snippet
        pattern = re.compile(
            r"###\s*\[(.*?)\]\((.*?)\)\s*\n\*(.*?)\s*\|\s*(.*?)\*\s*\n>\s*(.*?)(?=\n###|\Z)",
            re.DOTALL,
        )
        for match in pattern.finditer(content):
            title = match.group(1).strip()
            url = match.group(2).strip()
            source = match.group(3).strip()
            date_str = match.group(4).strip()
            snippet = match.group(5).strip()

            item = {
                "platform": "news_rss",
                "title": title,
                "author": source,
                "source_url": url,
                "snippet": snippet,
                "content": f"{title} ({source}) - {snippet}",
                "date": date_str,
                "score": 100,
            }
            if insert_research_item(conn, item, query="NBA tunnel fashion streetwear"):
                count += 1
                save_source_material(
                    conn,
                    source_url=url,
                    title=title,
                    content_type="news_article",
                    content=snippet,
                )

    # 2. Parse nba-tunnel-intelligence-briefing.md
    briefing_file = TRENDS_DIR / "nba-tunnel-intelligence-briefing.md"
    if briefing_file.exists():
        text = briefing_file.read_text(encoding="utf-8")
        # Ingest key sections
        sections = [
            (
                "The SGA vs. Devin Booker Divide & Tunnel Proportions",
                "https://reddit.com/r/ThrowingFits/comments/tunnel_proportions_sga_booker",
                "reddit",
                "r/ThrowingFits",
                "Shai Gilgeous-Alexander wins over high-fashion heads for drape and cropped-top/wide-bottom proportions (Loewe, Bode, Converse SHAI 001 in Butter/Steel). Devin Booker is favored for vintage Americana, 12oz duck canvas Detroit chore coats, and vintage 501s.",
            ),
            (
                "Sneaker Verdict: Converse SHAI 001 vs Nike Book 1 vs Adidas AE 1",
                "https://reddit.com/r/Sneakers/comments/bball_shoes_streetwear_styling",
                "reddit",
                "r/Sneakers",
                "Converse SHAI 001 (Butter/Steel) has puffed sculpted zipper shroud, styled with wide pleated trousers. Nike Book 1 looks like classic lifestyle low-top with vintage 501s. Adidas AE 1 has honeycomb TPU wing.",
            ),
            (
                "Ryoko Rain: Athlete-Favorite Indie Label",
                "https://timesofindia.indiatimes.com/sports/nba/lebron-tatum-ryoko-rain-debut",
                "news_rss",
                "The Times of India",
                "LeBron James and Jayson Tatum champion indie label Ryoko Rain, pushing kimono cuts, textured artisanal layers, and court-to-street crossovers.",
            ),
        ]
        for title, url, platform, author, snippet in sections:
            item = {
                "platform": platform,
                "title": title,
                "author": author,
                "source_url": url,
                "snippet": snippet,
                "content": snippet,
                "score": 250,
            }
            if insert_research_item(conn, item, query="NBA tunnel fashion streetwear"):
                count += 1
                save_source_material(
                    conn,
                    source_url=url,
                    title=title,
                    content_type="briefing_summary",
                    content=snippet,
                )

    print(f"Seeded {count} research items and source URLs into {DB_PATH}")


if __name__ == "__main__":
    seed_markdown_trends()
