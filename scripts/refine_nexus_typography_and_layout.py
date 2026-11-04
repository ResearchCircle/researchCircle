#!/usr/bin/env python3
import re
from pathlib import Path

CSS_PATH = Path("frontend/src/app/globals.css")

def main():
    css = CSS_PATH.read_text(encoding="utf-8")

    # 1. Scale font-size declarations
    def replace_fs(match):
        val = int(match.group(1))
        if val <= 7:
            new_val = 11
        elif val in (8, 9):
            new_val = 12
        elif val == 10:
            new_val = 13
        elif val == 11:
            new_val = 13
        else:
            new_val = val
        return f"font-size:{new_val}px"

    css = re.sub(r"font-size:\s*([0-9]+)px", replace_fs, css)

    # 2. Scale font shorthand declarations
    def replace_shorthand(match):
        weight = match.group(1)
        size = int(match.group(2))
        lh = match.group(3) or ""
        family = match.group(4)
        if size <= 7:
            new_size = 11
        elif size in (8, 9):
            new_size = 12
        elif size == 10:
            new_size = 13
        elif size == 11:
            new_size = 13
        else:
            new_size = size
        if lh:
            return f"font:{weight} {new_size}px{lh} {family}"
        else:
            return f"font:{weight} {new_size}px {family}"

    css = re.sub(
        r"font:\s*([0-9]+)\s+([0-9]+)px(/[\d.]+)?\s+([\'\"][^\'\"]+[\'\"]|\w+)",
        replace_shorthand,
        css,
    )

    # 3. Add explicit high-fidelity polish rules at the end of stylesheet
    polish_rules = """

/* === NEXUS PRODUCTION POLISH & REFINED TYPOGRAPHY === */

/* Paper Score Doughnut Ring Fix */
.paper-score {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  background: conic-gradient(var(--green) calc(var(--score, 96) * 1%), #e3e8e3 0) !important;
  position: relative !important;
  font: 700 14px 'DM Mono', monospace !important;
  isolation: isolate !important;
  padding-top: 0 !important;
}
.paper-score:before {
  content: "" !important;
  position: absolute !important;
  inset: 4px !important;
  background: var(--surface) !important;
  border-radius: 50% !important;
  z-index: 1 !important;
}
.paper-score > span {
  position: relative !important;
  z-index: 2 !important;
  font: 700 14px 'DM Mono', monospace !important;
  color: var(--ink) !important;
  line-height: 1 !important;
}
.paper-score > small {
  position: relative !important;
  z-index: 2 !important;
  font-size: 10px !important;
  color: var(--muted) !important;
  line-height: 1 !important;
  margin-left: 1px !important;
}

/* Home Match Score Badge */
.simple-match-score {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  background: #eef5fb !important;
  border: 1px solid #d4e4f2 !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
  flex: none !important;
  min-width: 64px !important;
}
.simple-match-score b {
  font: 700 18px 'DM Sans', sans-serif !important;
  color: #0a66c2 !important;
  line-height: 1.1 !important;
}
.simple-match-score span {
  font-size: 11px !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  color: #0a66c2 !important;
  margin-top: 2px !important;
}

/* Flightpath Milestones */
.flightpath button {
  display: grid !important;
  grid-template-columns: 28px 1fr !important;
  grid-template-rows: auto auto !important;
  column-gap: 10px !important;
  row-gap: 4px !important;
  align-items: center !important;
}
.flightpath b {
  font-size: 12px !important;
  line-height: 1.3 !important;
}
.flightpath small {
  font-size: 11px !important;
  line-height: 1.2 !important;
}

/* Trust Diagram in Vault */
.trust-diagram {
  gap: 12px !important;
}
.trust-diagram > div {
  min-width: 110px !important;
  text-align: center !important;
  gap: 5px !important;
}
.trust-diagram > div b {
  font-size: 13px !important;
  font-weight: 600 !important;
  color: var(--ink) !important;
}
.trust-diagram > div span {
  font-size: 11px !important;
  color: var(--muted) !important;
  line-height: 1.35 !important;
}
.trust-diagram > div.active b {
  color: var(--teal) !important;
}
.trust-diagram > i {
  height: 1px !important;
  width: 44px !important;
  margin-bottom: 24px !important;
}

/* Home Footer Links */
.home-footer {
  display: flex !important;
  justify-content: center !important;
  gap: 12px !important;
  flex-wrap: wrap !important;
  padding: 14px 10px !important;
}
.home-footer button,
.home-footer span {
  font-size: 11px !important;
  color: #7a8791 !important;
  cursor: pointer !important;
  transition: color 0.15s ease !important;
}
.home-footer button:hover {
  color: #0a66c2 !important;
  text-decoration: underline !important;
}
.home-footer span {
  width: 100% !important;
  text-align: center !important;
  margin-top: 4px !important;
  cursor: default !important;
}

/* People Suggestions */
.person-suggestion {
  display: grid !important;
  grid-template-columns: 36px 1fr auto !important;
  gap: 10px !important;
  align-items: center !important;
  padding: 10px 0 !important;
}
.person-suggestion .avatar {
  width: 36px !important;
  height: 36px !important;
}
.person-suggestion b {
  font-size: 13px !important;
  color: var(--ink) !important;
}
.person-suggestion small {
  font-size: 11px !important;
  color: #53616c !important;
}
.person-suggestion em {
  font-size: 11px !important;
  color: var(--muted) !important;
  font-style: normal !important;
}
.person-suggestion > button {
  font-size: 11px !important;
  padding: 6px 11px !important;
  border-radius: 16px !important;
  cursor: pointer !important;
  transition: all 0.15s ease !important;
}

/* Studio Document and Caption Readability */
.caption {
  font: 400 12px/1.45 'Newsreader', serif !important;
}
.caption mark {
  background: #e9dcf4 !important;
  padding: 1px 4px !important;
  border-radius: 3px !important;
}
.zoom-tools {
  font-size: 12px !important;
}
.zoom-tools button {
  font-size: 14px !important;
  cursor: pointer !important;
}
.zoom-tools span {
  font: 600 12px 'DM Mono', monospace !important;
}

/* Overlays Polish */
.workspace-overlay .overlay-header h2 {
  font-size: 20px !important;
}
.overlay-eyebrow {
  font-size: 11px !important;
  letter-spacing: 0.08em !important;
}
.reasoning-question p {
  font: 500 15px/1.4 'Newsreader', serif !important;
}
.reasoning-step b {
  font-size: 13px !important;
}
.reasoning-step p {
  font-size: 12px !important;
  line-height: 1.5 !important;
}
.reasoning-privacy {
  font-size: 12px !important;
}
.format-grid b {
  font-size: 13px !important;
}
.format-grid small {
  font-size: 11px !important;
}
.export-options b {
  font-size: 12px !important;
}
.export-options small {
  font-size: 11px !important;
}
"""
    css += polish_rules
    CSS_PATH.write_text(css, encoding="utf-8")
    print(f"Successfully refined {CSS_PATH} with updated typography and polish rules!")

if __name__ == "__main__":
    main()
