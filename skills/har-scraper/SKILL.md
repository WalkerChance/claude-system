---
name: har-scraper
description: >
  Build a production-ready Python scraper for any modern JavaScript-heavy website
  using HAR file analysis to reverse-engineer the site's network format. Use this
  skill whenever the user wants to scrape a site that uses Next.js, React, or other
  JS frameworks where standard requests.get() returns empty data. Also trigger when
  the user mentions HAR files, RSC streams, network traffic analysis, or wants to
  extract structured data from a site that blocks naive scraping. Works for any
  data source — game data, fantasy sports, e-commerce, APIs behind JS rendering, etc.
  Covers the full pipeline: HAR capture → format analysis → schema mapping →
  scraper generation → output validation → SQL/JSON export.
---

# HAR-Based Web Scraper Skill

A skill for building reliable Python scrapers for modern JS-heavy websites by
reverse-engineering their network traffic using HAR files.

## When to Use This Skill

Trigger this skill when:
- `requests.get()` returns a skeleton page with no real data
- The site uses Next.js, Nuxt, SvelteKit, or similar SSR/RSC frameworks
- The user mentions "the site uses React" or "data doesn't load without JS"
- The user wants to scrape game data, sports stats, product listings, or any
  structured data from a JS-rendered page
- The user uploads `.har` files and asks for data extraction help

---

## Pipeline Overview

The full pipeline has 5 steps. Each step has its own sub-skill reference file.
You can run them end-to-end or jump in at any step.

```
Step 1: CAPTURE    → Get HAR files from target URLs
Step 2: ANALYZE    → Reverse-engineer the network format
Step 3: MAP SCHEMA → Align scraped keys to target DB schema
Step 4: BUILD      → Generate the Python scraper script
Step 5: VALIDATE   → Test scraper against HAR files + run SQL
```

**Sub-skill files** (read the relevant one before starting each step):
- `references/01-capture.md`   — HAR capture (Playwright auto + manual fallback)
- `references/02-analyze.md`   — HAR analysis and format detection
- `references/03-schema.md`    — Schema interview and key mapping
- `references/04-build.md`     — Scraper generation patterns and templates
- `references/05-validate.md`  — Validation, SQL generation, and DB import

---

## How to Start

### Full pipeline (new project)
User says something like: *"I want to scrape [site] for [data]"*

1. Read `references/01-capture.md` and run HAR capture
2. Read `references/02-analyze.md` and analyze the HAR output
3. Read `references/03-schema.md` and interview user about target schema
4. Read `references/04-build.md` and generate the scraper
5. Read `references/05-validate.md` and validate + produce final output

### Jump-in (user already has HARs)
User uploads `.har` files directly → skip to Step 2.

### Jump-in (user has scraper, needs SQL)
User has working scraper and JSON output → skip to Step 5.

### Patch update (existing scraper, new data)
User says *"new patch dropped, re-run the scraper"* → go straight to Step 4,
reuse existing schema, run with new `--patch` flag.

---

## Project State Tracking

At the start of each step, summarize what you know:

```
Project:     [name]
Target URL:  [base URL]
Data goal:   [what we're extracting]
Format:      [detected: full-html / rsc-array / rsc-tprefix / unknown]
Schema:      [target DB / file format]
Step:        [current step]
```

Update this summary at the end of each step before moving to the next.

---

## Key Principles

1. **HAR files are ground truth.** Never guess at network behavior — always
   confirm with actual captured traffic before writing parsing code.

2. **Test with known items first.** Before running a full scrape, validate the
   parser against 3–5 HAR files covering different response formats.

3. **Print unmapped keys.** Every scraper must report unknown field names so
   gaps are visible immediately: `Unmapped keys: ['_unknown_XYZ']`

4. **Idempotent SQL.** All DB output uses `ON CONFLICT ... DO UPDATE SET`,
   never raw `INSERT`. Hand-curated fields are always excluded from UPDATE.

5. **Encoding safety.** Always apply `fix_encoding()` to scraped text to handle
   latin-1/UTF-8 mojibake from streaming responses.

6. **Never hardcode site structure.** Comments must explain *why* a pattern
   exists (e.g., "T-prefix is Next.js RSC binary protocol") so future maintainers
   can diagnose breakage when the site updates.
