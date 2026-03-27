# Research Report: Productivity Agent — Gmail + Google Calendar MCP

## Research Method

YouTube transcript research was attempted but blocked by proxy (403 Forbidden).
Research proceeded via direct MCP tool capability audit and domain knowledge of
productivity system best practices (GTD, time-blocking, inbox-zero patterns).

---

## Executive Summary

A Claude-powered productivity agent connected to Gmail and Google Calendar via MCP
can deliver high-value daily workflows: morning briefings that surface the day's
schedule and priority emails, ongoing task capture from inbox action language,
smart nudges based on calendar load, and Friday weekly reviews. The Gmail MCP
exposes full search/read capability. The Google Calendar MCP exposes events, free
time, and meeting scheduling. Together they cover the core "what's on my plate"
and "what did I miss" use cases without needing Slack or Notion.

---

## Available MCP Tool Audit

### Gmail MCP (`mcp__66697141-53e4-4ba8-a986-43cce0690113`)

| Tool | Capability |
|------|-----------|
| `gmail_get_profile` | Get user's Gmail address / account info |
| `gmail_search_messages` | Full Gmail query syntax: `is:unread`, `from:`, `after:`, `has:attachment`, etc. |
| `gmail_read_message` | Read full message body and headers |
| `gmail_read_thread` | Read full thread (all replies) |
| `gmail_list_labels` | List all Gmail labels (Inbox, Starred, custom) |
| `gmail_list_drafts` | List saved drafts |
| `gmail_create_draft` | Create a draft reply or new message |

**Key capabilities unlocked:**
- Unread inbox scan with priority detection
- Action-item extraction using search queries (`"please review"`, `"action required"`, `"by EOD"`)
- Thread context for follow-up detection
- Draft creation for replies the user needs to send

### Google Calendar MCP (`mcp__e3fc7b63-9f15-420c-bcff-33e4408fb6ba`)

| Tool | Capability |
|------|-----------|
| `gcal_list_calendars` | List all calendars the user has access to |
| `gcal_list_events` | List events in a time range, with search and pagination |
| `gcal_get_event` | Get full details of a single event |
| `gcal_create_event` | Create new calendar events |
| `gcal_update_event` | Update existing events |
| `gcal_delete_event` | Delete events |
| `gcal_respond_to_event` | Accept/decline/tentative responses to invites |
| `gcal_find_meeting_times` | Find available times for meetings with attendees |
| `gcal_find_my_free_time` | Find blocks of free time in a window |

**Key capabilities unlocked:**
- Today's schedule (times, locations, video links)
- Free-time detection for focus block identification
- Meeting invite handling (respond directly)
- Workload assessment (back-to-back meeting detection for nudges)
- Next-week preview for weekly reviews

---

## Key Use Cases Identified

1. **Daily Briefing** — Pull today's events + unread priority emails → structured morning summary
2. **Task Capture** — Scan Gmail for action language → extract tasks → output as markdown list (or create calendar blocks)
3. **Nudge Engine** — Cross-reference open tasks with calendar free time → flag at-risk items
4. **Weekly Review** — Summarize week's meetings, surface unanswered threads, preview next week

---

## What Should Be Built

### 1. Daily Briefing (high value, low complexity)
- List today's calendar events with times and video links
- Search Gmail `is:unread after:<yesterday>` for unread messages
- Categorize as: action required / time-sensitive / FYI
- Output structured briefing with focus recommendation
- **Why valuable**: Replaces 10 minutes of manual inbox + calendar scanning

### 2. Task Capture (high value, medium complexity)
- Gmail search for action language keywords
- Extract: task description, sender, deadline hint, message link
- Output as a markdown checklist (no Notion required)
- Optionally create a calendar block for the task
- **Why valuable**: Nothing falls through the cracks from email

### 3. Nudge Engine (medium value, medium complexity)
- Identify tasks captured but not resolved (no reply sent, no calendar block created)
- Use `gcal_find_my_free_time` to surface when the user has time to act
- Output a prioritized "what to do now" list
- **Why valuable**: Bridges the gap between capturing and doing

### 4. Weekly Review (high value, low complexity)
- Pull Mon-Fri events via `gcal_list_events`
- Pull unread/unanswered threads from the week via Gmail search
- Generate structured review: meetings attended, emails unresolved, next-week preview
- **Why valuable**: Forces reflection and prevents carryover buildup

---

## What Should NOT Be Built

- **Slack integration** — Not available via MCP in this environment; skip
- **Notion integration** — Not available; use markdown output instead
- **Auto-send email replies** — Gmail MCP only supports draft creation, not send; good, avoids mistakes
- **Complex NLP task extraction** — Claude's in-context reasoning is sufficient; no external ML needed
- **Cross-calendar conflict detection** — Complexity not worth it for v1; use `find_my_free_time` instead

---

## Recommended Skill Design

- **Skill name**: `productivity-agent`
- **Trigger phrases**: "morning briefing", "daily briefing", "what's on my plate", "catch me up", "capture tasks", "weekly review", "what should I focus on", "what did I miss", "nudge me"
- **Core workflows**: Daily Briefing, Task Capture, Nudge Engine, Weekly Review
- **MCP dependencies**: Gmail (required), Google Calendar (required)
- **Output format**: Structured markdown in chat; optional draft creation in Gmail
- **Orchestration**: Morning = Briefing + Capture; Midday = Nudge; Friday EOD = Nudge + Review

---

## Sources

_YouTube research was unavailable due to proxy restrictions. Report based on:_
- Direct audit of Gmail MCP tool schemas
- Direct audit of Google Calendar MCP tool schemas
- Domain knowledge: GTD (Getting Things Done), inbox-zero methodology, time-blocking best practices
- Pattern analysis of existing `productivity-agent/SKILL.md` v1
