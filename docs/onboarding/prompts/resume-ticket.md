# Resume an owned ticket

Fill in the bracketed values and paste this after opening the repo. Keep it with the matching teammate starter prompt.

```text
Resume workstream [Teammate 1 / Teammate 2 / Teammate 3 / Anurag], ticket [ID], branch [branch].
Read AGENTS.md, docs/design/17-v2-corrected-specification.md, docs/design/18-four-person-delivery-plan.md, docs/onboarding/DATA-HANDOFF.md and the matching starter prompt under docs/onboarding/prompts/.

Previous handoff: [ticket/PR/commit or short note].
Last verified behavior/tests: [actual command/result].
Open dependency: [contract/service/data input, or none].
Local data source: [actual received snapshot path, or not received].
Writable data output: [distinct working path].
Next owned slice: [specific behavior to implement].

Inspect git status/recent commits and actual current contracts first. Preserve others' changes and do not trust stale conversation state. Continue the next owned slice with focused checks; do not reopen the architecture/security scope. If a dependency is unavailable, make independent progress using an explicit fixture and report exactly what real validation remains. Do not push or open a PR unless I request it.
```
