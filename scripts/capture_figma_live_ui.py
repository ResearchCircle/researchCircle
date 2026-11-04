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
        print("[1/6] Capturing Home View...")
        page.screenshot(path="output/figma_live/01_nexus_home_feed.png", full_page=True)

        # 2. Capture Vault View
        print("[2/6] Capturing Vault View...")
        vault_button = page.locator("nav.continuum button:has-text('Vault')")
        if vault_button.count() > 0:
            vault_button.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/02_nexus_private_vault.png", full_page=True)

        # 3. Capture Pod View
        print("[3/6] Capturing Pod View...")
        pod_button = page.locator("nav.continuum button:has-text('Pod')")
        if pod_button.count() > 0:
            pod_button.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/03_nexus_pod_workspace.png", full_page=True)

        # 4. Capture Proposal Studio
        print("[4/6] Capturing Proposal Studio...")
        proof_button = page.locator("nav.continuum button:has-text('Proposal')")
        if proof_button.count() > 0:
            proof_button.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/04_nexus_pixel_to_proof.png", full_page=True)

        # 5. Open and Capture Knowledge Graph Overlay
        print("[5/6] Capturing Knowledge Graph Overlay...")
        tools_button = page.locator("button.header-nav-button:has-text('Tools')")
        if tools_button.count() > 0:
            tools_button.first.click()
            time.sleep(0.5)
            graph_menu = page.locator(".tools-menu button:has-text('Knowledge graph')")
            if graph_menu.count() > 0:
                graph_menu.first.click()
                time.sleep(1)
                page.screenshot(path="output/figma_live/05_nexus_knowledge_graph.png")
                # Close overlay
                close_btn = page.locator(".overlay-header button")
                if close_btn.count() > 0:
                    close_btn.first.click()
                    time.sleep(0.5)

        # 6. Open and Capture Ask Nexus / Telemetry Drawer
        print("[6/6] Capturing Ask Nexus Drawer...")
        msg_button = page.locator("button.header-nav-button:has-text('Messages')")
        if msg_button.count() > 0:
            msg_button.first.click()
            time.sleep(1)
            page.screenshot(path="output/figma_live/06_nexus_ask_telemetry_drawer.png")

        browser.close()
        print("All screenshots successfully captured!")

if __name__ == "__main__":
    main()
