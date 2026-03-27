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
    ("Potentials",      "24m4f0j", 240000),
    ("Quotes",          "4xq9c2h", 180000),
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
            print(f"\nProcessing {block_name}...")

            try:
                # Step 1: Find the block container by its iframe src and click fullscreen
                # The fullscreen button is a sibling of the iframe container
                fullscreen_btn = page.locator(
                    f'div[data-blockinstallationid] iframe[src*="{url_fragment}"]'
                    f' >> xpath=../../../.. >> [aria-label="Enter fullscreen"]'
                )

                # Alternative approach - find block frame div and look for fullscreen button
                block_frame = page.locator(f'iframe[src*="{url_fragment}"]').first
                
                if block_frame.count() == 0:
                    print(f"  ! Could not find iframe for {block_name}")
                    results.append((block_name, False))
                    continue

                # Hover over the block to make the fullscreen button visible
                block_frame.hover()
                page.wait_for_timeout(1000)

                # Click the fullscreen button for this block
                # It's inside the same blockFrame div as the iframe
                fs_button = page.locator(
                    f'iframe[src*="{url_fragment}"]'
                ).locator(
                    'xpath=ancestor::div[contains(@class,"blockFrame")]'
                ).locator('[aria-label="Enter fullscreen"]')

                if fs_button.count() > 0:
                    fs_button.click()
                    print(f"  ✓ Opened fullscreen for {block_name}")
                    page.wait_for_timeout(3000)
                else:
                    print(f"  ! Fullscreen button not found for {block_name}, trying anyway...")

                # Step 2: Find the iframe (now fullscreen) and click Run
                for frame in page.frames:
                    try:
                        if url_fragment in frame.url:
                            print(f"  Found iframe — clicking Run...")
                            frame.wait_for_timeout(2000)
                            btn = frame.locator('button:has-text("Run")')
                            if btn.count() > 0:
                                btn.first.click()
                                print(f"  ✓ Clicked Run — waiting {wait_ms//1000}s...")
                                page.wait_for_timeout(wait_ms)
                                print(f"  ✓ {block_name} done")
                                clicked = True

                                # Step 3: Close fullscreen (press Escape)
                                page.keyboard.press("Escape")
                                page.wait_for_timeout(2000)
                                break
                            else:
                                print(f"  ! No Run button found in {block_name}")
                    except Exception as e:
                        print(f"  ! Frame error in {block_name}: {e}")
                        continue

            except Exception as e:
                print(f"  ! Error processing {block_name}: {e}")

            if not clicked:
                print(f"  ! Could not complete {block_name}")
                # Try to escape fullscreen before moving on
                page.keyboard.press("Escape")
                page.wait_for_timeout(1000)

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

        print("\nDone — all blocks processed.")

if __name__ == "__main__":
    run()
