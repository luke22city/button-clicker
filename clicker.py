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
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.set_default_timeout(60000)  # 60 second timeout for all actions

        # Step 1: Log in to Airtable
        print("Navigating to Airtable login...")
        page.goto("https://airtable.com/login", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        print("Page title:", page.title())

        # Try multiple possible email field selectors
        print("Entering email...")
        for selector in ['input[name="email"]', 'input[type="email"]', 'input[placeholder*="email" i]', '#sign-in-email']:
            try:
                if page.locator(selector).count() > 0:
                    page.fill(selector, SITE_USER)
                    print(f"Filled email using selector: {selector}")
                    break
            except Exception as e:
                print(f"Selector {selector} failed: {e}")
                continue

        # Click continue/next button
        for selector in ['button[type="submit"]', 'button:has-text("Continue")', 'button:has-text("Sign in")', 'button:has-text("Next")']:
            try:
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    print(f"Clicked submit using: {selector}")
                    break
            except Exception:
                continue

        page.wait_for_timeout(2000)

        # Enter password
        print("Entering password...")
        for selector in ['input[name="password"]', 'input[type="password"]']:
            try:
                if page.locator(selector).count() > 0:
                    page.fill(selector, SITE_PASS)
                    print(f"Filled password using selector: {selector}")
                    break
            except Exception:
                continue

        # Click sign in
        for selector in ['button[type="submit"]', 'button:has-text("Sign in")', 'button:has-text("Log in")']:
            try:
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    print(f"Clicked sign in using: {selector}")
                    break
            except Exception:
                continue

        print("Waiting for login to complete...")
        page.wait_for_timeout(6000)
        print("Page after login:", page.title())

        # Step 2: Navigate to the target view
        print("Navigating to target view...")
        page.goto(TARGET_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        print("Page at target:", page.title())

        # Step 3: Find the iframe and click the Run button
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
            print("ERROR: Could not find Run button.")
            browser.close()
            sys.exit(1)

        page.wait_for_timeout(2000)
        browser.close()
        print("Done.")

if __name__ == "__main__":
    run()
