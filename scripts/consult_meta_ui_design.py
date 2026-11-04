import urllib.request
import json
import os
import sys

def main():
    api_key = None
    if os.path.exists("dist/core-runtime.env"):
        with open("dist/core-runtime.env") as f:
            for line in f:
                if line.startswith("MODEL_API_KEY="):
                    api_key = line.strip().split("=", 1)[1]
                    break
    if not api_key:
        api_key = os.environ.get("MODEL_API_KEY")

    if not api_key:
        print("ERROR: MODEL_API_KEY not found!")
        sys.exit(1)

    url = "https://api.meta.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = """You are the Principal Product Designer & Human-Computer Interaction (HCI) Lead at Meta AI advising the engineering team of 'Nexus' for the Cerebral Valley x Meta AI Developer Hackathon ($1,000,000 prize pool).

SYSTEM UNDER DESIGN:
Name: Nexus
Tagline: Connecting Minds. Synthesizing Science. / The Living Campus Graph.
Core Paradigm: The Pre-Publication Living Graph of a University. Turning isolated student projects, hypotheses, and faculty labs into a connected, collaborative intelligence fabric.

THE DESIGN CHALLENGE:
We need you to design a fresh, bias-free, world-class UI/UX architecture for Nexus. 
Take inspiration from LinkedIn (the social network effects, discovery feed, connection requests, profile presence, skill/offer/need endorsements), but elevate it with the focused velocity of Linear/Figma (split-screen collaboration, live presence avatars, real-time diffs, zero friction) and the academic rigor of Overleaf/Google Scholar.

We want specific UI architectures for the THREE FLAGSHIP SCREENS:
1. SCREEN 1: Research Pod Headquarters
   - Features: Live team presence (avatars with status), milestone timeline (Discovery -> Drafting -> Review -> Submitted), shared literature evidence cards with review annotations, and a split-screen collaborative proposal editor.
2. SCREEN 2: Private Vault & Teaser Approval
   - Features: Local-file protection with client-side SHA-256 priority hashing, downloadable timestamped certificate receipt (#NX-8492), and an "Audience Preview" toggle (Stranger vs Peer Student vs Professor) showing how abstracted Offers & Needs look before posting.
3. SCREEN 3: Nexus Campus Discovery Feed & Serendipity Match
   - Features: LinkedIn-inspired campus feed with project cards, stage badges (Hypothesis, Prototype, Experiment), color-coded Offers & Needs tags, and an Explainable Collaborator Match banner (94% synergy, distance on campus, Meta Muse Wonder bridge sentence, and double opt-in mutual reveal).

DELIVERABLES:
1. Navigation & Viewport Architecture: What is the cleanest layout hierarchy (Topbar, navigation hubs, feed vs studio viewports, side panels)?
2. Visual System & Design Tokens: Color palette, typography, border styling, dark/light surface depths that feel like a cutting-edge AI research OS.
3. Exact Component & Micro-interaction Breakdown for all 3 flagship screens.
4. What visual element will make the Meta AI and VC judges say "Wow" in the first 15 seconds?
"""

    payload = {
        "model": "muse-wonder-1.0",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 5500,
        "temperature": 0.6
    }

    print("Querying Meta AI (muse-wonder-1.0) for Principal UI/UX Design Specification...")
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            choice = res["choices"][0]
            content = choice["message"].get("content")
            usage = res.get("usage", {})
            print(f"Usage Tokens: {usage}")
            
            if content:
                print("UI Design received! Length:", len(content))
                os.makedirs("docs", exist_ok=True)
                with open("docs/META_AI_UI_UX_SPECIFICATION.md", "w") as out_f:
                    out_f.write("# Meta AI Principal UI/UX Design Specification for Nexus\n\n")
                    out_f.write(f"- **Evaluator Model:** `muse-wonder-1.0` (Meta AI Frontier Reasoning)\n")
                    out_f.write(f"- **Token Usage:** {json.dumps(usage)}\n")
                    out_f.write(f"- **Design Theme:** LinkedIn Discovery Network + Linear Workspace Velocity\n\n")
                    out_f.write(content)
                print("Saved to docs/META_AI_UI_UX_SPECIFICATION.md")
            else:
                print("WARNING: Content was None. Reason:", choice.get("finish_reason"))
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()
