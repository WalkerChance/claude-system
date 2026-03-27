# Sub-Skill 02: HAR Analysis

Analyze captured HAR files to reverse-engineer how the target site delivers
its data and identify the correct extraction strategy.

---

## Goal
Determine:
1. Which response(s) in the HAR contain the target data
2. What format that data is in
3. Where specifically the data lives within that format
4. What request headers are needed to reliably trigger data-bearing responses

---

## Step 2A: Find the Data-Bearing Response

For each HAR file, scan all responses for content that looks like target data:

```python
# find_data_response.py
import json, sys

def scan_har(har_file: str, keywords: list[str]):
    """Find responses containing target keywords."""
    with open(har_file) as f:
        har = json.load(f)

    print(f"\n=== {har_file} ===")
    for i, entry in enumerate(har["log"]["entries"]):
        url      = entry["request"]["url"]
        status   = entry["response"]["status"]
        mime     = entry["response"]["content"].get("mimeType", "")
        text     = entry["response"]["content"].get("text", "")
        hit      = any(kw.lower() in text.lower() for kw in keywords)

        if hit and len(text) > 500:
            print(f"\n[{i}] MATCH ({status} {mime})")
            print(f"  URL: {url[:100]}")
            print(f"  Size: {len(text)} chars")
            # Show a snippet around the first keyword hit
            for kw in keywords:
                idx = text.lower().find(kw.lower())
                if idx >= 0:
                    print(f"  Context [{kw}]: ...{text[max(0,idx-50):idx+150]}...")
                    break

# ── Configure ─────────────────────────────────────────────────────────────────
# Replace with terms you expect to find in the target data
KEYWORDS = ["FAQPage", "PhysicalPower", "stats", "cost", "gold"]

for f in sys.argv[1:]:
    scan_har(f, KEYWORDS)
```

Run as: `python find_data_response.py *.har`

---

## Step 2B: Identify the Response Format

Once you find the data-bearing response, identify which of these formats it uses:

### Format A — Full HTML with JSON-LD
```html
<script type="application/ld+json">{"@type": "SomeSchema", ...}</script>
```
**Indicators:**
- MIME type: `text/html`
- Contains `application/ld+json` script tags
- Data is in a schema.org or similar structured block

**Extraction:** Parse `<script type="application/ld+json">` tags with BeautifulSoup
or regex, then `json.loads()` each block.

---

### Format B — RSC Stream, Array Payload (Next.js)
```
22:["$","main",null,{...,"__html":"{\"@type\":\"FAQPage\",...}"}]
```
**Indicators:**
- MIME type: `text/x-component`
- Lines follow `ID:json-payload` pattern
- Target data embedded as escaped JSON string in `__html` key

**Extraction:** Split on newlines, find lines containing target keywords,
parse line after first `:`, recursively find `__html` values, parse as JSON.

---

### Format C — RSC Stream, T-Prefix Payload (Next.js)
```
2c:T427,{"@type":"FAQPage","mainEntity":[...]}extra_data_here
```
**Indicators:**
- MIME type: `text/x-component`
- Lines match pattern `ID:T[hex],{...}`
- JSON object starts immediately after the hex prefix and comma
- Extra data appended after the closing `}` causes standard `json.loads()` to fail

**Extraction:** Strip `T[0-9a-fA-F]+,` prefix with regex, then use
balanced-brace extraction to isolate the JSON object before extra data.

---

### Format D — Standard JSON API
```json
{"items": [...], "pagination": {...}}
```
**Indicators:**
- MIME type: `application/json`
- Direct JSON response, no streaming format

**Extraction:** `json.loads()` directly.

---

### Format E — GraphQL Response
```json
{"data": {"items": [...]}, "errors": null}
```
**Indicators:**
- Request URL contains `/graphql` or request body has `query:` field
- Response is `application/json` with nested `data` key

**Extraction:** `json.loads()`, navigate to `data.[field]`.

---

## Step 2C: Map the Data Structure

Once you've found the data, document its exact structure:

```python
# map_structure.py — run this to print the data structure
import json

def explore_structure(obj, path="root", depth=0, max_depth=4):
    """Recursively print the structure of a parsed JSON object."""
    indent = "  " * depth
    if depth > max_depth:
        print(f"{indent}{path}: [truncated]")
        return
    if isinstance(obj, dict):
        print(f"{indent}{path}: dict({len(obj)} keys)")
        for k, v in list(obj.items())[:10]:  # first 10 keys
            explore_structure(v, k, depth+1, max_depth)
    elif isinstance(obj, list):
        print(f"{indent}{path}: list({len(obj)} items)")
        if obj:
            explore_structure(obj[0], "[0]", depth+1, max_depth)
    else:
        preview = str(obj)[:80]
        print(f"{indent}{path}: {type(obj).__name__} = {preview}")
```

Run this on the parsed data object to understand its shape before writing
the parser.

---

## Step 2D: Identify Request Headers Needed

Check whether data-bearing responses require specific request headers:

```python
# check_headers.py
import json

def show_request_headers(har_file: str, response_mime: str):
    with open(har_file) as f:
        har = json.load(f)
    for entry in har["log"]["entries"]:
        mime = entry["response"]["content"].get("mimeType", "")
        if response_mime in mime:
            print(f"URL: {entry['request']['url']}")
            print("Request headers:")
            for h in entry["request"]["headers"]:
                print(f"  {h['name']}: {h['value']}")
            break
```

**Common headers needed for Next.js RSC:**
```python
"RSC": "1"
"Next-Router-State-Tree": "[url-encoded state tree]"
"Next-Url": "/path/to/page"
```

If these headers are present in the data-bearing request, the scraper must
send them to reliably get RSC stream responses instead of full HTML.

---

## Step 2E: Document Your Findings

Before moving to Step 3, record these findings:

```
## HAR Analysis Results

Site:           [URL]
Data location:  [response index, URL pattern]
Format:         [A/B/C/D/E + description]
Data path:      [e.g. FAQPage > mainEntity > acceptedAnswer > text]
Required headers: [list any special headers needed]
List page:      [URL of index/listing page, if any]
Item URL pattern: [e.g. /item/{slug}]

Fields found in data:
  - [field name]: [example value]
  - [field name]: [example value]
  ...

Quirks / edge cases:
  - [anything unusual found in the HAR]
```

This document feeds directly into Step 3 (schema mapping).
