#!/usr/bin/env python3
"""SQLite-backed Research Database & Retrieval Module.

Stores structured scraped research, social posts, news articles, and community discussions.
Provides Full-Text Search (FTS5), source URL persistence, and live source URL fetching
for Retrieval-Augmented Generation (RAG) agents.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import urllib.parse

DEFAULT_DB_PATH = Path("content-marketing-workspace/research.db")


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Connect to SQLite and ensure schema & FTS5 indexes are initialized."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def init_schema(conn: sqlite3.Connection):
    """Create normalized tables and FTS5 search indexes."""
    with conn:
        # 1. Main research items (posts, articles, discussions)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS research_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                platform TEXT NOT NULL,
                title TEXT,
                author TEXT,
                source_url TEXT UNIQUE NOT NULL,
                external_url TEXT,
                snippet TEXT,
                full_content TEXT,
                score INTEGER DEFAULT 0,
                num_comments INTEGER DEFAULT 0,
                raw_json TEXT,
                created_date TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 2. Source materials table (full-text cached articles & discussion trees from source URLs)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS source_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_url TEXT UNIQUE NOT NULL,
                title TEXT,
                content_type TEXT,
                content TEXT,
                outbound_links TEXT,
                images TEXT,
                raw_json TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # Backward-compatible migration: add images column if missing on existing DB
        existing_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(source_materials)").fetchall()
        }
        if "images" not in existing_cols:
            conn.execute("ALTER TABLE source_materials ADD COLUMN images TEXT")

        # 3. FTS5 Virtual Table for full-text keyword & phrase search
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS research_items_fts USING fts5(
                title,
                snippet,
                full_content,
                platform,
                query,
                content='research_items',
                content_rowid='id'
            );
            """
        )

        # 4. Triggers to keep research_items_fts in sync
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS research_items_ai AFTER INSERT ON research_items BEGIN
                INSERT INTO research_items_fts(rowid, title, snippet, full_content, platform, query)
                VALUES (new.id, new.title, new.snippet, new.full_content, new.platform, new.query);
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS research_items_ad AFTER DELETE ON research_items BEGIN
                INSERT INTO research_items_fts(research_items_fts, rowid, title, snippet, full_content, platform, query)
                VALUES ('delete', old.id, old.title, old.snippet, old.full_content, old.platform, old.query);
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS research_items_au AFTER UPDATE ON research_items BEGIN
                INSERT INTO research_items_fts(research_items_fts, rowid, title, snippet, full_content, platform, query)
                VALUES ('delete', old.id, old.title, old.snippet, old.full_content, old.platform, old.query);
                INSERT INTO research_items_fts(rowid, title, snippet, full_content, platform, query)
                VALUES (new.id, new.title, new.snippet, new.full_content, new.platform, new.query);
            END;
            """
        )

        # 5. FTS5 Virtual Table for source materials
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS source_materials_fts USING fts5(
                title,
                content,
                content='source_materials',
                content_rowid='id'
            );
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS source_materials_ai AFTER INSERT ON source_materials BEGIN
                INSERT INTO source_materials_fts(rowid, title, content)
                VALUES (new.id, new.title, new.content);
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS source_materials_ad AFTER DELETE ON source_materials BEGIN
                INSERT INTO source_materials_fts(source_materials_fts, rowid, title, content)
                VALUES ('delete', old.id, old.title, old.content);
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS source_materials_au AFTER UPDATE ON source_materials BEGIN
                INSERT INTO source_materials_fts(source_materials_fts, rowid, title, content)
                VALUES ('delete', old.id, old.title, old.content);
                INSERT INTO source_materials_fts(rowid, title, content)
                VALUES (new.id, new.title, new.content);
            END;
            """
        )


def insert_research_item(conn: sqlite3.Connection, item: dict, query: str = "") -> bool:
    """Insert or update a research item. Returns True if inserted/updated."""
    source_url = item.get("url") or item.get("source_url") or item.get("external_url")
    if not source_url:
        return False

    platform = item.get("platform") or "web"
    title = item.get("title") or ""
    author = item.get("author") or item.get("source") or ""
    external_url = item.get("external_url") or ""
    snippet = item.get("snippet") or item.get("description") or item.get("selftext") or ""
    full_content = item.get("content") or item.get("body") or item.get("selftext") or ""
    score = int(item.get("score") or item.get("likes") or item.get("points") or 0)
    num_comments = int(item.get("num_comments") or item.get("replies") or 0)
    created_date = item.get("date") or item.get("created_at") or ""
    raw_json = json.dumps(item, ensure_ascii=False)

    with conn:
        conn.execute(
            """
            INSERT INTO research_items (
                query, platform, title, author, source_url, external_url,
                snippet, full_content, score, num_comments, raw_json, created_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_url) DO UPDATE SET
                query=coalesce(nullif(excluded.query, ''), research_items.query),
                title=coalesce(nullif(excluded.title, ''), research_items.title),
                snippet=coalesce(nullif(excluded.snippet, ''), research_items.snippet),
                full_content=coalesce(nullif(excluded.full_content, ''), research_items.full_content),
                score=max(excluded.score, research_items.score),
                num_comments=max(excluded.num_comments, research_items.num_comments),
                raw_json=excluded.raw_json,
                scraped_at=CURRENT_TIMESTAMP;
            """,
            (
                query,
                platform,
                title,
                author,
                source_url,
                external_url,
                snippet,
                full_content,
                score,
                num_comments,
                raw_json,
                created_date,
            ),
        )
    return True


def save_source_material(
    conn: sqlite3.Connection,
    source_url: str,
    title: str = "",
    content_type: str = "webpage",
    content: str = "",
    outbound_links: list = None,
    images: list = None,
    raw_data: dict = None,
):
    """Save full-text content and extracted image URLs read directly from a source URL."""
    links_json = json.dumps(outbound_links or [], ensure_ascii=False)
    imgs_list = list(images or [])
    if not imgs_list and isinstance(raw_data, dict):
        if raw_data.get("images"):
            imgs_list = raw_data["images"]
        elif raw_data.get("og_image"):
            imgs_list = [{"url": raw_data["og_image"], "alt": title or "og:image", "kind": "og:image"}]
    images_json = json.dumps(imgs_list, ensure_ascii=False)
    raw_json = json.dumps(raw_data or {}, ensure_ascii=False)

    with conn:
        conn.execute(
            """
            INSERT INTO source_materials (
                source_url, title, content_type, content, outbound_links, images, raw_json, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(source_url) DO UPDATE SET
                title=coalesce(nullif(excluded.title, ''), source_materials.title),
                content_type=excluded.content_type,
                content=excluded.content,
                outbound_links=excluded.outbound_links,
                images=coalesce(nullif(excluded.images, '[]'), source_materials.images),
                raw_json=excluded.raw_json,
                fetched_at=CURRENT_TIMESTAMP;
            """,
            (source_url, title, content_type, content, links_json, images_json, raw_json),
        )


def ingest_scrape_report(conn: sqlite3.Connection, report: dict) -> int:
    """Ingest a multi-platform report dictionary from scrape_sources.py."""
    query = report.get("query") or ""
    count = 0

    for platform, items in report.get("search_results", {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            if "error" in item:
                continue
            item.setdefault("platform", platform)
            if insert_research_item(conn, item, query=query):
                count += 1

    for scraped in report.get("scraped_urls", []):
        if not isinstance(scraped, dict) or "error" in scraped:
            continue
        url = scraped.get("url")
        if not url:
            continue

        item = {
            "platform": scraped.get("type", "webpage"),
            "title": scraped.get("title", ""),
            "author": scraped.get("author", ""),
            "source_url": url,
            "snippet": scraped.get("description", "") or (scraped.get("content", "")[:300]),
            "content": scraped.get("content") or scraped.get("selftext") or "",
            "score": scraped.get("score") or scraped.get("likes") or 0,
            "num_comments": len(scraped.get("top_comments", [])) or scraped.get("replies", 0),
        }
        if insert_research_item(conn, item, query=query):
            count += 1

        # Save to source_materials
        save_source_material(
            conn,
            source_url=url,
            title=scraped.get("title", ""),
            content_type=scraped.get("type", "webpage"),
            content=scraped.get("content") or scraped.get("selftext") or "",
            outbound_links=scraped.get("outbound_links", []),
            images=scraped.get("images", []),
            raw_data=scraped,
        )

    return count


def query_research(
    conn: sqlite3.Connection,
    search_term: str,
    platform: str = None,
    limit: int = 10,
) -> list:
    """Query research items using FTS5 with fallback to LIKE search."""
    clean_term = re.sub(r"[^\w\s]", "", search_term).strip()
    results = []

    # Try FTS5 first
    if clean_term:
        fts_tokens = [f'"{token}"' for token in clean_term.split() if token]
        fts_query = " AND ".join(fts_tokens) if fts_tokens else clean_term
        try:
            sql = """
                SELECT r.id, r.query, r.platform, r.title, r.author, r.source_url,
                       r.external_url, r.snippet, r.score, r.num_comments, r.created_date,
                       r.scraped_at, rank
                FROM research_items_fts f
                JOIN research_items r ON f.rowid = r.id
                WHERE research_items_fts MATCH ?
            """
            params = [fts_query]
            if platform:
                sql += " AND r.platform = ?"
                params.append(platform)
            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)

            cursor = conn.execute(sql, params)
            for row in cursor.fetchall():
                results.append(dict(row))
        except sqlite3.OperationalError:
            results = []

    # Fallback to standard LIKE if FTS yielded few or empty results
    if len(results) < limit:
        needed = limit - len(results)
        existing_ids = {r["id"] for r in results}
        like_pattern = f"%{search_term.strip()}%"
        sql = """
            SELECT id, query, platform, title, author, source_url,
                   external_url, snippet, score, num_comments, created_date, scraped_at, 0 as rank
            FROM research_items
            WHERE (title LIKE ? OR snippet LIKE ? OR full_content LIKE ?)
        """
        params = [like_pattern, like_pattern, like_pattern]
        if platform:
            sql += " AND platform = ?"
            params.append(platform)
        sql += " ORDER BY score DESC, scraped_at DESC LIMIT ?"
        params.append(needed + len(existing_ids))

        cursor = conn.execute(sql, params)
        for row in cursor.fetchall():
            row_dict = dict(row)
            if row_dict["id"] not in existing_ids:
                results.append(row_dict)
                if len(results) >= limit:
                    break

    return results


def fetch_and_save_source_url(conn: sqlite3.Connection, url: str, force_refresh: bool = False) -> dict:
    """Read material directly from a source URL using scrape_single_url, caching in source_materials."""
    if not force_refresh:
        cursor = conn.execute(
            "SELECT source_url, title, content_type, content, outbound_links, images, fetched_at FROM source_materials WHERE source_url = ?",
            (url,),
        )
        cached = cursor.fetchone()
        if cached:
            return {
                "url": cached["source_url"],
                "title": cached["title"],
                "type": cached["content_type"],
                "content": cached["content"],
                "outbound_links": json.loads(cached["outbound_links"] or "[]"),
                "images": json.loads(cached["images"] or "[]"),
                "fetched_at": cached["fetched_at"],
                "cached": True,
            }

    # Import scraper from sibling path
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from scrape_sources import scrape_single_url

        scraped = scrape_single_url(url)
    except Exception as exc:
        return {"url": url, "error": f"Failed to fetch source URL: {exc}"}

    if "error" not in scraped:
        save_source_material(
            conn,
            source_url=url,
            title=scraped.get("title", ""),
            content_type=scraped.get("type", "webpage"),
            content=scraped.get("content") or scraped.get("selftext") or "",
            outbound_links=scraped.get("outbound_links", []),
            images=scraped.get("images", []),
            raw_data=scraped,
        )
        scraped["cached"] = False
    return scraped


def get_db_stats(conn: sqlite3.Connection) -> dict:
    """Retrieve statistical summary of stored research."""
    with conn:
        total_items = conn.execute("SELECT count(*) FROM research_items").fetchone()[0]
        total_sources = conn.execute("SELECT count(*) FROM source_materials").fetchone()[0]
        platforms = conn.execute(
            "SELECT platform, count(*) as count FROM research_items GROUP BY platform ORDER BY count DESC"
        ).fetchall()
        queries = conn.execute(
            "SELECT query, count(*) as count FROM research_items WHERE query != '' GROUP BY query ORDER BY count DESC LIMIT 10"
        ).fetchall()

    return {
        "total_research_items": total_items,
        "total_cached_sources": total_sources,
        "platforms": {row["platform"]: row["count"] for row in platforms},
        "top_topics": {row["query"]: row["count"] for row in queries},
    }


def main():
    parser = argparse.ArgumentParser(description="Research Database & Retrieval CLI for RAG Agent.")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database file (default: {DEFAULT_DB_PATH})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: init
    subparsers.add_parser("init", help="Initialize SQLite tables and FTS5 search indexes.")

    # Subcommand: query
    query_p = subparsers.add_parser("query", help="Query research items using FTS5 full-text search.")
    query_p.add_argument("--query", "-q", required=True, help="Search terms or topic.")
    query_p.add_argument("--platform", "-p", help="Filter by platform (e.g. reddit, news_rss, bluesky).")
    query_p.add_argument("--limit", "-l", type=int, default=8, help="Max results (default: 8).")
    query_p.add_argument("--format", choices=["json", "markdown"], default="markdown", help="Output format.")

    # Subcommand: read-source (Read material at source URL)
    read_p = subparsers.add_parser("read-source", help="Fetch, cache, and read material at a specific source URL.")
    read_p.add_argument("--url", "-u", required=True, help="Source URL to read and parse.")
    read_p.add_argument("--refresh", action="store_true", help="Force refresh even if cached.")
    read_p.add_argument("--format", choices=["json", "markdown"], default="markdown", help="Output format.")

    # Subcommand: stats
    subparsers.add_parser("stats", help="Show database overview and counts.")

    args = parser.parse_args()
    conn = get_connection(args.db)

    if args.command == "init":
        print(f"Initialized database schema and FTS5 search at: {args.db}")

    elif args.command == "query":
        results = query_research(conn, args.query, platform=args.platform, limit=args.limit)
        if args.format == "json":
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"# Research Query: `{args.query}` ({len(results)} matches)\n")
            if not results:
                print("No matches found in the research database.")
            for idx, r in enumerate(results, 1):
                title = r.get("title") or "Untitled Post"
                url = r.get("source_url", "")
                platform = r.get("platform", "web").upper()
                score = r.get("score", 0)
                author = r.get("author", "")
                snippet = r.get("snippet", "")

                print(f"### {idx}. [{title}]({url})")
                print(f"- **Platform:** `{platform}` | **Author:** {author} | **Score/Upvotes:** {score}")
                print(f"- **Source URL:** {url}")
                if snippet:
                    print(f"- **Snippet:** {snippet.strip()}\n")

    elif args.command == "read-source":
        material = fetch_and_save_source_url(conn, args.url, force_refresh=args.refresh)
        if args.format == "json":
            print(json.dumps(material, indent=2, ensure_ascii=False))
        else:
            if "error" in material:
                print(f"⚠️ Error reading source URL: {material['error']}")
            else:
                title = material.get("title") or args.url
                status = "Cached" if material.get("cached") else "Live Fetched"
                print(f"# Source Material: [{title}]({args.url}) ({status})\n")
                print(f"**URL:** {args.url}  ")
                print(f"**Type:** `{material.get('type', 'webpage')}`\n")
                if material.get("content"):
                    print("## Content\n")
                    print(material.get("content"))
                elif material.get("selftext"):
                    print("## Post Text\n")
                    print(material.get("selftext"))
                if material.get("top_comments"):
                    print("\n## Top Comments\n")
                    for c in material.get("top_comments"):
                        print(f"- **{c.get('author', 'anon')}** (Score: {c.get('score', 0)}): {c.get('body')}")
                if material.get("images"):
                    print("\n## Extracted Reference Images\n")
                    for img in material.get("images"):
                        if isinstance(img, dict):
                            alt = img.get("alt") or img.get("kind") or "Reference Image"
                            img_url = img.get("url", "")
                            kind = img.get("kind", "img")
                            if img_url:
                                print(f"- [{alt}]({img_url}) (`{kind}`)")
                        elif isinstance(img, str):
                            print(f"- [Reference Image]({img})")

    elif args.command == "stats":
        stats = get_db_stats(conn)
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
