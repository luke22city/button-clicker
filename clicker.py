from playwright.sync_api import sync_playwright
import os
import sys
import json

TARGET_URL = "https://airtable.com/appQpSxwTWUikCe3B/tblJQTbHTqHsvTJrW/viwRWbXKI0NLgC49a?blocks=bip4vA5JmA5fzprrL"
COOKIES_JSON = os.environ.get("AIRTABLE_COOKIES", "")

if not COOKIES_JSON:
    print("ERROR: AIRTABLE_COOKIES secret is not set.")
    sys.exit(1)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Load saved cookies so we skip login entirely
        print("Loading saved session cookies...")
        cookies = json.loads(COOKIES_JSON)
        context.add_cookies(cookies)
        print(f"Loaded {len(cookies)} cookies")

        page = context.new_page()
        page.set_default_timeout(60000)

        # Navigate directly to the target view
        print("Navigating to target view...")
        page.goto(TARGET_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        print("Page title:", page.title())

        # Check we are actually logged in
        if "login" in page.url.lower() or "verify" in page.title().lower():
            print("ERROR: Session expired or not logged in. Cookies need to be refreshed.")
            browser.close()
            sys.exit(1)

        # Find the Airtable block iframe and click Run
        print(f"Found {len(page.frames)} frames total")

        run_clicked = False
        for frame in page.frames:
            try:
                url = frame.url
                print(f"Frame: {url[:100]}")
                if "airtableblocks.com" in url:
                    print("Found Airtable block iframe!")
                    frame.wait_for_timeout(3000)
                    btn = frame.locator('button:has-text("Run")')
                    count = btn.count()
                    print(f"Run buttons found: {count}")
                    if count > 0:
                        btn.first.click()
                        print("SUCCESS — Clicked Run button!")
                        run_clicked = True
                        break
            except Exception as e:
                print(f"Frame error: {e}")
                continue

        if not run_clicked:
            print("ERROR: Could not find Run button in any frame.")
            browser.close()
            sys.exit(1)

        page.wait_for_timeout(2000)
        browser.close()
        print("Done.")

if __name__ == "__main__":
    run()
