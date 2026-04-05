# email copy optimizer and optional attachment status v1

## Scope

- Gemini-backed email copy optimization on top of the existing `poster_record` path
- improved deterministic fallback draft policy
- backend-owned optional attachment assets:
  - `poster_png`
  - `poster_pdf`
- optional attachment wiring for the `resend` send path
- Stage3 source/docs mirror update for backend-driven draft source and attachment readiness

## Positioning

This round extends the existing Storage / Copy / Email Closure path.
It does not reopen poster structure contract, bottom truth, product annotation truth, renderer routing, or beautification.

Gemini is optimizer only.
It is never treated as fact source.
When Gemini is unavailable or fails, preview still returns a deterministic draft successfully.

## What Changed

### Copy optimization layer

- Added `app/services/email/copy_optimizer.py`
- Added `app/services/email/gemini_optimizer.py`
- canonical copy input is now built from `poster_record` truth:
  - `brand_name`
  - `agent_name`
  - `title`
  - `subtitle` as weak input only
  - product annotation summary points / stable feature text
  - final poster URL
- preview/send path now uses `build_email_draft_for_poster_record(...)`

### Deterministic vs Gemini draft policy

- Deterministic draft now prefers product annotation summary points over subtitle
- subject prefers `brand + clean title`
- preview text no longer blindly echoes subtitle when annotation summary is available
- draft metadata now records:
  - `generated_from`
    - `deterministic`
    - `gemini`
    - `gemini_fallback_deterministic`
  - `summary_points`
  - `tone`

### Attachment asset model

- Added `app/services/email/attachments.py`
- backend can build and persist:
  - `email_assets.poster_png`
  - `email_assets.poster_pdf`
- asset metadata is backend-owned and recorded in `poster_record`
- object storage is used when available; local fallback is used otherwise
- preview may build assets when `EMAIL_ATTACHMENT_BUILD_ON_PREVIEW=true`
- no binary/base64 blobs are exposed in API responses

### API shape changes

- `POST /api/v2/email/preview`
  - now returns:
    - `subject`
    - `preview_text`
    - `html`
    - `text`
    - `summary_points`
    - `tone`
    - `generated_from`
    - `email_assets`
    - `available_attachment_types`
    - `buildable_attachment_types`
- `POST /api/v2/email/send`
  - accepts optional `attachment_types`
  - preserves `inline_only` safe default
  - returns selected `attachment_types`
- `poster_record` now supports:
  - `email_draft`
  - `email_assets`
  - `email_deliveries`

## Validation / Tests

- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py` → `18 passed`
- `./.venv/bin/python -m pytest -q tests/test_stage3_email_closure_surface.py` → `2 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'email or poster_record or attachment or draft'` → `3 passed, 254 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `2 passed`

## Remaining Risks

- Gemini live output quality still needs deployed-environment review with real credentials
- `poster_pdf` and `poster_png` are backend-owned and inspectable, but local fallback assets remain server-local until object storage is configured
- `resend` attachment sending is ready, but still needs live environment validation against real provider credentials

## One-line State

poster2 email copy is now optimizer-aware with deterministic fallback, and resend is attachment-ready without changing poster contract truth.
