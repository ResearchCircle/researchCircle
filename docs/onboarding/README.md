# Team startup and copy-paste prompts

Updated 2026-10-30. Start from branch `v2`. The goal is a working research platform; advanced security follows later.

## Which prompt to use

Paste the complete code block from the matching file into a new coding session opened at the repository root. The prompt tells the session to read the shared project rules and then implement the first assigned ticket. Replace the data path only if your local copy lives elsewhere.

| Person | Starter prompt | First ticket |
|---|---|---|
| Teammate 1 | [Data and discovery](prompts/teammate-1-data-discovery.md) | D-P1: inventory/import adapter and real source-linked search |
| Teammate 2 | [Workflow backend](prompts/teammate-2-backend-workflow.md) | B-P1: local database, accounts, teams and proposal skeleton |
| Teammate 3 | [Frontend and user journey](prompts/teammate-3-frontend.md) | U-P1: typed client, discovery and shortlist screens |
| Anurag | [Orin and drafting](prompts/anurag-orin-drafting.md) | A-P1: local provider contract, fixture and real Orin smoke |

## Get the checkout

On a new machine, clone `https://github.com/ResearchCircle/researchCircle.git` using your authorized GitHub account, then check out `v2`. On an existing checkout, inspect `git status` first; fetch and fast-forward only if clean. Do not discard local work or force a diverged branch into place. The old remote URL redirects to this repository; no remote rewrite is required for an existing checkout.

```sh
git clone --branch v2 https://github.com/ResearchCircle/researchCircle.git
cd researchCircle
git status --short
git branch --show-current
```

For work, create a role/ticket branch from the current `v2`, such as `teammate-1/d-p1-import`, `teammate-2/b-p1-core` or `teammate-3/u-p1-discovery`. The prompts request local implementation, not a direct push to shared `v2`. Ask the human only for genuinely missing access/input; do not pause routine work for repeated confirmations.

## Local setup expectations

Use Python 3.12 for the new backend work and the Node version compatible with the checked-in Next.js package. Inspect actual package engine requirements rather than guessing. Create an isolated `.venv`; use the existing npm lock with `npm ci` in `frontend`. Install from the agreed task dependency file/lock when available. At this baseline there is **no complete Python lock, Postgres compose file or ready-made platform bootstrap**. B-P1 creates the repeatable backend setup; do not claim a planned command exists.

For a small Python-only contract task, `python -m pip install -e . --no-deps` can register the existing project without installing every legacy ML/crawler dependency; install the specific metadata-declared dependencies needed for the task and record their versions. It is not a complete application installation. Avoid blindly installing the old `requirements.txt` or initializing a model while only working on DTOs or UI.

Current entry point is `python -m uvicorn services.api.app:app --reload` **after uvicorn/FastAPI dependencies are installed**. The baseline API has only `/healthz`; `/api/v2` routes are work to implement. Frontend starts with `npm run dev` in `frontend`, but existing screens still call legacy localhost endpoints until U-P1 replaces them. Expect this mismatch; do not mistake the UI starting for the product working.

The legacy `.env.example` mentions Gemini. That is not a requirement for these tasks. Do not obtain paid keys or copy Anurag's `.env`. Model fixtures unblock local work; only Anurag validates Orin.

## Receive the collected data

Anurag will share the data separately; a clone does not contain the complete corpus. Follow [Data handoff](DATA-HANDOFF.md). Keep the supplied source copy unchanged and place working indexes/output elsewhere. Each teammate reports what files are actually present before relying on them.

Inspection in this workspace on 2026-10-30 found approximately 44 KB: tracked prompt templates/taxonomy and empty artifact folders. It did **not** expose collected researcher JSON, research cards, populated Chroma, PDFs or a SQLite database. This is a limitation of this visible checkout, not a claim that Anurag has no collected data. A teammate receiving a fuller copy must inspect that copy rather than repeat these counts.

## Continue a session

Use [the resume template](prompts/resume-ticket.md) when restarting. Keep durable notes in a ticket/PR or short `docs/qa/` handoff, not hidden conversation memory. Check current commits/contracts before resuming; teammates may have merged changes meanwhile.

A first session should produce an owned code/test slice or a precise environment/access blocker plus independent progress. It should not end with an architecture rewrite, a new security project or a list of tasks someone else must do first.
