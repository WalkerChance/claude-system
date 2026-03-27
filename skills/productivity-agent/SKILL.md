---
name: productivity-agent
description: Personal productivity agent that keeps you on top of your day using Gmail and Google Calendar. Use this skill for daily briefings, capturing tasks from email, sending nudges about at-risk items, and running weekly reviews. Trigger any time the user says "morning briefing", "daily briefing", "what's on my plate", "catch me up", "weekly review", "what did I miss", "capture tasks from my email", "nudge me", or "what should I focus on". Always use this skill for any productivity, task management, or daily planning request.
---

# Productivity Agent

A personal productivity agent that connects Gmail and Google Calendar into a unified daily workflow. It runs four core workflows that can be triggered individually or chained together.

## MCP Requirements

This skill requires two MCP connections. Confirm both are available before running:

- **Gmail MCP** — provides `gmail_search_messages`, `gmail_read_message`, `gmail_read_thread`, `gmail_list_labels`, `gmail_create_draft`, `gmail_get_profile`
- **Google Calendar MCP** — provides `gcal_list_events`, `gcal_get_event`, `gcal_find_my_free_time`, `gcal_list_calendars`, `gcal_create_event`, `gcal_respond_to_event`

If either connection is unavailable, note it and work with what's available.

---

## Workflow 1: Daily Briefing

Run each morning. Pulls together everything needed to start the day focused.

### Steps

1. **Fetch today's calendar**
   - Call `gcal_list_events` with `timeMin` = start of today, `timeMax` = end of today
   - Extract: event title, start/end time, location or video link, attendees
   - Note any meeting invites needing a response (use `gcal_respond_to_event` if user wants to act)

2. **Find focus blocks**
   - Call `gcal_find_my_free_time` for today
   - Identify gaps of 30+ minutes — these are available focus windows

3. **Scan priority inbox**
   - Call `gmail_search_messages` with query: `is:unread newer_than:1d`
   - For each message, call `gmail_read_message` to get subject + snippet
   - Categorize each as:
     - **Action Required** — needs a reply, decision, or action (keywords: "please review", "can you", "action required", "following up", "deadline", "by EOD", "RSVP")
     - **Time-Sensitive** — meeting request, same-day deadline
     - **FYI** — newsletters, notifications, CC'd updates (no reply needed)

4. **Generate briefing**

```
## Daily Briefing — [Weekday, Month Day]

### Today's Schedule
- [HH:MM] — [Event Title] ([location or video link])
- [HH:MM] — [Event Title]

### Focus Windows Available
- [HH:MM–HH:MM] ([duration])

### Priority Inbox — Action Required
- [Sender Name]: [Subject] — [one-line summary] → [recommended action]

### Time-Sensitive
- [Sender Name]: [Subject] — [deadline or urgency]

### FYI (no action needed)
- [count] newsletters/notifications — skipped

### Focus Recommendation
[1–2 sentences on what to tackle first and why, based on calendar load + inbox]
```

---

## Workflow 2: Task Capture

Scans Gmail for action items and outputs them as a task list. Optionally blocks time on the calendar.

### Steps

1. **Search Gmail for action language**
   - Call `gmail_search_messages` with query: `is:unread ("please review" OR "can you" OR "action required" OR "following up" OR "deadline" OR "by EOD" OR "need your" OR "waiting on you")`
   - Also search: `is:starred newer_than:7d` for starred-but-unresolved emails

2. **Extract task details**
   - For each hit, call `gmail_read_message` to get full context
   - Extract:
     - **Task**: what needs to be done (one sentence)
     - **From**: sender name + email
     - **Deadline**: any date/time mentioned, or "unspecified"
     - **Message ID**: for linking back

3. **Deduplicate**
   - If the same task appears in multiple messages (a thread), count it once
   - Use `gmail_read_thread` to collapse threads before extracting

4. **Output task list**

```
## Captured Tasks — [Date]

- [ ] [Task description] — from [Sender] | due: [deadline] | [message link if available]
- [ ] [Task description] — from [Sender] | due: [deadline]
...

Total: [N] tasks captured
```

5. **Offer to block time** — Ask: "Want me to create calendar blocks for any of these?" If yes, call `gcal_create_event` for each selected task.

---

## Workflow 3: Nudge Engine

Identifies tasks from email that are still unresolved and surfaces when to act on them based on free calendar time.

### Steps

1. **Find unresolved threads**
   - Call `gmail_search_messages` with: `is:unread older_than:2d ("please review" OR "action required" OR "following up" OR "waiting on you")`
   - These are emails that arrived with action language but haven't been replied to

2. **Also check for unanswered follow-ups**
   - Call `gmail_search_messages` with: `subject:("following up") is:unread`

3. **Check calendar load**
   - Call `gcal_find_my_free_time` for today and tomorrow
   - Identify if the user has back-to-back meetings with little room to respond

4. **Flag at-risk items**
   - An item is at-risk if:
     - It has action language AND has been unread for 2+ days
     - OR a deadline mentioned in the email is within 24 hours
     - OR a meeting request hasn't been responded to

5. **Output nudge summary**

```
## Nudge Report — [Date]

### At-Risk Items (act today)
⚠️ [Sender]: [Subject] — [why it's at risk: X days unread / deadline today]
⚠️ [Sender]: [Subject] — [why it's at risk]

### Best Time to Work on These
📅 You have free time at [HH:MM–HH:MM] today — block it for these tasks?

### Pending Meeting Invites
📨 [Event name] from [Organizer] — respond before [date]
```

6. **Offer actions** — For each item, offer to draft a reply (`gmail_create_draft`) or block focus time (`gcal_create_event`).

---

## Workflow 4: Weekly Review

Run Friday EOD or any time. Produces a structured review of the week and a preview of next week.

### Steps

1. **Pull this week's calendar**
   - Call `gcal_list_events` with `timeMin` = Monday 00:00, `timeMax` = Friday 23:59
   - Count: total meetings, total hours in meetings
   - Note any recurring vs one-off meetings

2. **Find next week's calendar**
   - Call `gcal_list_events` with `timeMin` = next Monday, `timeMax` = next Friday
   - Identify the top 3 commitments by time or importance

3. **Scan for unresolved inbox items this week**
   - Call `gmail_search_messages`: `is:unread after:[last Monday's date]`
   - Identify threads that are unread and contain action language

4. **Find free focus time next week**
   - Call `gcal_find_my_free_time` for the next 5 business days
   - Note the largest available blocks

5. **Generate weekly review**

```
## Weekly Review — Week of [Month Day–Day]

### This Week in Meetings
- [N] meetings | ~[X] hours in meetings
- Busiest day: [Day]
- Notable: [any major meetings worth flagging]

### Unresolved from This Week
- [Sender]: [Subject] — [recommended action: reply / schedule / drop]
- [Sender]: [Subject] — [recommended action]

### Next Week Preview
📅 Top commitments:
- [Event] on [Day]
- [Event] on [Day]

🔓 Best focus windows:
- [Day HH:MM–HH:MM] ([duration])

### Reflection Prompt
[One rotating question to close out the week — see rotation below]
```

6. **Reflection prompt rotation** — Rotate through these (don't repeat consecutively):
   - "What's one thing you'd do differently if you ran this week again?"
   - "What slipped through the cracks that you need to catch next week?"
   - "What were you most proud of completing this week?"
   - "Where did you feel most reactive vs. proactive?"
   - "What's the one thing that would make next week a success?"

---

## Orchestration

Common workflow chains:

| Pattern | Trigger | Workflows |
|---------|---------|-----------|
| Morning routine | "Run my morning briefing" | Briefing → Task Capture |
| Midday check-in | "Nudge me" / "What am I missing?" | Nudge Engine |
| End of week | "Weekly review" | Nudge Engine → Weekly Review |
| Full daily | "Full daily check" | Briefing → Task Capture → Nudge Engine |

---

## Notes & Edge Cases

- **Always confirm MCP connections first** — if Gmail is down, skip email steps and run calendar-only briefing
- **Max 5 action items in briefing** — if more than 5 unread action emails, show top 5 and note the count
- **Don't read full bodies for FYI** — use subject + snippet only to keep responses fast
- **gmail_create_draft only** — this skill never sends email directly; it creates drafts for the user to review
- **Timezone awareness** — always use the user's local timezone for calendar queries; infer from their calendar settings via `gcal_list_calendars`
- **Nudge limit** — surface at most 5 at-risk items per nudge run to avoid overwhelming
- **Reflection prompt rotation** — track which prompt was last used in the conversation context and skip it next time
