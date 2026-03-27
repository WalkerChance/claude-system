# Sub-Skill 01: HAR Capture

Capture HAR files from target URLs using Playwright automation.
Fall back to manual browser instructions if automation fails.

---

## Goal
Produce one or more `.har` files containing the full network traffic for
representative pages of the target site. These files are the input to Step 2.

---

## Step 1A: Attempt Automated Capture (Playwright)

Install Playwright if not present:
```bash
pip install playwright --break-system-packages
playwright install chromium
```

Run the capture script below, substituting the target URLs:

```python
# har_capture.py
import asyncio
from playwright.async_api import async_playwright

async def capture_har(urls: list[dict], output_dir: str = "."):
    """
    Capture HAR files for a list of URLs.

    Args:
        urls: list of {"name": "item-slug", "url": "https://..."}
        output_dir: where to save .har files
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for item in urls:
            name    = item["name"]
            url     = item["url"]
            outfile = f"{output_dir}/{name}.har"

            context = await browser.new_context(record_har_path=outfile)
            page    = await context.new_page()

            print(f"Capturing: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)  # let any lazy-loaded content settle

            await context.close()
            print(f"  Saved: {outfile}")

        await browser.close()

# ── Configure these for your project ─────────────────────────────────────────
TARGET_URLS = [
    {"name": "sample-item-1", "url": "https://example.com/item/sample-1"},
    {"name": "sample-item-2", "url": "https://example.com/item/sample-2"},
    # Add more representative URLs — aim for 3–5 covering different item types
    # (e.g. one active item, one passive, one with unusual stats)
]
OUTPUT_DIR = "."

asyncio.run(capture_har(TARGET_URLS, OUTPUT_DIR))
```

### What to capture
Choose URLs that represent the **variety** of data you expect:
- At least one "standard" item/page
- At least one with an active/on-use effect (if applicable)
- At least one with unusual or rare stats/fields
- At least one from a different category (e.g. starter vs. tier 3)

For SmiteSource specifically, good test items:
```python
TARGET_URLS = [
    {"name": "bancrofts-talon",        "url": "https://smitesource.com/item/bancrofts-talon"},
    {"name": "golden-blade",           "url": "https://smitesource.com/item/golden-blade"},
    {"name": "hide-of-the-nemean-lion","url": "https://smitesource.com/item/hide-of-the-nemean-lion"},
    {"name": "sun-beam-bow",           "url": "https://smitesource.com/item/sun-beam-bow"},
    {"name": "transcendence",          "url": "https://smitesource.com/item/transcendence"},
]
```

---

## Step 1B: Verify Capture Quality

After running, check each HAR file contains real data:

```python
# verify_hars.py
import json, glob

for har_file in glob.glob("*.har"):
    with open(har_file) as f:
        har = json.load(f)
    entries = har["log"]["entries"]
    has_data = any(
        len(e["response"]["content"].get("text", "")) > 1000
        for e in entries
    )
    response_types = set(
        e["response"]["content"].get("mimeType", "")
        for e in entries
    )
    print(f"{har_file}: {len(entries)} requests | data={has_data} | types={response_types}")
```

**Good signs:**
- `text/x-component` responses present → RSC stream format (Next.js)
- `text/html` response > 10KB → full HTML format
- At least one response > 1000 chars containing target data keywords

**Bad signs:**
- All responses < 500 chars → page blocked or JS didn't execute
- Only `text/html` with < 5KB → got a skeleton page, no data loaded
- `403` or `429` status codes → rate limited or blocked

---

## Step 1C: Manual Fallback

If Playwright capture fails (bot detection, CAPTCHA, auth required), instruct
the user to capture manually:

> The automated capture didn't work — the site likely detects headless browsers.
> Here's how to capture the HAR manually:
>
> 1. Open Chrome or Firefox
> 2. Press **F12** to open DevTools
> 3. Click the **Network** tab
> 4. Check **Preserve log** (Chrome) or **Persist Logs** (Firefox)
> 5. Navigate to: `[TARGET_URL]`
> 6. Wait for the page to fully load (all data visible)
> 7. Right-click anywhere in the Network panel → **Save all as HAR with content**
> 8. Save as `[item-name].har`
> 9. Repeat for each representative URL (aim for 3–5)
> 10. Upload the `.har` files here

**Tips to give the user:**
- Disable any browser extensions that modify requests (ad blockers, VPNs)
- If the site requires login, log in first, then capture
- For sites with infinite scroll or lazy loading, scroll to the bottom before saving

---

## Step 1D: Handle List Pages

If the target site has a listing page (e.g. `/items`, `/players`, `/products`),
capture that too — it often contains the full index of URLs to scrape:

```python
# Add the list page to your captures
{"name": "items-list", "url": "https://example.com/items"},
```

The list page HAR will be used in Step 4 to build the URL discovery logic.

---

## Output of This Step

Before moving to Step 2, confirm you have:
- [ ] 3–5 `.har` files covering representative pages
- [ ] At least one HAR with a response > 1000 chars containing target data
- [ ] (Optional) HAR of the list/index page

Hand these files to Step 2 (analyze).
