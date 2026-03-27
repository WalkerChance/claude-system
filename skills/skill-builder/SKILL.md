---
name: skill-builder
description: Research, design, and create new Claude skills using YouTube as a knowledge source. Use this skill whenever the user wants to build a new Claude skill, automate a new capability, research best practices for a workflow via YouTube, or turn a manual process into a reusable Claude skill. Trigger any time the user says "build a skill for", "make a skill that", "research how to", "create a pipeline for", or "automate X". This skill runs a full pipeline: YouTube research → analysis report → skill design → SKILL.md authoring → registration.
---

# Skill Builder Pipeline

This skill automates the full lifecycle of creating a new Claude skill: from research to a deployable SKILL.md.

## Pipeline Overview

```
1. Research     → Search YouTube + fetch transcripts on the target topic
2. Analyze      → Claude reads transcripts and produces a decision report
3. Design       → Draft the SKILL.md based on approved report
4. Register     → Save skill to repo, ready for use
```

Always run the stages in order. Do not skip the report stage — it is the decision gate.

---

## Stage 1: Research

### Step 1a — Understand the target skill topic
Ask the user:
- What capability should this skill give Claude?
- Are there specific YouTube channels or videos they want included?
- Any channels that are authoritative on this topic?

### Step 1b — YouTube Search
Use the `scripts/yt_search.py` script to search YouTube for top videos on the topic:

```bash
python scripts/yt_search.py --query "<topic>" --max-results 10
```

This returns a list of video IDs and titles. Present them to the user and let them add/remove any before proceeding.

### Step 1c — Fetch Transcripts
Use the `scripts/fetch_transcripts.py` script to fetch transcripts for the approved video list:

```bash
python scripts/fetch_transcripts.py --video-ids <id1> <id2> ... --output skills/<skill-name>/research/
```

Transcripts are saved as `<video-id>.txt` in the research directory.

---

## Stage 2: Analysis & Report

Read all transcripts and produce a structured report saved to `skills/<skill-name>/research-report.md`.

### Report Structure

```markdown
# Research Report: <Skill Topic>

## Executive Summary
2-3 sentences on what the research found.

## Key Use Cases Identified
List of use cases found across the transcripts, with frequency/emphasis.

## What Should Be Built
For each recommended capability: what it is, why it's valuable, how complex to implement.

## What Should NOT Be Built
Capabilities that are out of scope, too complex, or not worth automating.

## Recommended Skill Design
- Skill name
- Trigger phrases and contexts
- Core workflow steps
- Expected inputs/outputs

## Sources
List of videos analyzed with titles and channel names.
```

**Present the report to the user and get explicit approval before proceeding to Stage 3.**

---

## Stage 3: Skill Design & Authoring

Based on the approved report, write the `SKILL.md` for the new skill.

### SKILL.md Requirements

Follow the standard format:

```markdown
---
name: <skill-name>
description: <when to trigger + what it does — be specific and slightly pushy>
---

# <Skill Title>

<Brief intro: what this skill does and why it exists>

## Workflow

### Step 1 — ...
### Step 2 — ...

## Inputs
...

## Outputs
...

## Notes & Edge Cases
...
```

### Quality Checklist
- [ ] Description clearly states WHEN to trigger (not just what it does)
- [ ] Workflow steps are concrete and actionable
- [ ] Inputs and outputs are defined
- [ ] Edge cases are noted
- [ ] Under 500 lines (if longer, split into reference files)

---

## Stage 4: Registration

Save the skill to the repo:

```bash
# Skill directory already created during research stage
# Confirm SKILL.md is at: skills/<skill-name>/SKILL.md

# Commit to GitHub
git add skills/<skill-name>/
git commit -m "feat: add <skill-name> skill"
git push
```

Confirm to the user:
- Where the skill lives
- How to trigger it
- Any dependencies or setup needed

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scripts/yt_search.py` | Search YouTube for videos on a topic |
| `scripts/fetch_transcripts.py` | Fetch transcripts for given video IDs |

See each script for usage flags and options.

---

## Notes

- Always save raw transcripts — they're useful for future research on related skills.
- If a transcript is unavailable (disabled by channel), note it in the report and skip.
- The report is the most important artifact. A bad report leads to a bad skill. Take time here.
- When in doubt about scope, build narrower and add more later.
