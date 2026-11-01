# Real drafting acceptance criteria

Status: criteria defined; T1's reviewed excerpts are **not ready**. No source
identities, expected research facts or real-model results are invented here.
The current scripted cases prove workflow behavior, not Qwen drafting quality.

## Approved input pack

T1 supplies a small fixed set of representative excerpts covering methods,
measurements, findings and limitations from actual approved sources. Prefer three
to five useful excerpts over a large collection of thin metadata. Publication
titles, author lists or research-topic keywords alone cannot support claims about
experimental methods or results.

For every excerpt, retain the existing `SourceSnapshot` identity and provenance:
actual source UUID, immutable version, SHA-256 of the exact normalized UTF-8 text,
title, origin and source text. Preserve any original PDF hash separately. T1
confirms public/approved use, extraction accuracy and the text/version mapping.
Unknown identity, affiliation, availability or reuse rights stay unknown.

Each case has a review sheet containing:

- Case ID, drafting instruction and selected source references.
- Expected facts: each fact linked to a selected source and an exact supporting
  quote, with the necessary study context and qualification.
- Forbidden claims: unsupported causal conclusions, invented numbers, outcomes,
  affiliations or generalizations identified by the source reviewer.
- Expected result: supported suggestion or explicit insufficient evidence.
- T1's source review and the platform lead's acceptance review, recorded separately.

This is an evaluation input format, not a change to the application DTOs. T1 and
the platform lead review the populated sheets before the first scored run.
Store annotations in a separate working/output directory. Never edit, replace,
reset or reindex the received source snapshot to prepare the pack. Do not commit
full source dumps, prompts, credentials or unapproved excerpts.

## Fixed quality cases

| Case | Instruction and expected behavior | Failure that blocks acceptance |
|---|---|---|
| Q1: single source | Explain a documented method using only its stated facts and limitations. | Added steps, fabricated findings or missing qualification. |
| Q2: two sources | Combine complementary evidence, citing each source for its own contribution. | A claim is attributed to the wrong study, or synthesis invents a new finding. |
| Q3: missing evidence | Ask for a result the selected excerpts do not establish. | Confident invented answer, unsupported number or outside knowledge presented as evidence. |
| Q4: numeric fidelity | Preserve relevant units, duration, population and measured quantities. | Changed units, swapped quantities, false precision or an invented effect size. |
| Q5: uncertainty | Describe preliminary/correlational evidence with its stated limitations. | A hypothesis becomes a demonstrated result, or correlation becomes causation. |
| Q6: differing findings | Preserve disagreement or differences in study context when T1 provides suitable sources. | Differences are silently erased or one result is generalized to both studies. |

An unavailable case is recorded as missing, never passed. T1 must provide suitable
inputs for the fixed set before it can serve as a release gate. Instructions
embedded in source text remain quoted data; they do not authorize tools, external
facts or changes to the requested task.

## Two distinct judgments

**Structural validity:** use the existing drafting service and validator. The
response must be complete valid JSON with the required types. Citations use only
the selected UUIDs; source versions/hashes match captured snapshots; support
quotes occur verbatim; inline markers match references; duplicate or invented
references fail. Truncation and malformed responses fail safely. A missing-evidence
result carries no citations and displays the canonical insufficiency message.

**Claim support:** inspect each factual sentence against the actual excerpt and
its context. Every factual statement needs support; the quote must support that
specific statement. Exact quote membership alone is insufficient. Preserve
uncertainty and numeric meaning, and reject every forbidden claim. Proposed work
must be distinguishable from a source's observed results.

The release gate requires both judgments to pass for every available fixed case,
and no required cases missing. Any unsupported claim or incorrect quantity blocks
acceptance, even when citation JSON is valid. These criteria are a small acceptance
set, not a population-level accuracy benchmark.

## Real Orin execution

When the approved pack and Orin are available:

1. Observe the actual served model/configuration and reachability. Keep one local
   model and the existing provider; do not swap models or use cloud fallback.
2. Run the fixed instructions through persisted API jobs and the real worker.
   Count the served chat template, enforce 8192 input tokens, request at most 512
   output tokens and retain the 120-second worker deadline. Fixture byte counts
   and Ollama token estimates do not prove these Orin limits.
3. Record each attempt: case/job ID, source refs, proposal/base revision, actual
   model ID, state/error category, tokenizer count, reported usage if available,
   queue time and generation time. Missing usage remains unknown.
4. Record structural and source-review judgments separately. Inspect output in
   the controlled workspace; evidence summaries omit full source/prompt dumps.
5. Keep failures and retries in the record. Do not turn a successful retry into a
   claim that the original attempt passed. Report the full denominator and the
   latency scope; do not mix fixture timing into inference results.
6. In the browser, inspect citations, accept a supported suggestion through the
   revision-checked save, and prove a newer collaborator save cannot be overwritten.

Current release gate: **pending approved T1 input and real Orin execution**.
