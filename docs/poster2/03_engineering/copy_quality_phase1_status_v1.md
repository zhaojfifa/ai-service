# copy quality phase1 status v1

## Scope

PR-10B only:

- annotation copy compression
- title / subtitle style normalization
- deterministic marketing-safe subtitle fallback
- Gemini optimizer quality hardening

Out of scope and unchanged:

- resend / attachments / email transport
- region bounds
- product ownership
- bottom mode
- feature suppression
- poster structure contract

## Positioning

This pass improves poster-facing and email-facing copy quality on top of the accepted poster2/template_dual_v2 baseline.
It is not a transport PR, not a geometry PR, and not a contract-expansion PR.

## What Changed

### Poster-facing text normalization

- title normalization now removes prompt-like noise, repeated punctuation, and trailing separator clutter
- subtitle normalization now treats subtitle as weak support copy and removes noisy lead-in phrasing
- feature / annotation text now passes through a rule-based compression layer before runtime budgets apply

### Annotation copy compression

- verbose sell-point phrasing is compressed into shorter business-safe points before poster runtime truncation
- representative examples:
  - `Feature: Fast preheat for busy weeknight cooking` -> `Fast preheat`
  - `Highlight: Even cooking with less guesswork` -> `Even cooking`
  - `Benefit: Easy cleanup after family dinners` -> `Easy cleanup`

This reduces avoidable truncation without changing annotation bounds, ownership, or geometry.

### Deterministic draft policy

- `subject` prefers clean `brand + title`
- `preview_text` prefers compressed product sell points
- if no sell points exist, subtitle is used only as normalized weak support fallback
- `summary_points` remain product-sell-point-driven
- `generated_from` remains explicit

### Gemini quality hardening

- Gemini remains optimizer only, not fact source
- prompt now instructs compact sell-point-first copy and blocks subtitle-only preview behavior when summary points exist
- optimizer output is normalized through the same clean-copy policy
- if Gemini returns no sell-point-driven summary when canonical summary points exist, fallback remains deterministic
- if Gemini only echoes subtitle as preview text while product sell points exist, fallback remains deterministic

## Validation / Tests

- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'email_draft or canonical_copy_input or product_annotation_copy_compression or gemini or deterministic_uses_clean_subtitle_fallback'`
  - `8 passed, 255 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py -k 'preview_uses_gemini_when_available or preview_falls_back_when_gemini_fails or preview_deterministic_uses_clean_subtitle_fallback_when_no_sell_points or preview_gemini_subtitle_echo_falls_back_to_deterministic'`
  - `4 passed, 19 deselected`
- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py`
  - `23 passed`

Representative records covered:

- dirty subtitle input
- clean product-features-only input
- Gemini failure / fallback input
- Gemini low-quality subtitle-echo input
- verbose annotation sell-point input

## Remaining Risks

- live Gemini output still needs deployed-environment review with real credentials
- compression rules are intentionally conservative and currently favor safe shortening over aggressive rewriting
- this pass does not change poster geometry or text budgets, so very poor raw copy can still exceed visual capacity after normalization

## One-line State

PR-10B copy quality phase 1 is complete: poster/email copy is cleaner, more sell-point-driven, less subtitle-dependent, and still deterministic when Gemini is unavailable or low quality.
