# Claude System — Project Instructions

This is a personal Claude Code system for automating research, productivity, and project management workflows. It is designed to grow over time as new skills and agents are added.

## Repo Structure

```
claude-system/
├── CLAUDE.md                  # This file — project-level instructions
├── skills/                    # Custom Claude skills (SKILL.md format)
│   ├── skill-builder/         # Pipeline to research, design, and create new skills
│   └── productivity-agent/    # Daily briefing, task capture, nudges, weekly review
├── agents/                    # Standalone agent scripts and configs
├── projects/                  # Individual project directories
│   └── smite2-oracle/         # Smite 2 build tracker and recommendation engine
└── scripts/                   # Shared utility scripts (scrapers, helpers, etc.)
```

## Core Principles

- **Skills first**: Before building any new capability, check if a skill exists or should be created.
- **GitHub is the source of truth**: All changes should be committed. Treat `main` as stable.
- **Automate the boring**: If something is done more than twice manually, build a script or skill for it.
- **MCP-aware**: The productivity agent connects to Google Calendar, Gmail, and Slack via MCP. Always check MCP availability before running agent workflows.

## Active Skills

| Skill | Purpose | Status |
|-------|---------|--------|
| `skill-builder` | Research YouTube, generate reports, author and register new skills | ✅ Active |
| `productivity-agent` | Daily briefings, task capture, nudges, weekly review | ✅ Active |

## Active Projects

| Project | Purpose | Status |
|---------|---------|--------|
| `smite2-oracle` | Smite 2 god build recommendations powered by pro build data | 🔧 In Progress |

## How to Add a New Skill

1. Run the `skill-builder` pipeline: provide a topic and it will research, report, and draft the skill.
2. Review the generated report in `skills/<skill-name>/research-report.md`.
3. Approve or modify the draft `SKILL.md`.
4. Commit to GitHub.

## How to Run the Productivity Agent

```bash
# Daily briefing (run each morning)
claude -p "Run my daily briefing" --skill productivity-agent

# Weekly review (run Friday EOD)
claude -p "Run my weekly review" --skill productivity-agent
```

## Environment & Dependencies

- Python 3.11+
- `youtube-transcript-api` — for transcript fetching
- `yt-dlp` — for YouTube search
- MCP servers: Google Calendar, Gmail, Slack (configured in Claude Code settings)
- GitHub CLI (`gh`) — for repo management

## Notes

- Skills live in `skills/<name>/SKILL.md` and follow the standard frontmatter format.
- The `scripts/` directory contains shared utilities used across multiple skills and projects.
- When in doubt, read the relevant SKILL.md before starting any task.
