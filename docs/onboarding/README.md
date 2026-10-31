# Team startup and copy-paste prompts

**Current implementation:** read [the core handoff](CORE-HANDOFF.md) first. Named
accounts, proposals/sources, public records, shortlists, persisted jobs, editor,
tracking records and local runtime now exist.

Updated 2026-10-31. Start from branch `anurag/a-p1-provider`, not `v2`, until it is merged. The goal is a working research platform; advanced security follows later.

## Which prompt to use

Paste the complete code block from the matching file into a new coding session opened at the repository root. The prompt tells the session to read the shared project rules and then start the next open work for that role.

| Person | Starter prompt | Starts with |
|---|---|---|
| Teammate 1 | [Data and discovery](prompts/teammate-1-data-discovery.md) | Real data snapshot import, then collaborator matching |
| Teammate 2 | [Workflow backend](prompts/teammate-2-backend-workflow.md) | Backup/membership checks on the current schema, then dependency lock |
| Teammate 3 | [Frontend and user journey](prompts/teammate-3-frontend.md) | Member management UI, then wider browser coverage |
| Anurag | [Orin and drafting](prompts/anurag-orin-drafting.md) | One real persisted Orin browser job, then shared demo |

## Get the checkout

On a new machine, clone `https://github.com/ResearchCircle/researchCircle.git` using your authorized GitHub account, then check out `anurag/a-p1-provider`. On an existing checkout, inspect `git status` first; fetch and fast-forward only if clean. Do not discard local work or force a diverged branch into place. The old remote URL redirects to this repository; no remote rewrite is required for an existing checkout.

```sh
git clone --branch anurag/a-p1-provider https://github.com/ResearchCircle/researchCircle.git
cd researchCircle
git status --short
git branch --show-current
```

For work, create a role/ticket branch from it, such as `teammate-1/d-p2-matching`, `teammate-2/backup-smoke` or `teammate-3/member-ui`. The prompts request local implementation, not a direct push to a shared branch. Ask the human only for genuinely missing access/input; do not pause routine work for repeated confirmations.

## Local setup expectations

Use Python 3.12 and Docker with Compose. Follow [the core handoff](CORE-HANDOFF.md) for the exact run and test commands. `services/api/requirements.txt` is the backend dependency file; use `npm ci` in `frontend`. Avoid installing the old root `requirements.txt` or initializing a model while working on the core product.

The legacy `.env.example` mentions Gemini. That is not a requirement for these tasks. Do not obtain paid keys or copy Anurag's `.env`. Model fixtures unblock local work; only Anurag validates Orin.

## Receive the collected data

Anurag will share the data separately; a clone does not contain the complete corpus. Follow [Data handoff](DATA-HANDOFF.md). Keep the supplied source copy unchanged and place working indexes/output elsewhere. Each teammate reports what files are actually present before relying on them.

Inspection of the platform lead's checkout `data/` folder on 2026-10-30 and 2026-10-31 found approximately 44 KB: tracked prompt templates/taxonomy and empty artifact folders. It did **not** expose collected researcher JSON, research cards, populated Chroma, PDFs or a SQLite database. This is a limitation of that folder, not a claim that Anurag has no collected data elsewhere. A teammate receiving a fuller copy must inspect that copy rather than repeat these counts.

## Continue a session

Use [the resume template](prompts/resume-ticket.md) when restarting. Keep durable notes in a ticket/PR or short `docs/qa/` handoff, not hidden conversation memory. Check current commits/contracts before resuming; teammates may have merged changes meanwhile.

A first session should produce an owned code/test slice or a precise environment/access blocker plus independent progress. It should not end with an architecture rewrite, a new security project or a list of tasks someone else must do first.
