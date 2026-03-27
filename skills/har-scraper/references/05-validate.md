# Sub-Skill 05: Validate Output

Test the generated scraper against HAR files, verify output quality,
and produce the final DB-ready SQL file.

---

## Goal
Confirm before any DB import:
- Zero empty stat/field records
- Zero missing required fields (icons, costs, etc.)
- Zero encoding issues
- Zero unmapped field keys
- SQL type casts match actual column types

---

## Step 5A: HAR-Based Unit Tests

Before running the full live scrape, test the parser against all captured
HAR files. This catches format issues without hitting the network.

```python
# validate_hars.py
import json, sys
sys.path.insert(0, ".")
from [name]_scraper import extract_item_from_page, build_db_row

TESTS = [
    # (har_file, url, expected_name)
    ("item1.har", "https://example.com/item/item-1", "Item One"),
    ("item2.har", "https://example.com/item/item-2", "Item Two"),
    # Add all captured HAR files
]

all_unknown = {}
for har_file, url, name in TESTS:
    with open(har_file) as f:
        har = json.load(f)
    for entry in har["log"]["entries"]:
        content = entry["response"]["content"].get("text", "")
        if len(content) < 1000 or "TARGET_KEYWORD" not in content:
            continue
        raw = extract_item_from_page(content, name, url)
        row = build_db_row(raw, "TEST")

        unknown = row.get("_unknown_stats", row.get("_unknown_fields", {}))
        ok      = "✓" if row.get("cost", 0) > 0 and row.get("stats", "{}") != "{}" else "✗"
        icon_ok = "✓" if row.get("icon_url") else "✗ MISSING"

        print(f"{ok} {name}")
        print(f"   fields: {row.get('stats') or row.get('data')}")
        print(f"   cost={row.get('cost')}  icon={icon_ok}  unknown={unknown}")
        if unknown:
            all_unknown[name] = unknown
        break

print()
if all_unknown:
    print("UNMAPPED KEYS — add to FIELD_MAP:")
    for item, keys in all_unknown.items():
        print(f"  {item}: {list(keys.keys())}")
else:
    print("ALL FIELDS MAPPED CLEANLY ✓")
```

**Pass criteria:** Every item shows `✓`, zero unmapped keys, icon present.

---

## Step 5B: Full Output Quality Check

After the production scrape produces `data.json`, run this analysis:

```python
# quality_check.py
import json
from collections import Counter

with open("data.json") as f:
    items = json.load(f)

print(f"Total items: {len(items)}")

# Core checks
empty_data   = [i for i in items if not i.get("stats") or i["stats"] == "{}"]
empty_icon   = [i for i in items if not i.get("icon_url")]
zero_cost    = [i for i in items if not i.get("cost") or i["cost"] == 0]
bad_encoding = [i for i in items if "â" in str(i.get("description", ""))]

print(f"Empty data:        {len(empty_data)}")
print(f"Missing icon_url:  {len(empty_icon)}")
print(f"Zero cost:         {len(zero_cost)}")
print(f"Encoding issues:   {len(bad_encoding)}")

# Field key coverage
all_keys = set()
for item in items:
    try:
        all_keys.update(json.loads(item.get("stats", "{}")).keys())
    except Exception:
        pass
print(f"\nField keys found: {sorted(all_keys)}")

# Scaling/type breakdown (if applicable)
if any("scaling_type" in i for i in items):
    scaling = Counter(str(i.get("scaling_type")) for i in items)
    print(f"\nScaling types: {dict(scaling)}")

# Flag problem items
for label, lst in [
    ("Empty data", empty_data),
    ("Missing icon", empty_icon),
    ("Bad encoding", bad_encoding),
]:
    if lst:
        print(f"\n{label}:")
        for i in lst[:5]:
            print(f"  {i.get('name')}")
```

**Pass criteria:** All counts = 0.

---

## Step 5C: SQL Type Verification

Before running SQL against the DB, verify column types match:

### Checklist
- [ ] `text[]` columns use `ARRAY[...]::text[]` or `ARRAY[]::text[]`
- [ ] `jsonb` columns use `'...'::jsonb`
- [ ] `integer` columns are bare numbers (no quotes)
- [ ] `timestamptz` columns use `'...'::timestamptz`
- [ ] `boolean` columns use `TRUE` / `FALSE` (not `'true'`/`'false'`)
- [ ] `ON CONFLICT` column matches an actual UNIQUE constraint in the DB
- [ ] Protected fields are absent from `DO UPDATE SET`

### Common errors and fixes:

```
ERROR: column "roles" is of type text[] but expression is of type jsonb
Fix: Change '[]'::jsonb → ARRAY[]::text[]

ERROR: column "cooldown" is of type integer but expression is of type text
Fix: Change '60' → 60

ERROR: there is no unique constraint matching ON CONFLICT specification
Fix: Add constraint or change conflict column to match existing one:
  ALTER TABLE [table] ADD CONSTRAINT [table]_name_unique UNIQUE (name);
```

---

## Step 5D: Incremental DB Import Strategy

For large datasets or when updating existing data:

### Option A: Direct SQL execution (Supabase SQL editor)
Paste `data_[version].sql` into the Supabase SQL editor and run.
Works for up to ~500 rows. Above that, split into batches.

### Option B: Split into batches
```python
# split_sql.py
with open("data_OB31.sql") as f:
    content = f.read()

# Split on INSERT statements
statements = content.split("\nINSERT INTO")
statements = ["INSERT INTO" + s for s in statements[1:]]

batch_size = 50
for i in range(0, len(statements), batch_size):
    batch = statements[i:i+batch_size]
    fname = f"batch_{i//batch_size + 1:03d}.sql"
    with open(fname, "w") as f:
        f.write("\n".join(batch))
    print(f"Written: {fname} ({len(batch)} rows)")
```

### Option C: Supabase Python client
```python
from supabase import create_client
import json

client = create_client(SUPABASE_URL, SUPABASE_KEY)

with open("data.json") as f:
    items = json.load(f)

# Upsert in batches of 50
for i in range(0, len(items), 50):
    batch = items[i:i+50]
    result = client.table("[table]").upsert(batch, on_conflict="name").execute()
    print(f"Upserted rows {i}–{i+len(batch)}")
```

---

## Step 5E: Patch Update Workflow

When a new patch drops and you need to refresh the data:

1. **Test first** — run with `--limit 5 --skip 10` and verify output looks right
2. **Check for new fields** — `Unmapped keys: []` must stay empty; new keys = patch change
3. **Check for stat changes** — cross-reference 2–3 known items against patch notes
4. **Run full scrape** — `--patch [new_version] --output data.json --sql data_[version].sql`
5. **Quality check** — run `quality_check.py` on new output
6. **Import SQL** — run against DB; `build_order_note` and curated fields are preserved

### Detecting site structure changes
If scraper suddenly returns 0 items or all empty stats, the site may have
updated its structure. Run a quick diagnostic:

```bash
# Capture a fresh HAR for one item and re-analyze
python har_capture.py  # capture 1-2 items
python find_data_response.py new_item.har
```

Compare the format to what the scraper expects. If the FAQPage structure
changed, update `extract_item_from_page()` accordingly.

---

## Step 5F: Final Deliverable Checklist

Before closing the scraping session:

- [ ] `[name]_scraper.py` — final scraper, all formats handled
- [ ] `data.json` — clean output, all quality checks passed
- [ ] `data_[version].sql` — DB-ready UPSERT SQL
- [ ] Quality check output showing all zeros
- [ ] Run command documented in script docstring
- [ ] Any new unmapped keys added to FIELD_MAP
- [ ] Any patch-specific stat changes noted in comments
