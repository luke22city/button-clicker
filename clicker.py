from playwright.sync_api import sync_playwright
import os
import sys

TARGET_URL = "https://airtable.com/appQpSxwTWUikCe3B/tblJQTbHTqHsvTJrW/viwRWbXKI0NLgC49a?blocks=bip4vA5JmA5fzprrL"
SITE_USER  = os.environ.get("SITE_USER", "")
SITE_PASS  = os.environ.get("SITE_PASS", "")

if not SITE_USER or not SITE_PASS:
    print("ERROR: SITE_USER or SITE_PASS secret is not set.")
    sys.exit(1)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Step 1: Log in to Airtable
        print("Navigating to Airtable login...")
        page.goto("https://airtable.com/login")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(2000)

        print("Entering credentials...")
        page.fill('input[name="email"]', SITE_USER)
        page.click('button[type="submit"]')
        page.wait_for_timeout(1500)

        page.fill('input[name="password"]', SITE_PASS)
        page.click('button[type="submit"]')
        print("Waiting for login to complete...")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(4000)

        # Step 2: Navigate to the target view
        print("Navigating to target view...")
        page.goto(TARGET_URL)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(5000)

        # Step 3: Find the iframe and click the Run button inside it
        print("Looking for iframe...")
        frames = page.frames
        print(f"Found {len(frames)} frames")

        run_clicked = False
        for frame in frames:
            try:
                url = frame.url
                print(f"Checking frame: {url[:80]}")
                if "airtableblocks.com" in url or "alt.airtableblocks" in url:
                    print("Found Airtable block iframe — looking for Run button...")
                    frame.wait_for_timeout(2000)
                    run_button = frame.locator('button:has-text("Run")')
                    if run_button.count() > 0:
                        run_button.first.click()
                        print("Clicked Run button!")
                        run_clicked = True
                        break
                    else:
                        print("Run button not found in this frame, trying next...")
            except Exception as e:
                print(f"Error in frame: {e}")
                continue

        if not run_clicked:
            print("Trying fallback — searching all frames for Run button...")
            for frame in page.frames:
                try:
                    btn = frame.locator('button:has-text("Run")')
                    if btn.count() > 0:
                        btn.first.click()
                        print("Clicked Run button via fallback!")
                        run_clicked = True
                        break
                except Exception:
                    continue

        if not run_clicked:
            print("ERROR: Could not find Run button in any frame.")
            browser.close()
            sys.exit(1)

        page.wait_for_timeout(2000)
        browser.close()
        print("Done — Run button clicked successfully.")

if __name__ == "__main__":
    run()
