# Meta AI Principal UI/UX Design Specification for Nexus

- **Evaluator Model:** `muse-wonder-1.0` (Meta AI Frontier Reasoning)
- **Token Usage:** {"completion_tokens": 5500, "prompt_tokens": 524, "total_tokens": 6024, "completion_tokens_details": {"reasoning_tokens": 3944}, "prompt_tokens_details": {"cached_tokens": 0}}
- **Design Theme:** LinkedIn Discovery Network + Linear Workspace Velocity

# NEXUS — UI/UX Architecture
### Principal Design Direction for Engineering

**North Star:** LinkedIn's discovery, without LinkedIn's bias. Linear/Figma's velocity, with Overleaf's rigor.

Nexus is not a social feed. It's a **Research OS**. Every decision must enforce our bias-free rule:

> **No name, photo, gender, GPA, lab prestige, follower count, or like count is visible before double opt-in. Only Offers, Needs, Methods, and Evidence travel.**

Avatars in discovery are generative geometric identicons seeded from Project ID. Identity is *earned* through mutual interest, not judged upfront.

### 1. NAVIGATION & VIEWPORT ARCHITECTURE

Use a fixed App Shell. Never let the body scroll in Studio views.

```
100dvh App Shell
┌────────────────────────────────────────────────────────────┐
│ TOPBAR 56px                                                │
├────┬──────────────────────────────────────────┬────────────┤
│RAIL│  MAIN VIEWPORT                           │ INSPECTOR  │
│64px│  Feed Mode OR Studio Mode                │ 320px      │
│    │                                          │ contextual │
└────┴──────────────────────────────────────────┴────────────┘
```

**Topbar (always present):** Left: Nexus node-mark logo. Center: `⌘K` Command Pill — *"Search needs, offers, methods..."* — this is your Linear moment. Right: Vault Lock icon with green dot, Presence Facepile, [Post Teaser] primary button.

**Left Rail 64px, icon-only:** Discover [Compass], My Pod [Users], Vault [Lock], Campus Graph [Network], Messages [MessageCircle - locked until reveal]. Tooltips on hover, active state = 2px Muse Violet left bar. Collapses to bottom nav on mobile.

**Two Viewport Modes — this is key:**

1.  **Feed Mode (Screen 3):** Light, social, centered. Max-width 1120px, single vertical scroll, 3-column inside: 240px Mini-Profile | 560px Feed | 300px Right Rail. Familiar like LinkedIn so judges get it in 2 seconds.
2.  **Studio Mode (Screens 1 & 2):** Dark, focused, full-bleed. No page scroll. Each pane scrolls independently. Draggable split-panes. Feels like Figma/Linear. This contrast *is* the brand.

**Right Inspector 320px:** Contextual, never static. Select an Evidence Card -> shows annotations. Select a Match -> shows synergy breakdown. Select a File -> shows hash details. Hide with `⌘\`.

### 2. VISUAL SYSTEM & DESIGN TOKENS

Dark for intelligence, Paper for scholarship. That juxtaposition is our visual signature.

```css
/* Canvas - Dark OS */
--canvas: #07080A;
--surface-1: #0E1015; /* cards */
--surface-2: #15181F; /* raised */
--surface-3: #1D212B; /* hover/active */
--hairline: rgba(255,255,255,0.08);
--hairline-strong: rgba(255,255,255,0.14);

/* Paper - Light Academic */
--paper: #F7F6F3;
--paper-card: #FFFFFF;
--ink: #101218;
--ink-2: #5A5E6A;

/* Accents - Use ONLY for meaning */
--muse: #7C6CFF; /* AI / Muse Wonder, gradient to #00C2FF */
--offer: #0EC9A7; /* Emerald - I can provide */
--need: #FFB224;  /* Amber - I am seeking */
--evidence: #4EA1FF;
--danger: #FF6B7A;

--radius-card: 16px; --radius-inner: 10px; --radius-pill: 999px;
--ease: cubic-bezier(0.2, 0, 0, 1);
```

**Typography:** `Inter` 13/14px for all UI (tight, -0.01em). `Newsreader` Serif 20-28px for project titles/paper titles only — instant academic credibility. `JetBrains Mono` 11px for hashes, IDs, timestamps, synergy data.

**Borders & Depth:** No drop shadows in dark mode. 1px hairline + inset top highlight `inset 0 1px 0 rgba(255,255,255,0.04)`. Paper editor gets one soft shadow to float *above* the dark OS. Offers = solid emerald pill with `[+]` icon. Needs = outlined amber pill with `[○]` icon. Never color alone — icon + label for colorblind safety.

**Motion:** 180ms ease-out for hover, 400ms spring for layout morphs. All AI animations use `pathLength` / typewriter, never fade-in generic.

### 3. EXACT COMPONENT BREAKDOWN

#### SCREEN 1: Research Pod Headquarters — Studio Mode

**Wireframe:** Header 72px / Timeline 64px / Split Pane fills rest

**A. `<PodPresenceBar/>`:** Editable Pod title in Serif. Right: Facepile of 4. Status ring = Editing (emerald pulse), Thinking (amber), In Muse Dive (violet). Typing = avatar ring pulses + tooltip: *"Editing Methods · Line 42"*. Live cursors in editor mirror this color.

**B. `<MilestoneStepper/>`:** Discovery → Drafting → Review → Submitted. Horizontal line, completed = filled check with SVG draw-on animation, current = pulsing dot + expanding checklist drawer on click. This is your progress, not a Kanban board.

**C. Left Pane 42% `<EvidenceBoard/>`:** Stack of `<EvidenceCard/>`. Each: Serif paper title, Mono DOI + Verified check, Relevance `89%`, left border by verdict: Supports (emerald), Contradicts (rose), Method (blue). Annotation count bubble. Hover: lifts 2px, reveals `[Pin to Proposal]` — clicking animates card flying into editor as a citation.

**D. Right Pane 58% `<SplitEditor/>`:** **Wow contrast:** Bright Paper card inside dark frame. Overleaf toolbar. Multiplayer carets with name flags. Muse suggestion = violet ghost text inline, `Tab` to accept, `Esc` to reject, diff shows +green / -rose on accept. Margin dots = comment threads, click expands in Inspector.

*Build once:* Resizer is draggable, double-click resets to 50/50.

#### SCREEN 2: Private Vault & Teaser Approval — Studio Mode

Left 50% Dark Vault, Right 50% Preview. Same `<TeaserCard/>` component as the Feed — WYSIWYG trust.

**A. `<VaultHasher/>`:** Dashed dropzone. On drop: **file never uploads.** A cyan scan-line sweeps the file icon, SHA-256 in Mono scrambles character-by-character then locks (Web Crypto `crypto.subtle.digest`). Below: generative fingerprint block from the hash + `Local only · Never left this device` shield copy.

**B. `<CertificateReceipt id="#NX-8492"/>`:** Looks like a lab receipt / boarding pass with perforated edge. Mono rows: Hash `a3f9...