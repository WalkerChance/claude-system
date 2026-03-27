---
name: playwright-screenshot-automation
description: Capture screenshots of web pages using Python and Playwright. Use this skill any time the user says "take a screenshot of", "capture a webpage", "screenshot this URL", "full page screenshot", "screenshot this element", "batch screenshot", "save webpage as image", or "automate screenshots". Handles single URLs, batch lists, and element-level captures. Always use this skill for any web screenshot or page capture request.
---

# Playwright Screenshot Automation

Automates browser-based screenshot capture using Python Playwright. Supports single pages, full-page captures, element-level screenshots, and batch URL processing with error handling.

## Dependencies

```bash
pip install playwright
playwright install chromium
```

---

## Workflow

### Step 1 — Clarify the request

Ask the user (if not already specified):
- **URL(s)**: Single URL or a list?
- **Capture type**: Full page, visible viewport only, or a specific element?
- **Output directory**: Where to save? (default: `./screenshots`)
- **Headless**: Run silently in background? (default: yes)

If the user provides enough context, skip asking and proceed.

---

### Step 2 — Write the script

Generate a Python script based on the request. Use the templates below.

#### Single page screenshot

```python
from playwright.sync_api import sync_playwright
from datetime import datetime
import os

url = "https://example.com"
output_dir = "./screenshots"
full_page = False  # set True for full-page capture
headless = True
viewport = {"width": 1280, "height": 720}

os.makedirs(output_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{output_dir}/{timestamp}_screenshot.png"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=headless)
    page = browser.new_page(viewport=viewport)
    page.goto(url, wait_until="networkidle", timeout=30000)
    page.screenshot(path=filename, full_page=full_page)
    browser.close()

print(f"Saved: {filename}")
```

#### Element-specific screenshot

```python
from playwright.sync_api import sync_playwright
from datetime import datetime
import os

url = "https://example.com"
selector = "h1"  # CSS or XPath selector
output_dir = "./screenshots"

os.makedirs(output_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"{output_dir}/{timestamp}_element.png"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="networkidle", timeout=30000)
    element = page.locator(selector)
    element.screenshot(path=filename)
    browser.close()

print(f"Saved: {filename}")
```

#### Batch URL processing

```python
from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import re

urls = [
    "https://example.com",
    "https://example.org",
]
output_dir = "./screenshots"
full_page = True

def safe_filename(url):
    return re.sub(r"[^a-z0-9]", "_", url.lower())[:60]

os.makedirs(output_dir, exist_ok=True)
results = {"success": [], "failed": []}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 720})

    for url in urls:
        try:
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{output_dir}/{timestamp}_{safe_filename(url)}.png"
            page.screenshot(path=filename, full_page=full_page)
            page.close()
            results["success"].append({"url": url, "file": filename})
            print(f"✓ {url} → {filename}")
        except Exception as e:
            results["failed"].append({"url": url, "error": str(e)})
            print(f"✗ {url}: {e}")

    context.close()
    browser.close()

print(f"\nDone: {len(results['success'])} captured, {len(results['failed'])} failed")
if results["failed"]:
    print("Failed:")
    for f in results["failed"]:
        print(f"  {f['url']}: {f['error']}")
```

---

### Step 3 — Run it

Save the script and run:

```bash
python screenshot.py
```

If `playwright install chromium` hasn't been run yet, do it first.

---

### Step 4 — Confirm output

Report back:
- Files saved and their paths
- Any failed URLs and why
- Total count

---

## Notes & Edge Cases

- **networkidle vs load**: Use `networkidle` for SPAs and dynamic content. Use `"load"` for faster captures on static pages.
- **Viewport matters**: Default 1280×720. For mobile-style captures, use `{"width": 390, "height": 844}`.
- **Timestamp naming**: Always use timestamps in filenames — re-running will otherwise overwrite previous captures.
- **Authentication**: Pages behind login walls require session cookies or manual login steps before screenshotting. Ask the user if the page requires auth.
- **Timeouts**: Default 30s. Increase for slow pages, decrease for batch jobs where speed matters.
- **Browser contexts**: For batch jobs, reuse one context across pages rather than launching a new browser per URL — faster and less memory-intensive.
- **Format**: Default is PNG. For JPEG with compression: `page.screenshot(path="out.jpg", type="jpeg", quality=80)`.
