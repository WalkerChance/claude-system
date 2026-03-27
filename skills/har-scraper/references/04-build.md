# Sub-Skill 04: Build Scraper

Generate the Python scraper script using the patterns established from
HAR analysis and schema mapping.

---

## Goal
Produce a complete, working `[project]_scraper.py` that:
- Handles all detected response formats
- Maps all scraped fields to target schema
- Prints unmapped keys for debugging
- Outputs clean JSON and/or SQL
- Is idempotent (safe to re-run on each data update)

---

## Step 4A: Scraper Structure

Every generated scraper follows this structure:

```python
"""
[Project] Scraper
=================
[Brief description of what this scrapes and why standard requests fail]

Strategy:
  1. GET [list URL] -> extract item list
  2. For each item, GET its page -> parse [format] for data
  3. Output rows matching [schema name]

Requirements: pip install requests beautifulsoup4
Usage:
  python [name]_scraper.py --patch [version] --output data.json
  python [name]_scraper.py --patch [version] --limit 5     (test)
  python [name]_scraper.py --patch [version] --skip 10     (skip cheap/bad items)
"""

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL   = "[base]"
LIST_URL   = "[list page]"
CDN_BASE   = "[cdn base if applicable]"
HEADERS    = { ... }           # Standard browser headers
RSC_HEADERS = { ... }          # Special headers if needed (Next.js etc.)
REQUEST_DELAY = 0.6            # Polite delay between requests

# ── Field Map ─────────────────────────────────────────────────────────────────
FIELD_MAP = { ... }            # Scraped key → DB column key

# ── Core Functions ────────────────────────────────────────────────────────────
def fix_encoding(text)         # UTF-8 mojibake fix
def fetch_page(url, ...)       # HTTP GET with retries + RSC headers
def get_item_list(html, ...)   # Extract URLs from list page
def find_html_values(obj, ...) # Recursively find __html values (RSC)
def parse_data(response, ...)  # Format-specific extraction
def normalize_fields(raw, ...) # Map scraped keys → DB keys
def build_db_row(raw, ...)     # Assemble complete DB row
def scrape_items(...)          # Main scrape loop
def to_db_rows(items)          # Strip debug fields
def to_sql(items, ...)         # Generate UPSERT SQL
def main()                     # CLI entry point
```

---

## Step 4B: Format-Specific Parser Templates

Use the appropriate template based on Step 2 findings.

### Template A — Full HTML JSON-LD
```python
def parse_data(content: str, item_name: str, item_url: str) -> dict:
    result = {"name": item_name, "source_url": item_url, "raw_fields": {}}

    ld_scripts = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        content, re.DOTALL | re.IGNORECASE
    )
    for script_text in ld_scripts:
        try:
            data = json.loads(script_text.strip())
        except (json.JSONDecodeError, ValueError):
            continue
        if data.get("@type") == "TARGET_SCHEMA_TYPE":
            extract_fields(data, result)
            break

    return result
```

### Template B — RSC Stream Array Payload
```python
def find_html_values(obj, results=None):
    if results is None: results = []
    if isinstance(obj, dict):
        if "__html" in obj: results.append(obj["__html"])
        for v in obj.values(): find_html_values(v, results)
    elif isinstance(obj, list):
        for item in obj: find_html_values(item, results)
    return results

def parse_data(content: str, item_name: str, item_url: str) -> dict:
    result = {"name": item_name, "source_url": item_url, "raw_fields": {}}

    for line in content.split("\n"):
        if not line.strip() or "TARGET_KEYWORD" not in line: continue
        colon_idx = line.find(":")
        if colon_idx < 0: continue
        payload = line[colon_idx + 1:]
        try:
            parsed = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            continue
        for html_val in find_html_values(parsed):
            if "TARGET_KEYWORD" not in html_val: continue
            try:
                data = json.loads(html_val)
                extract_fields(data, result)
                break
            except (json.JSONDecodeError, ValueError):
                continue
        if result["raw_fields"]: break

    return result
```

### Template C — RSC Stream T-Prefix Payload
```python
def parse_data(content: str, item_name: str, item_url: str) -> dict:
    result = {"name": item_name, "source_url": item_url, "raw_fields": {}}

    for line in content.split("\n"):
        if not line.strip() or "TARGET_KEYWORD" not in line: continue
        colon_idx = line.find(":")
        if colon_idx < 0: continue
        payload = line[colon_idx + 1:]

        # Strip T<hex-length>, prefix (Next.js RSC binary protocol)
        t_match = re.match(r"^T[0-9a-fA-F]+,", payload)
        if t_match:
            payload = payload[t_match.end():]

        if payload.startswith("{") and "TARGET_KEYWORD" in payload:
            # Balanced-brace extraction — extra data may follow the closing }
            depth, end = 0, 0
            for i, c in enumerate(payload):
                if c == "{": depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            try:
                data = json.loads(payload[:end])
                extract_fields(data, result)
                break
            except (json.JSONDecodeError, ValueError):
                pass

    return result
```

### Combined template (handles all three — recommended)
When the site might return different formats for different pages, combine all
three into a single `parse_data()` with Method 1/2/3 fallback. See the
SmiteSource scraper (`smitesource_scraper.py`) as the reference implementation.

---

## Step 4C: Field Normalization Template

```python
def normalize_fields(raw_fields: dict, description: str = "") -> dict:
    """Map scraped field names → DB column keys. Print unknowns for debugging."""
    result  = {}
    for key, value in raw_fields.items():
        db_key = FIELD_MAP.get(key)
        if db_key:
            result[db_key] = value
        else:
            result[f"_unknown_{key}"] = value  # flagged for review

    # Fallback: parse certain fields from description text if not in raw
    # Example: stats_item_percent from "+7.5% of all Stats from Items"
    # if "target_field" not in result:
    #     match = re.search(r"pattern", description)
    #     if match: result["target_field"] = match.group(1)

    return result
```

---

## Step 4D: SQL Generator Template

```python
def to_sql(items: list, patch_version: str) -> str:
    lines = [
        f"-- [Project] Data - {patch_version}",
        f"-- Generated: {datetime.now().strftime('%Y-%m-%d')}",
        f"-- Total rows: {len(items)}",
        f"-- Strategy: upsert on [conflict_key]; [protected_field] never overwritten",
        "",
    ]

    for item in items:
        def esc(s):
            if s is None: return "NULL"
            return "'" + str(s).replace("'", "''") + "'"

        def esc_int(v):
            return str(int(v)) if v is not None else "NULL"

        def esc_bool(v):
            return "TRUE" if v else "FALSE"

        def esc_array(v):
            """Emit text[] literal from list or '[]' string."""
            if not v or v in ("[]", "", None): return "ARRAY[]::text[]"
            lst = json.loads(v) if isinstance(v, str) else v
            return "ARRAY[" + ",".join(f"'{x}'" for x in lst) + "]::text[]"

        lines.append(f"""INSERT INTO [table] (
  [column_list]
) VALUES (
  [value_list]
)
ON CONFLICT ([conflict_key]) DO UPDATE SET
  [update_list];
  -- [protected_field] intentionally excluded (preserve existing data)
""")

    lines.append(f"-- {len(items)} rows upserted")
    return "\n".join(lines)
```

---

## Step 4E: CLI Interface Template

Every scraper gets these standard arguments:

```python
parser.add_argument("--output",    default="data.json",  help="Output JSON file")
parser.add_argument("--sql",       default="",           help="Also output SQL file")
parser.add_argument("--patch",     default="Unknown",    help="Version label e.g. OB30")
parser.add_argument("--limit",     type=int, default=None, help="Scrape first N items (testing)")
parser.add_argument("--skip",      type=int, default=0,    help="Skip first N items")
parser.add_argument("--all-tiers", action="store_true",  help="Include all item tiers")
```

---

## Step 4F: Required Debug Output

Every scraper must emit this during a run so problems are immediately visible:

```
Step 1: Fetching item list from [URL]...
  Found [N] total items
  Filtered to [N] likely target items

Step 2: Scraping [N] item pages (~[N]s)...
  [  1/132] Item Name
    -> Raw fields:   {'FieldA': 40, 'FieldB': 10}
    -> DB fields:    {"col_a": 40, "col_b": 10}
    -> Cost:         2500
    -> Icon:         https://...
  [  2/132] ...

Post-filter removed [N] items with [reason]

Done! [N] items scraped, [N] failed.

Unmapped field keys: ['_unknown_NewField']   ← ALWAYS print this
Add these to FIELD_MAP if needed.
```

---

## Step 4G: Encoding Safety

Always include and apply `fix_encoding()`:

```python
def fix_encoding(text: str) -> str:
    """Fix mojibake from latin-1/UTF-8 mismatch in streaming responses."""
    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
```

Apply it to all text fields extracted from RSC stream responses:
```python
result["description"] = fix_encoding(raw_text)
```

---

## Step 4H: Run Command

Always end with the standard run commands for this project:

```bash
# Full production scrape
python [name]_scraper.py --patch [version] --output data.json --sql data_[version].sql

# Test run (skip low-value items, grab 5 real ones)
python [name]_scraper.py --patch [version] --skip 10 --limit 5 --output test.json
```
