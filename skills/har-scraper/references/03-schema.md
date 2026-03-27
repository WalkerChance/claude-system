# Sub-Skill 03: Schema Mapping

Interview the user about their target schema and build the field mapping
between scraped data keys and database/output columns.

---

## Goal
Produce:
1. A confirmed target schema (column names, types, constraints)
2. A complete field mapping from scraped keys → target columns
3. A list of fields that need special handling (enums, type inference, etc.)

---

## Step 3A: Schema Interview

Ask the user these questions. Adapt based on context — if this is a returning
project (e.g. ORACLE patch update), skip questions already answered.

### Required questions:

**Q1 — Output format:**
> What's the target for the scraped data?
> - Supabase / PostgreSQL table
> - SQLite
> - JSON file only (no DB)
> - CSV
> - Other

**Q2 — Existing schema:**
> Do you have an existing table/schema I should match, or are we designing
> it from scratch?
> If existing: share the CREATE TABLE SQL, a column list, or a CSV export.

**Q3 — Conflict / upsert strategy:**
> If a record already exists, should we:
> - Update it (upsert on a unique key)
> - Skip it (insert-if-not-exists)
> - Replace it (delete + insert)
>
> If upsert: which column(s) are the unique conflict key?

**Q4 — Protected fields:**
> Are there any columns that should NEVER be overwritten by the scraper?
> (e.g. hand-curated notes, manual classifications, user-generated content)

**Q5 — Array / JSON columns:**
> Do any columns store arrays or JSON? If so, what PostgreSQL type are they?
> (text[], jsonb, json — matters for SQL casting)

### Optional questions (ask if relevant):

**Q6 — Enum / controlled vocabulary:**
> Are any columns restricted to a fixed set of values?
> (e.g. scaling_type = STR/INT/BOTH/Defense)

**Q7 — Inferred fields:**
> Are there fields that should be computed from the scraped data rather
> than scraped directly?
> (e.g. scaling_type inferred from which stat keys are present)

---

## Step 3B: Build the Field Mapping

Once you understand the schema, map scraped field names → target column names.

### Mapping table format:
```
| Scraped Key         | Target Column    | Type     | Notes                        |
|---------------------|-----------------|----------|------------------------------|
| PhysicalPower       | stats.str       | jsonb    | Nested in stats JSON         |
| MagicalPower        | stats.int       | jsonb    | Nested in stats JSON         |
| MaxHealth           | stats.hp        | jsonb    | Nested in stats JSON         |
| totalGoldCost       | cost            | integer  | Direct mapping               |
| imagePath           | icon_url        | text     | Prepend CDN base URL         |
| [computed]          | scaling_type    | text     | Inferred from stats keys     |
| [not scraped]       | build_order_note| text     | PROTECTED — never overwrite  |
```

### Key mapping patterns:

**Direct mapping** — scraped key → column, same value:
```python
"cost": row["totalGoldCost"]
```

**Renamed key** — scraped name differs from column name:
```python
"icon_url": CDN_BASE + "/" + row["imagePath"]
```

**Nested / transformed** — scraped value needs processing:
```python
"stats": json.dumps(normalize_stats(row["raw_stats"]))
```

**Inferred / computed** — not scraped, derived from other fields:
```python
"scaling_type": infer_scaling(row["stats"])
```

**Protected** — never written by scraper:
```python
# build_order_note — excluded from DO UPDATE SET
```

**Empty default** — scraper can't populate this, user fills it:
```python
"good_for_roles": "ARRAY[]::text[]"
```

---

## Step 3C: Handle Type Mismatches

Common SQL type issues to resolve before Step 4:

### text[] vs jsonb arrays
```sql
-- WRONG: '[]'::jsonb  (if column is text[])
-- RIGHT: ARRAY[]::text[]

-- WRONG: '["Solo","Mid"]'::jsonb  (if column is text[])
-- RIGHT: ARRAY['Solo','Mid']::text[]
```

### jsonb stats column
```sql
-- Always cast stats dict to jsonb:
'{"str": 40, "cdr": 10}'::jsonb
```

### integer vs text for cooldowns
```sql
-- active_cooldown should be integer, not text:
-- WRONG: '60'   RIGHT: 60
```

### timestamptz
```sql
-- Always cast ISO timestamps:
'2026-03-01T12:00:00+00:00'::timestamptz
```

---

## Step 3D: Document the Stat/Key Mapping (if applicable)

If the site uses verbose or inconsistent field names (like SmiteSource's
PascalCase stat names), build a complete key mapping dict:

```python
FIELD_MAP = {
    # Scraped name       : target column key
    "PhysicalPower"      : "str",
    "MagicalPower"       : "int",
    "MaxHealth"          : "hp",
    "PhysicalProtection" : "phys_prot",
    "MagicalProtection"  : "mag_prot",
    "MaxMana"            : "mana",
    "ManaPerTime"        : "mp5",
    "HealthPerTime"      : "hp5",
    "AttackSpeedPercent" : "attack_speed",
    "MovementSpeedPercent": "move_speed",
    "CooldownReductionPercent": "cdr",
    "LifeStealPercent"   : "lifesteal",
    "CritChance"         : "crit_chance",
    "CCR"                : "ccr",
    # Add as discovered during test runs — scraper will print unmapped keys
}
```

**Process for building this map:**
1. Start with the keys visible in your HAR files
2. Run a test scrape — any unmapped keys print as `_unknown_KeyName`
3. Add them to the map
4. Repeat until `Unmapped keys: []`

---

## Step 3E: Output of This Step

Before moving to Step 4, confirm you have:

```
## Schema Mapping Summary

Target:          [Supabase table / file format]
Conflict key:    [column(s) for ON CONFLICT]
Protected fields: [list — never overwritten]
Array columns:   [name: type for each]
JSON columns:    [name: type for each]

Field mapping:   [complete table from 3B]
Key map:         [FIELD_MAP dict if needed]
Inferred fields: [list with inference logic]
```
