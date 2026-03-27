---
name: productivity-agent
description: Personal productivity agent that keeps you on top of your day. Use this skill for daily briefings, capturing tasks from Gmail or Slack, sending reminders and nudges, and running weekly reviews. Trigger any time the user says "morning briefing", "what's on my plate", "catch me up", "weekly review", "what did I miss", "capture tasks from my email", or "what should I focus on". Connects to Google Calendar, Gmail, Slack, and Notion. Always use this skill for any productivity, task management, or "get shit done" request.
---

# Productivity Agent

A personal productivity agent that connects your calendar, email, messages, and tasks into a unified system. It runs four core workflows that can be triggered individually or together.

## MCP Requirements

This skill requires the following MCP connections (check availability before running):
- **Google Calendar** — `https://gcal.mcp.claude.com/mcp`
- **Gmail** — `https://gmail.mcp.claude.com/mcp`
- **Slack** — (configure in Claude Code MCP settings)
- **Notion** — (configure API key in environment)

If any connection is unavailable, note it and proceed with available sources.

---

## Workflow 1: Daily Briefing

Run each morning. Pulls together everything the user needs to start the day.

### Steps

1. **Fetch today's calendar** — Pull all events for today from Google Calendar. Note times, locations, and any video links.

2. **Scan Gmail priority inbox** — Look for unread emails from the last 24 hours. Identify:
   - Action items (emails requiring a reply or decision)
   - Time-sensitive items (deadlines, meeting requests)
   - FYIs (no action needed)

3. **Check Slack mentions** — Pull unread @mentions and DMs from the last 24 hours. Flag anything requiring a response.

4. **Cross-reference with open tasks** — If Notion is connected, pull open tasks due today or overdue.

5. **Generate briefing** — Output a structured daily briefing:

```
## 🌅 Daily Briefing — [Date]

### Today's Schedule
- [time] — [event title] ([location/link])

### Priority Inbox (Action Required)
- [sender]: [subject] — [one-line summary + recommended action]

### Slack (Needs Response)
- [@channel or DM]: [summary]

### Open Tasks Due Today
- [ ] [task name] — [due time if set]

### Focus Recommendation
[1-2 sentences on what to tackle first and why]
```

---

## Workflow 2: Task Capture

Monitors Gmail and Slack for action items and writes them to Notion.

### Steps

1. **Scan Gmail** — Look for emails containing action language: "please review", "can you", "by EOD", "deadline", "following up", "action required". Extract:
   - Task description
   - Who assigned it
   - Deadline (if mentioned)
   - Source email link

2. **Scan Slack** — Look for DMs or @mentions with action language. Same extraction as above.

3. **Deduplicate** — Check if a task already exists in Notion before creating it.

4. **Write to Notion** — Create a task entry for each new item:
   - Title: short task description
   - Source: Gmail / Slack + sender
   - Due date: extracted or blank
   - Status: To Do
   - Link: direct link to source email or message

5. **Confirm** — Report back: "Captured X new tasks to Notion."

---

## Workflow 3: Nudge Engine

Checks open tasks against the calendar and sends Slack reminders when things are at risk.

### Steps

1. **Pull open tasks from Notion** — Filter for status = "To Do" or "In Progress" with a due date.

2. **Check calendar** — Identify busy blocks today that reduce available working time.

3. **Flag at-risk tasks** — Any task due today or tomorrow where:
   - The user has back-to-back meetings
   - The task has been open for 3+ days with no status change
   - The deadline is within 2 hours

4. **Send Slack nudge** — For each at-risk task, send a DM to the user:
   ```
   ⚠️ Task at risk: "[task name]"
   Due: [date/time]
   Last updated: [N days ago]
   → [link to Notion task]
   ```

5. **Report** — Summary of nudges sent.

---

## Workflow 4: Weekly Review

Run Friday EOD (or manually any time). Produces a structured review of the week.

### Steps

1. **Pull completed tasks from Notion** — Filter for tasks marked Done this week.

2. **Pull incomplete tasks** — Tasks that were due this week but not completed.

3. **Review calendar** — Pull all events from Mon-Fri this week.

4. **Generate weekly review**:

```
## 📋 Weekly Review — Week of [Date]

### ✅ Completed This Week
- [task name]

### ❌ Not Completed (Rolling Over)
- [task name] — [recommended action: reschedule / drop / delegate]

### 📅 Meetings & Events
- [count] meetings | [total hours] hours in meetings

### 🔮 Next Week Preview
- [top 3 priorities for next week based on open tasks + calendar]

### 💡 Reflection Prompt
[One question to prompt the user to think about their week]
```

5. **Update Notion** — Move incomplete tasks to next week, log the review.

---

## Orchestration

All four workflows can be chained. Common patterns:

```
Morning routine:    Daily Briefing → Task Capture
Midday check-in:    Nudge Engine
End of week:        Nudge Engine → Weekly Review
```

To run a chain, specify which workflows in your prompt: "Run my morning routine" triggers Daily Briefing + Task Capture automatically.

---

## Notes

- Always confirm MCP connections at the start of any workflow.
- If Notion isn't available, output tasks as a markdown list and ask where to save them.
- Nudges should feel helpful, not naggy — max 3 nudges per day.
- The weekly review reflection prompt should rotate — don't repeat the same question two weeks in a row.
