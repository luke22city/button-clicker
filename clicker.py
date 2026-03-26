from playwright.sync_api import sync_playwright
import os
import sys
import json

TARGET_URL = "https://airtable.com/appQpSxwTWUikCe3B/tblJQTbHTqHsvTJrW/viwRWbXKI0NLgC49a?blocks=bip4vA5JmA5fzprrL"
COOKIES_JSON = os.environ.get("AIRTABLE_COOKIES", "")

if not COOKIES_JSON:
    print("ERROR: AIRTABLE_COOKIES secret is not set.")
    sys.exit(1)

# Block name, iframe URL fragment, wait time in milliseconds
BLOCKS = [
    ("Partners",        "2g6508a",  30000),
    ("User",            "pbt7bis",  60000),
    ("Licenses",        "7gc54xg",  60000),
    ("Potentials",      "24m4f0j", 120000),
    ("Quotes",          "4xq9c2h", 120000),
    ("Accounts",        "mq82ak7",  30000),
    ("CEO User Groups", "i2e5m6q",  30000),
]

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        print("Loading saved session cookies...")
        cookies = json.loads(COOKIES_JSON)
        context.add_cookies(cookies)
        print(f"Loaded {len(cookies)} cookies")

        page = context.new_page()
        page.set_default_timeout(180000)

        print("Navigating to target view...")
        page.goto(TARGET_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(8000)
        print("Page title:", page.title())

        if "login" in page.url.lower() or "verify" in page.title().lower():
            print("ERROR: Session expired. Cookies need to be refreshed.")
            browser.close()
            sys.exit(1)

        print(f"Found {len(page.frames)} frames total")

        results = []
        for block_name, url_fragment, wait_ms in BLOCKS:
            clicked = False
            for frame in page.frames:
                try:
                    if url_fragment in frame.url:
                        print(f"Found {block_name} — clicking Run, waiting {wait_ms//1000}s...")
                        frame.wait_for_timeout(2000)
                        btn = frame.locator('button:has-text("Run")')
                        if btn.count() > 0:
                            btn.first.click()
                            page.wait_for_timeout(wait_ms)
                            print(f"  ✓ {block_name} done")
                            clicked = True
                            break
                        else:
                            print(f"  ! No Run button found in {block_name}")
                except Exception as e:
                    print(f"  ! Error in {block_name}: {e}")
                    continue

            if not clicked:
                print(f"  ! Could not click {block_name}")
            results.append((block_name, clicked))

        print("\n--- Summary ---")
        all_ok = True
        for name, success in results:
            status = "SUCCESS" if success else "FAILED"
            print(f"  {status}: {name}")
            if not success:
                all_ok = False

        browser.close()

        if not all_ok:
            sys.exit(1)

        print("\nDone — all Run buttons clicked.")

if __name__ == "__main__":
    run()
