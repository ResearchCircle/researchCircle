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
        time.sleep(2)

        # 1. Capture Home View
        print("[1/10] Capturing Home Feed...")
        page.screenshot(path="output/figma_live/01_nexus_home_feed.png", full_page=True)

        # 2. Capture Campus Discovery View
        print("[2/10] Capturing Campus Discovery...")
        find_btn = page.locator(".share-actions button:has-text('Find a collaborator')")
        if find_btn.count() > 0:
            find_btn.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/02_nexus_campus_discovery.png", full_page=True)

        # 3. Capture Vault View
        print("[3/10] Capturing Vault View...")
        vault_button = page.locator("nav.continuum button:has-text('Vault')")
        if vault_button.count() > 0:
            vault_button.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/03_nexus_private_vault.png", full_page=True)

        # 4. Capture Pod View (Evidence Board & Discussion)
        print("[4/10] Capturing Pod View...")
        pod_button = page.locator("nav.continuum button:has-text('Pod')")
        if pod_button.count() > 0:
            pod_button.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/04_nexus_pod_workspace.png", full_page=True)

        # 5. Capture Proposal Studio
        print("[5/10] Capturing Proposal Studio...")
        proof_button = page.locator("nav.continuum button:has-text('Proposal')")
        if proof_button.count() > 0:
            proof_button.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/05_nexus_pixel_to_proof.png", full_page=True)

        # 6. Capture Knowledge Graph Overlay
        print("[6/10] Capturing Knowledge Graph...")
        tools_button = page.locator("button.header-nav-button:has-text('Tools')")
        if tools_button.count() > 0:
            tools_button.first.click()
            time.sleep(0.5)
            graph_menu = page.locator(".tools-menu button:has-text('Knowledge graph')")
            if graph_menu.count() > 0:
                graph_menu.first.click()
                time.sleep(1)
                page.screenshot(path="output/figma_live/06_nexus_knowledge_graph.png")
                close_btn = page.locator(".overlay-header button")
                if close_btn.count() > 0:
                    close_btn.first.click()
                    time.sleep(0.5)

        # 7. Capture Peer Review Audit Overlay
        print("[7/10] Capturing Peer Review Audit...")
        pod_button.first.click()
        time.sleep(0.5)
        audit_btn = page.locator("button.focus-audit-button")
        if audit_btn.count() > 0:
            audit_btn.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/08_nexus_peer_review_audit.png")
            close_btn = page.locator(".overlay-header button")
            if close_btn.count() > 0:
                close_btn.first.click()
                time.sleep(0.5)

        # 8. Capture Evidence Conflict Resolution Overlay
        print("[8/10] Capturing Conflict Overlay...")
        # Paper 2 is "Contradicts", pin-button opens conflict overlay
        contradict_pin = page.locator(".paper-row:has(.tag-contradicts) .pin-button")
        if contradict_pin.count() > 0:
            contradict_pin.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/09_nexus_evidence_conflict.png")
            close_btn = page.locator(".overlay-header button")
            if close_btn.count() > 0:
                close_btn.first.click()
                time.sleep(0.5)

        # 9. Capture Academic Export Dialog
        print("[9/10] Capturing Academic Export...")
        proof_button.first.click()
        time.sleep(0.5)
        export_btn = page.locator("button:has-text('Export')")
        if export_btn.count() > 0:
            export_btn.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/10_nexus_academic_export.png")
            close_btn = page.locator(".overlay-header button")
            if close_btn.count() > 0:
                close_btn.first.click()
                time.sleep(0.5)

        # 10. Capture Ask Nexus / Telemetry Drawer
        print("[10/10] Capturing Ask Nexus Drawer...")
        msg_button = page.locator("button.header-nav-button:has-text('Messages')")
        if msg_button.count() > 0:
            msg_button.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/07_nexus_ask_telemetry_drawer.png")

        browser.close()
        print("All 10 polished screenshots captured successfully!")

if __name__ == "__main__":
    main()
