from playwright.sync_api import sync_playwright
import os
import sys

TARGET_URL = os.environ.get("TARGET_URL", "")
SITE_USER  = os.environ.get("SITE_USER", "")
SITE_PASS  = os.environ.get("SITE_PASS", "")

if not TARGET_URL:
    print("ERROR: TARGET_URL secret is not set.")
    sys.exit(1)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # ── Optional: log in first ──────────────────────────────────────
        # Uncomment and update selectors below if your site requires login
        #
        # page.goto("https://example.com/login")
        # page.fill("#username", SITE_USER)
        # page.fill("#password", SITE_PASS)
        # page.click("button[type=submit]")
        # page.wait_for_load_state("networkidle")
        # ────────────────────────────────────────────────────────────────

        print(f"Navigating to {TARGET_URL}")
        page.goto(TARGET_URL)
        page.wait_for_load_state("networkidle")

        # ── Replace selectors below with your actual button selectors ───
        # Right-click button in Chrome → Inspect → right-click element
        # → Copy → Copy selector → paste here
        #
        # Examples:
        #   page.click("button#submit-btn")
        #   page.click("text=Confirm")
        #   page.click(".btn-primary")

        page.click("button#your-button-id")   # <-- change this
        print("Clicked button 1")
        page.wait_for_timeout(1500)

        # page.click("button#second-button")   # add more clicks here
        # print("Clicked button 2")

        browser.close()
        print("Done — all buttons clicked successfully.")

if __name__ == "__main__":
    run()
