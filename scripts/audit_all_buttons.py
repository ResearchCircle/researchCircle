import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

def run_audit():
    print("=" * 80)
    print("SYSTEMATIC PLAYWRIGHT INTERACTIVE BUTTON AUDIT")
    print("Target: http://127.0.0.1:18088/")
    print("=" * 80)

    results = {
        "passed": [],
        "failed": [],
        "alerts_detected": [],
        "console_errors": []
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 960})
        page = context.new_page()

        # Listen for browser dialogs (ensure 0 alert() calls)
        def on_dialog(dialog):
            print(f"  [ALERT DETECTED] Type: {dialog.type}, Message: {dialog.message}")
            results["alerts_detected"].append({"type": dialog.type, "message": dialog.message})
            dialog.dismiss()

        page.on("dialog", on_dialog)

        # Listen for console errors
        def on_console(msg):
            if msg.type == "error":
                print(f"  [CONSOLE ERROR] {msg.text}")
                results["console_errors"].append(msg.text)

        page.on("console", on_console)

        page.goto("http://127.0.0.1:18088/", wait_until="networkidle")
        time.sleep(1)

        def verify_toast(expected_text=None):
            try:
                page.locator(".nexus-toast").wait_for(state="visible", timeout=3000)
                if expected_text:
                    for _ in range(5):
                        txt = page.locator(".nexus-toast").inner_text()
                        if expected_text.lower() in txt.lower():
                            return True, ""
                        time.sleep(0.15)
                    return False, f"Toast text mismatch: got '{txt}' (expected '{expected_text}')"
                return True, ""
            except Exception as e:
                return False, f"Toast not visible within timeout: {e}"

        def click_and_verify(label, selector, expected_check_fn=None, delay=0.3):
            print(f"Checking button: {label} ({selector})...")
            loc = page.locator(selector)
            if loc.count() == 0:
                print(f"  FAIL: Selector '{selector}' not found!")
                results["failed"].append({"label": label, "reason": "Selector not found", "selector": selector})
                return False
            
            try:
                loc.first.scroll_into_view_if_needed()
                loc.first.click(timeout=5000)
                time.sleep(delay)
                if expected_check_fn:
                    check_result, reason = expected_check_fn()
                    if not check_result:
                        print(f"  FAIL: {label} action failed: {reason}")
                        results["failed"].append({"label": label, "reason": reason, "selector": selector})
                        return False
                print(f"  PASS: {label}")
                results["passed"].append(label)
                return True
            except Exception as e:
                print(f"  FAIL: {label} exception: {e}")
                results["failed"].append({"label": label, "reason": str(e), "selector": selector})
                return False

        # =========================================================================
        # 1. GLOBAL HEADER & NAVIGATION
        # =========================================================================
        print("\n--- 1. Testing Global Header & Navigation ---")
        
        click_and_verify("Nav -> Vault", "nav.continuum button:has-text('Vault')", 
                         lambda: (page.locator(".view.vault-view").count() > 0, "Vault view not mounted"))
        click_and_verify("Nav -> Pod", "nav.continuum button:has-text('Pod')", 
                         lambda: (page.locator(".view.pod-view").count() > 0, "Pod view not mounted"))
        click_and_verify("Nav -> Proposal", "nav.continuum button:has-text('Proposal')", 
                         lambda: (page.locator(".proof-view").count() > 0, "Proposal view not mounted"))
        click_and_verify("Nav -> Home", "nav.continuum button:has-text('Home')", 
                         lambda: (page.locator(".home-view").count() > 0, "Home view not mounted"))
        click_and_verify("Logo -> Home", "button.wordmark", 
                         lambda: (page.locator(".home-view").count() > 0, "Logo click did not return to Home"))

        # Global Search
        search_input = page.locator(".search-wrapper input")
        search_input.fill("neural")
        time.sleep(0.3)
        click_and_verify("Search Dropdown Item Click", ".search-dropdown button.search-item", 
                         lambda: (page.locator(".project-overlay, .pod-view, .campus-view, .proof-view, .vault-view").count() > 0, "Search result navigation failed"))
        page.locator("nav.continuum button:has-text('Home')").click()
        time.sleep(0.3)

        # Tools Dropdown
        click_and_verify("Tools Dropdown Toggle", "button.header-nav-button:has-text('Tools')", 
                         lambda: (page.locator(".tools-menu").is_visible(), "Tools menu not visible"))
        click_and_verify("Tools -> Knowledge graph", ".tools-menu button:has-text('Knowledge graph')", 
                         lambda: (page.locator(".graph-workspace").is_visible(), "Graph workspace not open"))
        click_and_verify("Close Graph Overlay", ".overlay-header button", 
                         lambda: (not page.locator(".graph-workspace").is_visible(), "Graph overlay did not close"))

        # Tools -> Funding Finder
        page.locator("button.header-nav-button:has-text('Tools')").click()
        time.sleep(0.3)
        click_and_verify("Tools -> Funding finder", ".tools-menu button:has-text('Funding finder')", 
                         lambda: (page.locator(".funding-workspace").is_visible(), "Funding workspace not open"))
        click_and_verify("Close Funding Overlay", ".overlay-header button", 
                         lambda: (not page.locator(".funding-workspace").is_visible(), "Funding overlay did not close"))

        # Messages / Ask Nexus Drawer
        click_and_verify("Messages Button (Open Drawer)", "button.header-nav-button:has-text('Messages')", 
                         lambda: (page.locator(".telemetry-drawer").is_visible(), "Telemetry drawer not visible"))
        click_and_verify("Drawer Question Chip", ".prompt-chips button", 
                         lambda: (page.locator(".assistant-composer textarea").input_value() != "", "Chat prompt not set in textarea"))
        click_and_verify("Drawer Ask Nexus Button", ".assistant-composer button:has-text('Ask Nexus')", 
                         lambda: (page.locator(".assistant-answer").is_visible(), "Assistant synthesis answer not rendered"))
        click_and_verify("Close Telemetry Drawer", ".telemetry-drawer header button", 
                         lambda: (not page.locator(".telemetry-drawer").is_visible(), "Drawer did not close"))

        # Alerts Popover
        click_and_verify("Alerts Popover Open", "button.header-nav-button:has-text('Alerts')", 
                         lambda: (page.locator(".alerts-popover").is_visible(), "Alerts popover not open"))
        click_and_verify("Alerts -> Mark all read", ".alerts-popover button:has-text('Mark all read')", 
                         lambda: (True, ""))
        page.locator("button.wordmark").click()
        time.sleep(0.3)

        # Me Popover
        click_and_verify("Me Popover Open", "button.me-button", 
                         lambda: (page.locator(".me-popover").is_visible(), "Me popover not open"))
        click_and_verify("Me -> Privacy charter & keys", ".me-popover button:has-text('Privacy charter')", 
                         lambda: (page.locator(".modal-backdrop h3:has-text('Charter')").is_visible(), "Charter modal not open"))
        page.locator(".modal-head button").click()
        time.sleep(0.3)

        # =========================================================================
        # 2. HOME VIEW & PROFILE CARD
        # =========================================================================
        print("\n--- 2. Testing Home View & Profile Card ---")
        click_and_verify("Profile Card -> View profile", ".profile-card-body button:has-text('View profile')", 
                         lambda: (page.locator(".modal-backdrop h3:has-text('Researcher Profile')").is_visible(), "Profile modal not open"))
        click_and_verify("Close Profile Modal", ".modal-head button", 
                         lambda: (not page.locator(".modal-backdrop").is_visible(), "Modal not closed"))

        click_and_verify("Profile Card -> Project views", ".profile-stats button:has-text('Project views')", 
                         lambda: (page.locator(".modal-backdrop h3:has-text('Project Views')").is_visible(), "Views modal not open"))
        click_and_verify("Close Views Modal", ".modal-head button", 
                         lambda: (not page.locator(".modal-backdrop").is_visible(), "Modal not closed"))

        click_and_verify("Profile Card -> Edit availability", ".availability-card button:has-text('Edit availability')", 
                         lambda: (page.locator(".modal-backdrop h3:has-text('Availability')").is_visible(), "Availability modal not open"))
        click_and_verify("Availability Option Select", ".modal-body label", lambda: (True, ""))
        click_and_verify("Save Availability", ".modal-foot button:has-text('Save Preferences')", 
                         lambda: (page.locator(".nexus-toast").is_visible(), "Toast not shown on save"))

        click_and_verify("Profile Card -> Saved research", ".saved-card button:has-text('Saved research')", 
                         lambda: (page.locator(".modal-backdrop h3:has-text('Saved Research')").is_visible(), "Saved research modal not open"))
        click_and_verify("Close Saved Modal", ".modal-head button", 
                         lambda: (not page.locator(".modal-backdrop").is_visible(), "Modal not closed"))

        click_and_verify("Profile Card -> Private vault shortcut", ".saved-card button:has-text('Private vault')", 
                         lambda: (page.locator(".view.vault-view").is_visible(), "Vault view not opened"))
        page.locator("button.wordmark").click()
        time.sleep(0.3)

        # Post Composer
        click_and_verify("Composer -> Open Modal", ".share-card button:has-text('Share what you’re working on')", 
                         lambda: (page.locator(".modal-backdrop h3:has-text('Share with Campus')").is_visible(), "Composer modal not open"))
        page.locator(".modal-body input").first.fill("Automated Verification of Claims")
        page.locator(".modal-body textarea").fill("Testing automated verification of peer-review citations and consensus.")
        click_and_verify("Composer -> Submit Post", ".modal-foot button:has-text('Publish to Feed')", 
                         lambda: (page.locator(".nexus-toast").is_visible(), "Toast not shown on publish"))

        # Post Action Shortcuts
        click_and_verify("Post a project shortcut", ".share-actions button:has-text('Post a project')", 
                         lambda: (page.locator(".modal-backdrop").is_visible(), "Project post modal not opened"))
        page.locator(".modal-head button").click()
        time.sleep(0.3)

        click_and_verify("Find a collaborator shortcut", ".share-actions button:has-text('Find a collaborator')", 
                         lambda: (page.locator(".campus-view").is_visible(), "Campus view not opened"))
        page.locator("button.wordmark").click()
        time.sleep(0.3)

        click_and_verify("Protect an idea shortcut", ".share-actions button:has-text('Protect an idea')", 
                         lambda: (page.locator(".view.vault-view").is_visible(), "Vault view not opened"))
        page.locator("button.wordmark").click()
        time.sleep(0.3)

        # Feed sort toggle
        click_and_verify("Feed Sort Toggle", ".feed-sort button", lambda: (True, ""))

        # Collaborator Match Card
        click_and_verify("Match Card -> Connect privately", ".match-post footer button:has-text('Connect privately')", 
                         lambda: (page.locator(".match-post footer button:has-text('Review connection')").is_visible(), "Review connection state not active"))
        click_and_verify("Match Card -> Ask a question", ".match-post footer button:has-text('Ask a question')", 
                         lambda: (page.locator(".telemetry-drawer").is_visible(), "Ask drawer not opened"))
        page.locator(".telemetry-drawer header button").click()
        time.sleep(0.3)

        click_and_verify("Match Card -> Options menu", ".match-post .options-anchor button.icon-button", 
                         lambda: (page.locator(".options-dropdown").is_visible(), "Options menu not opened"))
        click_and_verify("Match Card -> Save match option", ".options-dropdown button:has-text('Save match')", 
                         lambda: (page.locator(".nexus-toast").is_visible(), "Toast not shown on save match"))

        # Active Project Post & Comments
        click_and_verify("Project Post -> Follow button", ".project-post footer button:has-text('Follow project')", 
                         lambda: (page.locator(".project-post footer button:has-text('Following')").is_visible(), "Following state not active"))
        click_and_verify("Project Post -> Comment button (Toggle thread)", ".project-post footer button:has-text('Comment')", 
                         lambda: (page.locator(".comment-thread").is_visible(), "Comment thread not opened"))
        page.locator(".comment-composer input").fill("Great breakthrough! Have you tested with cross-attention?")
        click_and_verify("Project Post -> Submit comment", ".comment-composer button:has-text('Post')", 
                         lambda: (page.locator(".comment-item:has-text('Great breakthrough')").is_visible(), "Comment not posted to thread"))
        click_and_verify("Project Post -> Share button", ".project-post footer button:has-text('Share')", 
                         lambda: verify_toast("Project link copied"))

        # Active Pod Summary
        click_and_verify("Active Pod Summary -> Continue your work", ".next-step-card button:has-text('Continue your work')", 
                         lambda: (page.locator(".view.pod-view").is_visible(), "Did not navigate to Pod view"))
        page.locator("button.wordmark").click()
        time.sleep(0.3)

        # People Recommendations
        click_and_verify("People Rec -> Follow", ".person-suggestion button", 
                         lambda: (page.locator(".person-suggestion button:has-text('Following')").count() > 0, "Following state not updated"))
        click_and_verify("People Rec -> See all suggestions", "button.see-all", 
                         lambda: (page.locator(".campus-view").is_visible(), "Campus view not opened"))
        page.locator("button.wordmark").click()
        time.sleep(0.3)

        # Funding Recommendation
        click_and_verify("Funding Rec -> View opportunity", ".funding-card button:has-text('View opportunity')", 
                         lambda: (page.locator(".funding-workspace").is_visible(), "Funding overlay not opened"))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        # Footer Links
        click_and_verify("Footer -> About", ".home-footer button:has-text('About')", 
                         lambda: (page.locator(".modal-backdrop h3:has-text('Charter')").is_visible(), "About charter modal not opened"))
        page.locator(".modal-head button").click()
        time.sleep(0.3)

        # =========================================================================
        # 3. CAMPUS DISCOVERY VIEW
        # =========================================================================
        print("\n--- 3. Testing Campus Discovery View ---")
        page.locator(".share-actions button:has-text('Find a collaborator')").click()
        time.sleep(0.3)

        page.locator(".search-field input").fill("EEG")
        time.sleep(0.3)
        click_and_verify("Campus Filter Pill -> EECS", ".filter-pill:has-text('EECS')", lambda: (True, ""))
        click_and_verify("Campus Filter Pill -> All campus", ".filter-pill:has-text('All campus')", lambda: (True, ""))
        click_and_verify("Campus Filter Pill -> Refine (Knowledge Graph)", ".filter-pill:has-text('Refine')", 
                         lambda: (page.locator(".graph-workspace").is_visible(), "Graph overlay not opened"))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        # Clear search so all projects show
        page.locator(".search-field input").fill("")
        time.sleep(0.3)

        click_and_verify("Campus Card -> View project", ".project-card footer button:has-text('View project')", 
                         lambda: (page.locator(".reveal-flow").is_visible(), "Reveal overlay not opened"))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        click_and_verify("Campus Card -> See why you match", "button.mutual-button", 
                         lambda: (page.locator("button.mutual-button:has-text('Private interest sent')").is_visible(), "Interest sent state not active"))
        click_and_verify("Campus Card -> Explore knowledge graph", "button.graph-glimpse", 
                         lambda: (page.locator(".graph-workspace").is_visible(), "Graph overlay not opened"))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        # =========================================================================
        # 4. PRIVATE VAULT VIEW
        # =========================================================================
        print("\n--- 4. Testing Private Vault View ---")
        page.locator("nav.continuum button:has-text('Vault')").click()
        time.sleep(0.3)

        page.locator(".hypothesis-box textarea").fill("Audited cryptographic consensus for privacy-preserving federated campus research networks.")
        time.sleep(0.3)
        click_and_verify("Vault -> Create priority proof", "button.accent-button:has-text('Create priority proof')", 
                         lambda: (page.locator(".certificate.panel.issued").is_visible(), "Proof certificate not generated"), delay=2.6)
        
        click_and_verify("Vault -> Download Certificate", "button.soft-button:has-text('Certificate')", 
                         lambda: (page.locator(".nexus-toast").is_visible(), "Download toast not shown"))
        
        click_and_verify("Vault -> Audience Stranger", ".preview-toolbar button:has-text('Stranger')", lambda: (True, ""))
        click_and_verify("Vault -> Audience Peer student", ".preview-toolbar button:has-text('Peer student')", lambda: (True, ""))
        click_and_verify("Vault -> Audience Professor", ".preview-toolbar button:has-text('Professor')", lambda: (True, ""))
        
        click_and_verify("Vault -> Request private match", "button:has-text('Request a private match')", 
                         lambda: (page.locator(".reveal-flow").is_visible(), "Reveal overlay not opened"))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        click_and_verify("Vault -> Open verification page", "button.certificate-footer", 
                         lambda: (page.locator(".verification-page").is_visible(), "Verify overlay not opened"))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        # =========================================================================
        # 5. RESEARCH POD WORKSPACE
        # =========================================================================
        print("\n--- 5. Testing Research Pod Workspace ---")
        page.locator("nav.continuum button:has-text('Pod')").click()
        time.sleep(0.3)

        click_and_verify("Pod -> Add Teammate Modal", ".pod-people button:has-text('Add teammate')", 
                         lambda: (page.locator(".modal-backdrop h3:has-text('Add Teammate')").is_visible(), "Add teammate modal not open"))
        page.locator(".modal-body input[type='email']").fill("elena.vasquez@princeton.edu")
        click_and_verify("Pod -> Submit Teammate", ".modal-foot button:has-text('Send Invitation')", 
                         lambda: verify_toast("Invitation sent"))

        # Milestone Flightpath
        click_and_verify("Milestone 1: Literature discovery", ".flightpath button:nth-child(1)", lambda: (True, ""))
        click_and_verify("Milestone 2: Evidence assembly", ".flightpath button:nth-child(2)", lambda: (True, ""))
        click_and_verify("Milestone 3: Collaborative drafting", ".flightpath button:nth-child(3)", lambda: (True, ""))
        click_and_verify("Milestone 4: Peer review", ".flightpath button:nth-child(4)", lambda: (True, ""))
        click_and_verify("Milestone 5: Final submission", ".flightpath button:nth-child(5)", lambda: (True, ""))

        # Grant selector switch
        click_and_verify("Pod -> Switch Grant", ".milestone-heading button", lambda: (True, ""))

        # Focus Audit button on 'Your next move' card
        click_and_verify("Pod -> Run pre-flight audit", "button.focus-audit-button", 
                         lambda: (page.locator(".peer-review").is_visible(), "Peer review overlay not opened"))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        # Add Paper Modal
        click_and_verify("Evidence Board -> Add paper", ".panel-tools button.soft-button", 
                         lambda: (page.locator(".modal-backdrop h3:has-text('Add Research Paper')").is_visible(), "Add paper modal not open"))
        page.locator(".modal-body input").nth(1).fill("Autonomous Multi-Agent Calibration in High-Noise Regimes")
        page.locator(".modal-body input").nth(2).fill("K. Vance et al. · NeurIPS 2026")
        click_and_verify("Evidence Board -> Submit Paper", ".modal-foot button:has-text('Index & Add Paper')", 
                         lambda: verify_toast("indexed into Evidence Board"))

        # Pin Citation Toggle
        click_and_verify("Evidence Board -> Pin citation toggle", ".paper-row:first-child .pin-button", 
                         lambda: verify_toast("citation"))

        # Paper Options Dropdown
        click_and_verify("Evidence Board -> Paper options", ".paper-row:first-child .options-anchor button.icon-button", 
                         lambda: (page.locator(".options-dropdown").is_visible(), "Paper options dropdown not open"))
        click_and_verify("Paper options -> Download BibTeX", ".options-dropdown button:has-text('Download BibTeX')", 
                         lambda: verify_toast("Downloaded BibTeX entry"))

        # Expand all 18 sources
        click_and_verify("Evidence Board -> View all sources", "button.text-button.full", 
                         lambda: (page.locator("button.text-button.full:has-text('Show top foundational sources')").is_visible(), "18 sources not expanded"))
        click_and_verify("Evidence Board -> Collapse sources", "button.text-button.full", 
                         lambda: (page.locator("button.text-button.full:has-text('View all')").is_visible(), "Sources not collapsed"))

        # Pod Discussion Tab & Composer
        click_and_verify("Pod Workspace -> Discussion Tab", ".switcher button:has-text('Discussion')", 
                         lambda: (page.locator(".discussion-list").is_visible(), "Discussion thread not visible"))
        page.locator(".reply-box input").fill("Confirmed: verified equation 3 bounds against the lemma yesterday.")
        click_and_verify("Pod Discussion -> Send reply", ".reply-box button[title='Send reply']", 
                         lambda: (page.locator(".discussion-list p:has-text('equation 3')").is_visible(), "Reply not appended"))
        
        # Switch back to Evidence Board tab
        page.locator(".switcher button:has-text('Evidence board')").click()
        time.sleep(0.3)

        # Filter Activity button
        click_and_verify("Pod Activity -> Filter activity", ".activity-panel .options-anchor button.icon-button", 
                         lambda: (page.locator(".options-dropdown").is_visible(), "Filter options not open"))
        click_and_verify("Pod Activity -> Select filter", ".options-dropdown button:has-text('Citations only')", lambda: (True, ""))

        # Continue Writing -> Proposal Studio
        click_and_verify("Pod Proposal Entry -> Continue writing", ".studio-copy button.accent-button:has-text('Continue writing')", 
                         lambda: (page.locator(".proof-view").is_visible(), "Did not navigate to Proposal Studio"))

        # =========================================================================
        # 6. PROPOSAL STUDIO & PIXEL-TO-PROOF
        # =========================================================================
        print("\n--- 6. Testing Proposal Studio & Pixel-to-Proof ---")
        
        # Header controls
        click_and_verify("Proposal Header -> Discuss", ".studio-presence button:has-text('Discuss')", 
                         lambda: (page.locator(".telemetry-drawer").is_visible(), "Discuss drawer not opened"))
        page.locator(".telemetry-drawer header button").click()
        time.sleep(0.3)

        click_and_verify("Proposal Header -> Export", ".studio-presence button:has-text('Export')", 
                         lambda: (page.locator(".export-dialog").is_visible(), "Export overlay not opened"))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        # Formatting toolbar
        click_and_verify("Toolbar -> Bold", ".editor-toolbar button:has-text('B')", lambda: (True, ""))
        click_and_verify("Toolbar -> Italic", ".editor-toolbar button:has-text('I')", lambda: (True, ""))
        click_and_verify("Toolbar -> Heading 2", ".editor-toolbar button:has-text('H₂')", lambda: (True, ""))
        click_and_verify("Toolbar -> Format Style Dropdown", ".editor-toolbar .options-anchor button", 
                         lambda: (page.locator(".options-dropdown").is_visible(), "Format dropdown not visible"))
        click_and_verify("Toolbar -> Choose Heading 1", ".options-dropdown button:has-text('Heading 1')", lambda: (True, ""))

        # Claim selection in Claim Rail
        click_and_verify("Claim Rail -> Select Claim 1 (Equation 3)", ".rail-claims button:nth-child(2)", 
                         lambda: (page.locator(".pdf-stage:has-text('Equation 3')").is_visible(), "Equation 3 not rendered for Claim 1"))
        click_and_verify("Claim Rail -> Select Claim 0 (Figure 4B)", ".rail-claims button:nth-child(1)", 
                         lambda: (page.locator(".pdf-stage:has-text('Figure 4.')").is_visible(), "Figure 4B not rendered for Claim 0"))

        # AI Suggestion Actions
        click_and_verify("AI Suggestion -> Tab to accept", ".ai-suggestion footer span:has-text('Accept')", 
                         lambda: (page.locator(".nexus-toast").is_visible(), "Toast not shown on tab accept"))

        # Source Evidence Tabs
        click_and_verify("Evidence Tab -> Extraction", ".source-tabs button:has-text('Extraction')", 
                         lambda: (page.locator(".source-tab-content .extraction-grid").is_visible(), "Extraction tab not mounted"))
        click_and_verify("Evidence Tab -> Audit trail", ".source-tabs button:has-text('Audit trail')", 
                         lambda: (page.locator(".source-tab-content:has-text('SOURCE DOCUMENT SHA-256 HASH')").is_visible(), "Audit trail tab not mounted"))
        click_and_verify("Evidence Tab -> PDF source", ".source-tabs button:has-text('PDF source')", 
                         lambda: (page.locator(".pdf-stage").is_visible(), "PDF source view not mounted"))

        # Zoom Controls
        click_and_verify("Zoom In (+)", ".zoom-tools button:has-text('+')", lambda: (True, ""))
        click_and_verify("Zoom Out (-)", ".zoom-tools button:has-text('−')", lambda: (True, ""))

        # Live verification button
        click_and_verify("Source Verification -> Check against source", "button.verify-button", 
                         lambda: (page.locator(".audit-result:has-text('The source supports this claim')").is_visible(), "Verified badge not shown"), delay=2.4)

        # Ask Literature & Reasoning
        click_and_verify("Claim Rail -> Ask literature", ".claim-rail button:has-text('Ask literature')", 
                         lambda: (page.locator(".telemetry-drawer").is_visible(), "Ask drawer not opened"))
        page.locator(".telemetry-drawer header button").click()
        time.sleep(0.3)

        click_and_verify("Claim Rail -> Reasoning", ".claim-rail button:has-text('Reasoning')", 
                         lambda: (page.locator(".reasoning-inspector").is_visible(), "Reasoning overlay not opened"))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        # Back chevron to Pod
        click_and_verify("Proposal Header -> Back chevron", ".studio-header button.icon-button", 
                         lambda: (page.locator(".view.pod-view").is_visible(), "Back did not return to Pod"))

        # =========================================================================
        # 7. OVERLAYS DEEP WORKFLOW
        # =========================================================================
        print("\n--- 7. Testing Overlays Deep Interaction ---")
        
        # 1. Peer review merit review accordions
        page.locator("button.focus-audit-button").click()
        time.sleep(0.3)
        click_and_verify("Peer Review -> Toggle Question 1 Accordion", ".peer-review button.question-card:first-of-type", lambda: (True, ""))
        click_and_verify("Peer Review -> Toggle Question 2 Accordion", ".peer-review button.question-card:last-of-type", lambda: (True, ""))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        # 2. Evidence conflict resolution modal
        page.locator(".pin-button:has-text('Inspect conflict')").click()
        time.sleep(0.3)
        click_and_verify("Conflict Overlay -> Insert Balanced Claim", ".conflict-view button:has-text('Insert Balanced Claim')", 
                         lambda: (page.locator(".nexus-toast").is_visible(), "Insert draft toast not shown"))
        # (It automatically closes and navigates to proof)
        time.sleep(0.3)

        # 3. Academic export modal downloads
        page.locator(".studio-presence button:has-text('Export')").click()
        time.sleep(0.3)
        click_and_verify("Export -> Select Format TEX", ".export-dialog button:has-text('TEX')", lambda: (True, ""))
        click_and_verify("Export -> Select Format PDF", ".export-dialog button:has-text('PDF')", lambda: (True, ""))
        click_and_verify("Export -> Select Format MD", ".export-dialog button:has-text('MD')", lambda: (True, ""))
        click_and_verify("Export -> Download Package", ".export-dialog button.accent-button", 
                         lambda: (page.locator(".nexus-toast").is_visible(), "Export toast not shown"))
        time.sleep(0.3)

        # 4. Interactive knowledge graph overlay
        page.locator("nav.continuum button:has-text('Home')").click()
        time.sleep(0.3)
        page.locator("button.header-nav-button:has-text('Tools')").click()
        time.sleep(0.3)
        page.locator(".tools-menu button:has-text('Knowledge graph')").click()
        time.sleep(0.3)
        click_and_verify("Knowledge Graph -> Search Query Input", ".graph-workspace input", lambda: (True, ""))
        click_and_verify("Knowledge Graph -> Click Node", "g.graph-node", lambda: (True, ""))
        click_and_verify("Knowledge Graph -> Filter People", ".graph-toolbar button:has-text('People')", lambda: (True, ""))
        click_and_verify("Knowledge Graph -> Bridge Gap", ".graph-inspector button:has-text('Bridge this gap on Campus')", 
                         lambda: (page.locator(".campus-view").is_visible(), "Campus view not opened"))
        time.sleep(0.3)

        # 5. Funding Finder modal agency filters
        page.locator("nav.continuum button:has-text('Home')").click()
        time.sleep(0.3)
        page.locator("button.header-nav-button:has-text('Tools')").click()
        time.sleep(0.3)
        page.locator(".tools-menu button:has-text('Funding finder')").click()
        time.sleep(0.3)
        click_and_verify("Funding Finder -> Filter NSF", ".funding-filters button:has-text('NSF')", lambda: (True, ""))
        click_and_verify("Funding Finder -> Filter NIH", ".funding-filters button:has-text('NIH')", lambda: (True, ""))
        click_and_verify("Funding Finder -> Filter DARPA", ".funding-filters button:has-text('DARPA')", lambda: (True, ""))
        page.locator(".overlay-header button").click()
        time.sleep(0.3)

        browser.close()

    print("\n" + "=" * 80)
    print("AUDIT RESULTS SUMMARY")
    print(f"Total Passed Controls: {len(results['passed'])}")
    print(f"Total Failed Controls: {len(results['failed'])}")
    print(f"Total Alerts Detected: {len(results['alerts_detected'])}")
    print(f"Total Console Errors:  {len(results['console_errors'])}")
    print("=" * 80)

    if results["failed"]:
        print("\nFAILED CONTROLS DETAILS:")
        for f in results["failed"]:
            print(f" - [{f['label']}]: {f['reason']} (selector: {f['selector']})")

    if results["alerts_detected"]:
        print("\nUNWANTED ALERTS DETECTED:")
        for a in results["alerts_detected"]:
            print(f" - [{a['type']}]: {a['message']}")

    if results["console_errors"]:
        print("\nCONSOLE ERRORS DETECTED:")
        for err in results["console_errors"]:
            print(f" - {err}")

    # Write audit JSON report
    os.makedirs("output", exist_ok=True)
    with open("output/systematic_button_audit_report.json", "w") as fp:
        json.dump(results, fp, indent=2)

    return len(results["failed"]) == 0 and len(results["alerts_detected"]) == 0

if __name__ == "__main__":
    success = run_audit()
    sys.exit(0 if success else 1)
