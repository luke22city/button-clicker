from playwright.sync_api import sync_playwright
import os
import sys
import json

TARGET_URL = "https://airtable.com/appQpSxwTWUikCe3B/tblJQTbHTqHsvTJrW/viwRWbXKI0NLgC49a?blocks=bip4vA5JmA5fzprrL"
COOKIES_JSON = os.environ.get("AIRTABLE_COOKIES", "")

if not COOKIES_JSON:
    print("ERROR: AIRTABLE_COOKIES secret is not set.")
    sys.exit(1)

BLOCKS = [
    ("Partners",        "2g6508a",  240000),
    ("User",            "pbt7bis",  240000),
    ("Licenses",        "7gc54xg",  240000),
    ("Potentials",      "24m4f0j",  240000),
    ("Quotes",          "4xq9c2h",  240000),
    ("Accounts",        "mq82ak7",  240000),
    ("CEO User Groups", "i2e5m6q",  240000),
]

def dismiss_transcend_overlay(page):
    """Disable the Transcend consent overlay so it doesn't intercept pointer events."""
    try:
        page.evaluate("""
            const el = document.getElementById('transcend-shadow-root');
            if (el) {
                el.style.pointerEvents = 'none';
                el.style.display = 'none';
            }
        """)
    except Exception:
        pass

def close_fullscreen(page):
    try:
        exit_btn = page.locator('[aria-label="Exit fullscreen"]')
        if exit_btn.count() > 0:
            exit_btn.first.click()
            print("  Closed fullscreen")
            page.wait_for_timeout(2000)
        else:
            page.keyboard.press("Escape")
            page.wait_for_timeout(1000)
    except Exception:
        page.keyboard.press("Escape")
        page.wait_for_timeout(1000)

def wait_for_done(frame, timeout_ms):
    """Poll the iframe content every 3 seconds until 'Done!' appears or timeout."""
    elapsed = 0
    interval = 3000
    while elapsed < timeout_ms:
        try:
            content = frame.locator('body').inner_text()
            if "Done!" in content:
                return True
        except Exception:
            pass
        frame.page.wait_for_timeout(interval)
        elapsed += interval
        print(f"  Still running... ({elapsed//1000}s elapsed)")
    return False

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

        # Suppress the Transcend overlay once after page load
        dismiss_transcend_overlay(page)

        results = []
        for block_name, url_fragment, timeout_ms in BLOCKS:
            print(f"\nProcessing {block_name}...")
            clicked = False

            try:
                # Re-suppress overlay before each block in case it re-renders
                dismiss_transcend_overlay(page)

                # Hover to reveal fullscreen button, using force=True to bypass intercept checks
                block_frame = page.locator(f'iframe[src*="{url_fragment}"]').first
                block_frame.hover(force=True)
                page.wait_for_timeout(1000)

                # Click fullscreen
                fs_button = page.locator(
                    f'iframe[src*="{url_fragment}"]'
                ).locator(
                    'xpath=ancestor::div[contains(@class,"blockFrame")]'
                ).locator('[aria-label="Enter fullscreen"]')

                if fs_button.count() > 0:
                    fs_button.click(force=True)
                    print(f"  Opened fullscreen")
                    page.wait_for_timeout(3000)
                else:
                    print(f"  Fullscreen button not found, trying anyway...")

                # Find iframe and click Run
                for frame in page.frames:
                    try:
                        if url_fragment in frame.url:
                            print(f"  Clicking Run...")
                            frame.wait_for_timeout(2000)
                            btn = frame.locator('button:has-text("Run")')
                            if btn.count() > 0:
                                btn.first.click()
                                print(f"  Waiting for Done!...")
                                done = wait_for_done(frame, timeout_ms)
                                if done:
                                    print(f"  ✓ {block_name} — Done! detected")
                                else:
                                    print(f"  ! {block_name} — timed out waiting for Done!")
                                clicked = True
                            else:
                                print(f"  No Run button found")
                            break
                    except Exception as e:
                        print(f"  Frame error: {e}")
                        continue

            except Exception as e:
                print(f"  Error: {e}")

            # Always close fullscreen before next block
            close_fullscreen(page)

            if not clicked:
                print(f"  ! Could not complete {block_name}")
            results.append((block_name, clicked))

        print("\n--- Summary ---")
        all_ok = True
        for name, success in results:
            print(f"  {'SUCCESS' if success else 'FAILED'}: {name}")
            if not success:
                all_ok = False

        browser.close()
        if not all_ok:
            sys.exit(1)
        print("\nDone.")

if __name__ == "__main__":
    run()
