# A-P1 local model provider handoff

A-P1 supplies a tested provider boundary, a deterministic completion fixture and
a smoke command. It does not implement API job routes, persistence, a worker or
selected-source drafting. Shared contracts are unchanged.

This is the original A-P1 record. Subsequent drafting/controller work and current
integration status are documented in [HANDOFF.md](HANDOFF.md). The A-P1 test count
below describes that earlier slice; run the full suite for the current count.

## Setup and fixture demo

From the repository root, use Python 3.12. This slice requires only the standard
library; no package install, model download, paid key or Orin access is needed.
Do not install the legacy ML dependency set for this demo.

```sh
python3.12 -m venv .venv
.venv/bin/python -m scripts.orin.smoke
.venv/bin/python -m unittest discover -s tests/platform -v
```

The tests run a temporary loopback HTTP server. Restricted environments must allow
loopback bind/connect for those tests. This is a provider-only setup, not a full
application installation.

```python
from dataclasses import asdict
from src.platform.models.fixtures import FixtureModelProvider
from src.platform.models.provider import ModelProvider, ProviderError

provider: ModelProvider = FixtureModelProvider()
try:
    result = provider.generate("Draft a short section", max_output_tokens=64, timeout_s=30)
except ProviderError as error:
    body = {"error": {"code": error.code, "message": str(error), "retryable": error.retryable}}
else:
    body = asdict(result)
```

`generate(prompt, max_output_tokens, timeout_s)` is synchronous and intended for
the background worker, not the API request/event loop. `ModelResult` contains
`text`, `model_id`, nullable `usage` (`prompt_tokens`, `completion_tokens`,
`total_tokens`) and `finish_reason`. `length` means output was truncated and must
remain visible to consumers. Token usage is returned only when supplied by the
server; it is never estimated. The fixture returns the same canned text and null
usage for every valid call. It validates arguments but does not perform inference,
tokenization, budget simulation or evidence/citation validation.

Both providers reject empty prompts, noninteger/output budgets outside 1–512,
and nonfinite/timeouts outside (0, 120] seconds with `ValueError`. The local adapter
sends `max_tokens`, temperature zero and non-streaming chat to the configured model.
It rejects missing/empty/malformed completions and unexpected model identifiers.
The exact 8192-input-token limit requires the served model's tokenizer/prompt
assembly in A-P2; A-P1 does not claim to enforce it.

## Existing Orin service

Observed on 2026-10-31 UTC (2026-10-30 America/New_York):

| Setting | Observed value |
|---|---|
| Model API on Orin | `http://127.0.0.1:8000/v1` |
| Served model ID | `homelab-llm` |
| Model path | `/models/qwen3-coder-30b-a3b-awq` |
| Container / image tag | `vllm` / `vllm:0.20.0-orin` |
| Quantization | `compressed-tensors` |
| Context capacity | `262144` (server capacity, not the product input limit) |
| KV cache / GPU fraction | `fp8` / `0.78` |
| Tool parsing | auto tool choice, `qwen3_xml` |
| Request logging | `--no-enable-log-requests` |
| Admission before smoke | 0 running, 0 waiting in `/metrics` |

These values came from `/v1/models`, `docker ps`, the container's launch arguments
and `/metrics`. No model was swapped, restarted or reconfigured. The image tag is
an observed tag, not a pinned immutable image digest.

Only the platform lead needs this optional hardware check. Keep the model API
internal; teammates use the fixture. From the lead's workstation, open a temporary
tunnel using the existing authorized SSH alias:

```sh
ssh -o BatchMode=yes -o ExitOnForwardFailure=yes \
  -L 127.0.0.1:18080:127.0.0.1:8000 -N orin
```

In another terminal, from this repository:

```sh
.venv/bin/python -m scripts.orin.smoke --provider local \
  --base-url http://127.0.0.1:18080/v1 --model-id homelab-llm \
  --max-output-tokens 32 --timeout-s 30
```

Close the tunnel with Ctrl-C afterward. The adapter accepts explicit HTTP `/v1`
endpoints on localhost, private IP literals or the tailnet IP range; use a tunnel
for hostnames. It ignores proxy environment variables, never follows redirects,
never substitutes a model, never retries automatically and has no cloud fallback.
It exposes only fixed error messages, never server bodies, prompts or credentials.

One real completion through this interface returned:

```json
{"provider":"local","elapsed_s":0.408505,"result":{"text":"Local provider ready.","model_id":"homelab-llm","usage":{"prompt_tokens":68,"completion_tokens":5,"total_tokens":73},"finish_reason":"stop"}}
```

Latency is one observed round trip through SSH, not a throughput benchmark or a
512-token drafting measurement. The prompt is a tiny synthetic connectivity check
embedded in `smoke.py`. This proves provider completion, not research quality or
the complete browser workflow. The temporary tunnel was closed after this check.

## Errors and worker boundary

| Code | Meaning | Retryable |
|---|---|---|
| `provider_unavailable` | connection/transport failure or server 5xx | yes |
| `provider_busy` | server HTTP 429 | yes |
| `provider_timeout` | deadline expired; server may still be computing | yes |
| `provider_rejected` | other non-200 rejection | no |
| `provider_redirect` | server attempted redirect | no |
| `provider_invalid_response` | invalid JSON/completion/model/usage | no |

`retryable` means a user may eventually retry, not that the caller should repeat
inference immediately. A timeout closes the client socket and does **not** confirm
that server inference stopped. Likewise, cancellation of a wrapper thread/task
does not stop this synchronous call. A-P3 must retain the generation slot until
completion or confirmed server abort; neither cancellation nor a UI timeout may
admit another generation while the old one runs. No worker/admission guarantee is
claimed by this provider alone. Current limits for that integration remain one
generation, four queued jobs, one queued/running job per user and a 120-second
worker deadline; a persisted restart must mark abandoned jobs interrupted.

## T1 / T2 / T3 handoff

[`fixtures.json`](fixtures.json) publishes the provider result and four snapshots
of one **synthetic** DraftJob (`queued`, `running`, `succeeded`, `failed`). UUIDs and
timestamps are synthetic. `source_refs` and citations are empty intentionally;
this fixture provides no evidence for a research claim. The job field names are a
proposal for T2/T3 review, not a frozen shared DTO or an implemented `/api/v2` route.

- **T1 request for A-P2:** supply one small public, source-linked sample with stable
  source UUID, version/content hash, title, origin URL, selected snippet/text and
  expected supported claim. Identify its provenance and usable text; no full corpus
  dump or re-crawl is needed. The visible immutable snapshot contains 9 files,
  21,141 bytes: `.gitkeep`, 7 prompt Markdown files and one taxonomy JSON object
  (`domains`, `fallbacks`). No collected paper/researcher records were present.
- **T2 review request:** agree the minimal `DraftJob` example fields, nullable
  output/error shape and `source_refs` versions before moving them into shared
  contracts. Capture `base_revision` and exact sources at job creation; retain
  membership checks, persistence and routes in the backend workstream. Map safe
  provider errors to `{error: {code, message, retryable}}`.
- **T3 integration:** use `model_result`/job snapshots for UI states now. Fixture
  success is integration scaffolding. Show insufficient evidence, missing usage
  and truncated output truthfully. Accept suggestions through the normal
  revision-checked proposal save; never overwrite a newer revision automatically.

Next owned ticket: A-P2 selected-source prompt assembly and citation validation
using T1's reviewed sample. A-P1 has no blocking hardware dependency. Consumer DTO
review, source evidence, job persistence and browser integration remain pending.

## Verification record

Python 3.12.7, standard library only; no dependency manifests/locks changed.
The new tests first failed because the provider/smoke/fixtures were absent, then
passed after implementation. Initial loopback test execution was denied by the
restricted environment; rerunning with loopback access passed. The initial baseline
had no `tests/platform/` directory, so no pre-existing platform suite was available.

The focused suite covers deterministic fixtures, invalid arguments, actual HTTP
request/result shape, refused connections, timeouts, HTTP errors/redirects, model
mismatch, malformed/oversized output, usage and truncation, plus CLI and published
fixture consistency. Final command: `.venv/bin/python -m unittest discover -s
tests/platform -v` — 15 tests passed. Review also reproduced and fixed three edge
cases: deeply nested JSON escaping typed errors, explicit port zero becoming port
80, and enormous timeout integers raising overflow instead of validation errors.
Each fix was checked with a failing regression before the final passing suite.
No full legacy ML suite, database, frontend or browser test is claimed here.
