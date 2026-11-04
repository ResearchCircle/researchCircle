import os
import time
from playwright.sync_api import sync_playwright

def main():
    os.makedirs("output/figma_live", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 960})
        page = context.new_page()

        print("Navigating to http://127.0.0.1:18088/ ...")
        page.goto("http://127.0.0.1:18088/", wait_until="networkidle")
        time.sleep(1)

        # 1. Capture Project Creator overlay
        print("[1/4] Capturing Project Creator...")
        composer_input = page.locator(".composer-fake-input")
        if composer_input.count() > 0:
            composer_input.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/07_nexus_project_creator.png")
            page.locator(".overlay-header button").first.click()
            time.sleep(0.5)

        # 2. Capture Pod View -> Pre-flight audit overlay
        print("[2/4] Capturing Pre-Flight Audit...")
        page.locator("nav.continuum button:has-text('Pod')").first.click()
        time.sleep(1)
        audit_btn = page.locator("button:has-text('Run pre-flight audit')")
        if audit_btn.count() > 0:
            audit_btn.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/08_nexus_peer_review_audit.png")
            page.locator(".overlay-header button").first.click()
            time.sleep(0.5)

        # 3. Capture Evidence Conflict overlay
        print("[3/4] Capturing Evidence Conflict...")
        conflict_btn = page.locator("button:has-text('Compare evidence')")
        if conflict_btn.count() > 0:
            conflict_btn.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/09_nexus_evidence_conflict.png")
            page.locator(".overlay-header button").first.click()
            time.sleep(0.5)

        # 4. Capture Proposal Studio -> Export dialog
        print("[4/4] Capturing Academic Export Dialog...")
        page.locator("nav.continuum button:has-text('Proposal')").first.click()
        time.sleep(1)
        export_btn = page.locator("button:has-text('Export')")
        if export_btn.count() > 0:
            export_btn.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/10_nexus_academic_export.png")

        browser.close()
        print("Overlays successfully captured!")

if __name__ == "__main__":
    main()
