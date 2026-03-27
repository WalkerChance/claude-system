#!/usr/bin/env python3
"""
yt_search.py — Search YouTube for top videos on a topic.

Usage:
    python scripts/yt_search.py --query "Claude Code skills" --max-results 10

Output:
    Prints a JSON list of videos with id, title, channel, and URL.
    Also saves results to skills/<slug>/research/search-results.json if --output is set.

Dependencies:
    pip install yt-dlp
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", text.lower()).strip("-")


def search_youtube(query: str, max_results: int) -> list[dict]:
    """Use yt-dlp to search YouTube and return video metadata."""
    cmd = [
        sys.executable, "-m", "yt_dlp",
        f"ytsearch{max_results}:{query}",
        "--dump-json",
        "--no-playlist",
        "--skip-download",
        "--quiet",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        print("Error: yt_dlp module not found. Install it with: pip install yt-dlp", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Error: YouTube search timed out.", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        print(f"Error from yt-dlp: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            meta = json.loads(line)
            videos.append({
                "id": meta.get("id"),
                "title": meta.get("title"),
                "channel": meta.get("uploader") or meta.get("channel"),
                "duration_seconds": meta.get("duration"),
                "view_count": meta.get("view_count"),
                "upload_date": meta.get("upload_date"),
                "url": f"https://www.youtube.com/watch?v={meta.get('id')}",
                "description_snippet": (meta.get("description") or "")[:200],
            })
        except json.JSONDecodeError:
            continue

    return videos


def format_for_display(videos: list[dict]) -> str:
    lines = [f"Found {len(videos)} videos:\n"]
    for i, v in enumerate(videos, 1):
        duration = ""
        if v.get("duration_seconds"):
            mins = v["duration_seconds"] // 60
            secs = v["duration_seconds"] % 60
            duration = f" [{mins}:{secs:02d}]"
        views = ""
        if v.get("view_count"):
            views = f" | {v['view_count']:,} views"
        lines.append(f"{i:2}. [{v['id']}] {v['title']}{duration}{views}")
        lines.append(f"     Channel: {v['channel']}")
        lines.append(f"     URL: {v['url']}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search YouTube for videos on a topic.")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--max-results", type=int, default=10, help="Max number of results (default: 10)")
    parser.add_argument("--output", help="Directory to save search-results.json (optional)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted list")
    args = parser.parse_args()

    print(f"Searching YouTube for: '{args.query}'...", file=sys.stderr)
    videos = search_youtube(args.query, args.max_results)

    if not videos:
        print("No results found.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(videos, indent=2))
    else:
        print(format_for_display(videos))

    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "search-results.json"
        with open(output_file, "w") as f:
            json.dump({"query": args.query, "results": videos}, f, indent=2)
        print(f"\nResults saved to: {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
