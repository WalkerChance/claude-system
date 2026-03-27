# claude-system

A personal Claude Code system for automating research, productivity, and project management. Built to grow — new skills get added via the skill-builder pipeline, agents get wired to real tools via MCP.

## Quick Start

```bash
# Clone and set up
git clone https://github.com/YOUR_USERNAME/claude-system.git
cd claude-system
bash setup.sh
```

## What's Inside

### Skills

| Skill | What it does |
|-------|-------------|
| `skill-builder` | Research YouTube → generate report → author new skill → register it |
| `productivity-agent` | Daily briefings, task capture from Gmail/Slack, nudges, weekly review |

### Projects

| Project | What it does |
|---------|-------------|
| `smite2-oracle` | Smite 2 god build recommendations powered by scraped pro build data |

### Scripts

| Script | What it does |
|--------|-------------|
| `scripts/yt_search.py` | Search YouTube and return video metadata |
| `scripts/fetch_transcripts.py` | Fetch transcripts for YouTube video IDs |
| `scripts/analyze_transcripts.py` | Call Claude to analyze transcripts and produce a research report |

## Building a New Skill

```bash
# 1. Search for relevant YouTube videos
python scripts/yt_search.py --query "your topic here" --max-results 10 \
    --output skills/your-skill/research/

# 2. Fetch transcripts for selected videos
python scripts/fetch_transcripts.py \
    --from-file skills/your-skill/research/search-results.json \
    --output skills/your-skill/research/

# 3. Analyze and generate research report
python scripts/analyze_transcripts.py \
    --transcripts-dir skills/your-skill/research/ \
    --skill-topic "Your Skill Topic" \
    --output skills/your-skill/research-report.md

# 4. Review the report, then ask Claude to draft the SKILL.md
# 5. Commit and push
git add skills/your-skill/
git commit -m "feat: add your-skill"
git push
```

## Running the Productivity Agent

The productivity agent requires MCP connections to Google Calendar, Gmail, and Slack. Configure these in your Claude Code MCP settings, then:

```
# In Claude Code
"Run my daily briefing"
"Capture tasks from my email"
"What should I focus on today?"
"Run my weekly review"
```

## Environment Variables

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

## Dependencies

```
anthropic>=0.40.0
youtube-transcript-api>=0.6.0
yt-dlp>=2024.1.0
```

Install: `pip install -r requirements.txt`
