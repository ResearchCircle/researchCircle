# Team startup and copy-paste prompts

**Current implementation:** read [the core handoff](CORE-HANDOFF.md) first. Named
accounts, proposals/sources, public records, shortlists, persisted jobs, editor,
tracking records and local runtime now exist. Collaboration Hub, graph visualization
and previous research chat are retained code awaiting [explicit restoration](../design/23-v2-remaining-feature-restoration.md).

Updated 2026-11-01. Always use `anurag/latest` as the current shared team base. The goal is a working research platform; advanced security follows later.

## Which prompt to use

Paste the complete code block from the matching file into a new coding session opened at the repository root. The prompt tells the session to read the shared project rules and then start the next open work for that role.

| Person | Starter prompt | Starts with |
|---|---|---|
| Teammate 1 | [Data and discovery](prompts/teammate-1-data-discovery.md) | Real data snapshot import, then collaborator matching |
| Teammate 2 | [Workflow backend](prompts/teammate-2-backend-workflow.md) | Backup/membership checks on the current schema, then dependency lock |
| Teammate 3 | [Frontend and user journey](prompts/teammate-3-frontend.md) | Member management UI, then wider browser coverage |
| Anurag | [Orin and drafting](prompts/anurag-orin-drafting.md) | Real Orin quality/browser acceptance, then chat-provider integration |

## Get the checkout

On a new machine, clone `https://github.com/anurag2796/tiger_research_buddy.git` using your authorized GitHub account, with branch `anurag/latest`. On an existing checkout, inspect `git status` first; fetch and fast-forward only if clean. Do not discard local work or force a diverged branch into place. If an old checkout cannot see this branch, inspect `git remote -v` and confirm the repository before changing remotes.

```sh
git clone --branch anurag/latest https://github.com/anurag2796/tiger_research_buddy.git
cd tiger_research_buddy
git status --short
git branch --show-current
```

For work, fetch origin and create a role/ticket branch from current `origin/anurag/latest`, such as `teammate-1/d-p2-matching`, `teammate-2/backup-smoke` or `teammate-3/member-ui`. Target ticket reviews/PRs at `anurag/latest`. The prompts request local implementation, not a direct push to a shared branch. Ask the human only for genuinely missing access/input; do not pause routine work for repeated confirmations.

## Local setup expectations

Use Python 3.12 and Docker with Compose. Follow [the core handoff](CORE-HANDOFF.md) for the exact run and test commands. `services/api/requirements.txt` is the backend dependency file; use `npm ci` in `frontend`. Avoid installing the old root `requirements.txt` or initializing a model while working on the core product.

The legacy `.env.example` mentions Gemini. That is not a requirement for these tasks. Do not obtain paid keys or copy Anurag's `.env`. You do not need access to Anurag's machine, homelab or Orin. Fixture inference covers most work; for real-model testing, run a small Ollama model on your own machine as described in [the core handoff](CORE-HANDOFF.md). Only Anurag validates Orin.

## Receive the collected data

Anurag will send the data folder directly (about 10 GB); a clone does not contain the corpus. Follow [Data handoff](DATA-HANDOFF.md). Keep the supplied source copy unchanged and place working indexes/output elsewhere. Each teammate reports what files are actually present before relying on them.

Without it, a checkout's `data/` holds only tracked prompt templates and a taxonomy. Each teammate reports what files are actually present before relying on them.

## Continue a session

Use [the resume template](prompts/resume-ticket.md) when restarting. Keep durable notes in a ticket/PR or short `docs/qa/` handoff, not hidden conversation memory. Check current commits/contracts before resuming; teammates may have merged changes meanwhile.

A first session should produce an owned code/test slice or a precise environment/access blocker plus independent progress. It should not end with an architecture rewrite, a new security project or a list of tasks someone else must do first.
