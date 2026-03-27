#!/usr/bin/env python3
"""
fetch_transcripts.py — Fetch transcripts for YouTube videos.

Usage:
    python scripts/fetch_transcripts.py --video-ids dQw4w9WgXcQ abc123 --output skills/my-skill/research/
    python scripts/fetch_transcripts.py --from-file skills/my-skill/research/search-results.json --output skills/my-skill/research/

Output:
    Saves one .txt transcript file per video in the output directory.
    Also saves a manifest.json listing all fetched/failed videos.

Dependencies:
    pip install youtube-transcript-api
"""

import argparse
import json
import sys
import time
from pathlib import Path


def fetch_transcript(video_id: str) -> tuple[str | None, str | None]:
    """
    Fetch transcript for a single video.
    Returns (transcript_text, error_message).
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
    except ImportError:
        print("Error: youtube-transcript-api not installed. Run: pip install youtube-transcript-api", file=sys.stderr)
        sys.exit(1)

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Prefer manually created English, fall back to auto-generated, then any language
        try:
            transcript = transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
        except Exception:
            try:
                transcript = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
            except Exception:
                # Take whatever's available and translate
                transcript = transcript_list.find_generated_transcript(
                    [t.language_code for t in transcript_list]
                ).translate("en")

        entries = transcript.fetch()
        text = " ".join(entry["text"] for entry in entries)
        # Clean up common transcript artifacts
        text = text.replace("\n", " ").replace("[Music]", "").replace("[Applause]", "")
        text = " ".join(text.split())  # normalize whitespace
        return text, None

    except Exception as e:
        return None, str(e)


def load_video_ids_from_file(filepath: str) -> list[dict]:
    """Load video IDs from a search-results.json file."""
    with open(filepath) as f:
        data = json.load(f)
    return data.get("results", [])


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube transcripts.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--video-ids", nargs="+", help="One or more YouTube video IDs")
    group.add_argument("--from-file", help="Path to search-results.json from yt_search.py")
    parser.add_argument("--output", required=True, help="Directory to save transcripts")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests (default: 1.0)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build list of videos to process
    videos = []
    if args.video_ids:
        videos = [{"id": vid, "title": vid, "channel": "unknown"} for vid in args.video_ids]
    else:
        videos = load_video_ids_from_file(args.from_file)

    if not videos:
        print("No videos to process.", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching transcripts for {len(videos)} videos...", file=sys.stderr)

    manifest = {"fetched": [], "failed": []}

    for i, video in enumerate(videos, 1):
        video_id = video["id"]
        title = video.get("title", video_id)
        channel = video.get("channel", "unknown")

        print(f"[{i}/{len(videos)}] {title[:60]}...", file=sys.stderr)

        transcript, error = fetch_transcript(video_id)

        if transcript:
            # Save transcript
            safe_id = video_id.replace("/", "_")
            output_file = output_dir / f"{safe_id}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# Transcript: {title}\n")
                f.write(f"# Channel: {channel}\n")
                f.write(f"# Video ID: {video_id}\n")
                f.write(f"# URL: https://www.youtube.com/watch?v={video_id}\n\n")
                f.write(transcript)

            manifest["fetched"].append({
                "id": video_id,
                "title": title,
                "channel": channel,
                "file": str(output_file),
                "char_count": len(transcript),
            })
            print(f"  ✓ Saved ({len(transcript):,} chars)", file=sys.stderr)
        else:
            manifest["failed"].append({
                "id": video_id,
                "title": title,
                "channel": channel,
                "reason": error,
            })
            print(f"  ✗ Failed: {error}", file=sys.stderr)

        if i < len(videos):
            time.sleep(args.delay)

    # Save manifest
    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDone: {len(manifest['fetched'])} fetched, {len(manifest['failed'])} failed", file=sys.stderr)
    print(f"Manifest saved to: {manifest_file}", file=sys.stderr)

    if manifest["failed"]:
        print("\nFailed videos:", file=sys.stderr)
        for v in manifest["failed"]:
            print(f"  - {v['title']} ({v['id']}): {v['reason']}", file=sys.stderr)


if __name__ == "__main__":
    main()
