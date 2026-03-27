#!/usr/bin/env python3
"""
analyze_transcripts.py — Analyze YouTube transcripts and produce a skill research report.

Usage:
    python scripts/analyze_transcripts.py \
        --transcripts-dir skills/my-skill/research/ \
        --skill-topic "Claude Code custom skills" \
        --output skills/my-skill/research-report.md

Dependencies:
    pip install anthropic
    Set ANTHROPIC_API_KEY in environment.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def load_transcripts(transcripts_dir: str) -> list[dict]:
    """Load all transcript .txt files from a directory."""
    dir_path = Path(transcripts_dir)
    transcripts = []

    for txt_file in sorted(dir_path.glob("*.txt")):
        with open(txt_file, encoding="utf-8") as f:
            content = f.read()

        # Parse header metadata
        lines = content.split("\n")
        meta = {}
        body_start = 0
        for i, line in enumerate(lines):
            if line.startswith("# "):
                key, _, value = line[2:].partition(": ")
                meta[key.lower().replace(" ", "_")] = value
            elif line == "":
                body_start = i + 1
                break

        body = "\n".join(lines[body_start:]).strip()

        # Truncate very long transcripts to keep within context limits
        MAX_CHARS = 12000
        if len(body) > MAX_CHARS:
            body = body[:MAX_CHARS] + f"\n\n[Transcript truncated at {MAX_CHARS} chars]"

        transcripts.append({
            "file": str(txt_file),
            "title": meta.get("transcript", txt_file.stem),
            "channel": meta.get("channel", "unknown"),
            "video_id": meta.get("video_id", ""),
            "url": meta.get("url", ""),
            "content": body,
            "char_count": len(body),
        })

    return transcripts


def build_analysis_prompt(skill_topic: str, transcripts: list[dict]) -> str:
    transcript_sections = []
    for i, t in enumerate(transcripts, 1):
        transcript_sections.append(
            f"--- VIDEO {i} ---\n"
            f"Title: {t['title']}\n"
            f"Channel: {t['channel']}\n"
            f"URL: {t['url']}\n\n"
            f"{t['content']}\n"
        )

    transcripts_text = "\n\n".join(transcript_sections)

    return f"""You are a research analyst helping design a Claude AI skill on the topic: "{skill_topic}".

You have been given transcripts from {len(transcripts)} YouTube videos on this topic. Your job is to analyze them and produce a structured research report that will guide the creation of a new Claude skill.

{transcripts_text}

---

Based on these transcripts, produce a comprehensive research report in the following Markdown format:

# Research Report: {skill_topic}

## Executive Summary
2-3 sentences summarizing what the research found and the overall recommendation.

## Key Use Cases Identified
List the specific use cases, workflows, or capabilities mentioned across the videos. For each, note how frequently it appeared and how much emphasis was placed on it.

## What Should Be Built (Into the Skill)
For each recommended capability:
- **Capability name**: What it is
- **Why it's valuable**: Evidence from the transcripts
- **Complexity**: Simple / Medium / Complex
- **Implementation approach**: Brief suggestion

## What Should NOT Be Built
Capabilities that are out of scope, too complex, already handled by Claude natively, or not worth automating. Explain why for each.

## Recommended Skill Design
- **Skill name**: (kebab-case)
- **Trigger phrases**: Specific phrases and contexts that should activate this skill
- **Core workflow**: Step-by-step high-level workflow
- **Inputs**: What the user provides
- **Outputs**: What the skill produces
- **Dependencies**: Any tools, APIs, or scripts needed

## Gaps & Unknowns
Things the research didn't answer that the skill designer should investigate.

## Sources
| # | Title | Channel | URL |
|---|-------|---------|-----|
{chr(10).join(f"| {i+1} | {t['title'][:50]} | {t['channel']} | {t['url']} |" for i, t in enumerate(transcripts))}

---

Be specific and actionable. Ground your recommendations in what you actually found in the transcripts — don't invent capabilities that weren't discussed.
"""


def call_claude(prompt: str) -> str:
    """Call Claude API to analyze transcripts."""
    try:
        import anthropic
    except ImportError:
        print("Error: anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set in environment.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print("Calling Claude API to analyze transcripts...", file=sys.stderr)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


def main():
    parser = argparse.ArgumentParser(description="Analyze YouTube transcripts and generate a skill research report.")
    parser.add_argument("--transcripts-dir", required=True, help="Directory containing transcript .txt files")
    parser.add_argument("--skill-topic", required=True, help="The topic/capability being researched")
    parser.add_argument("--output", required=True, help="Output path for the research report (.md)")
    args = parser.parse_args()

    transcripts = load_transcripts(args.transcripts_dir)

    if not transcripts:
        print(f"No transcripts found in: {args.transcripts_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(transcripts)} transcripts from {args.transcripts_dir}", file=sys.stderr)
    for t in transcripts:
        print(f"  - {t['title'][:60]} ({t['char_count']:,} chars)", file=sys.stderr)

    prompt = build_analysis_prompt(args.skill_topic, transcripts)
    report = call_claude(prompt)

    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport saved to: {output_path}", file=sys.stderr)
    print("\n" + "="*60, file=sys.stderr)
    print("REPORT PREVIEW (first 500 chars):", file=sys.stderr)
    print(report[:500], file=sys.stderr)


if __name__ == "__main__":
    main()
