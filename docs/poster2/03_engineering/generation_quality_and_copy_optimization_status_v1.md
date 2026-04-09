# generation quality and copy optimization status v1

## Scope

- poster-facing copy sanitization for title / subtitle / features / annotation-derived text
- deterministic draft quality improvement
- Gemini optimizer quality tightening
- explicit deterministic fallback preservation

This round does not reopen:

- resend send logic
- attachment transport
- poster contract structure
- bottom geometry
- product geometry
- header geometry
- beautification expansion

## Positioning

Storage / Copy / Email Closure is already accepted.
This round tightens marketing copy quality only.

Gemini remains optimizer only.
It is not a fact source.

## What Changed

### Sanitization layer

Added:

- `app/services/email/copy_safety.py`

This layer now:

- normalizes poster-facing text
- strips prompt-like / internal / training / copilot-like text from title, subtitle, features, and annotation sources
- preserves clean product-selling language
- guards against ungrounded marketing claims in optimized output:
  - pricing
  - shipping / delivery promises
  - certification claims
  - warranty / guarantee claims

### Deterministic copy policy

Updated:

- `app/services/email/drafts.py`
- `app/services/email/copy_optimizer.py`

Deterministic draft policy now:

- keeps `subject` on `brand + clean title`
- treats subtitle as weak input only
- prefers product-owned sell points for `preview_text`
- builds `summary_points` from sanitized product annotation items and clean features
- avoids mechanically echoing dirty subtitle text into preview copy

### Gemini quality policy

Updated:

- `app/services/email/gemini_optimizer.py`
- `app/services/email/copy_optimizer.py`

Gemini prompt now explicitly:

- rewrites only provided facts
- prefers `summary_points` over subtitle
- treats subtitle as weak support text
- forbids invented specs, pricing, certification, shipping, delivery promises, offers, or extra claims
- aims to be cleaner than the deterministic base

Gemini post-processing now:

- sanitizes returned subject / preview / text / html / summary points
- rejects ungrounded risky claims
- falls back to deterministic when Gemini output is unsafe or not materially better

## Deterministic vs Gemini Policy

- `deterministic`
  - always available
  - business-safe
  - product-sell-point-first
- `gemini`
  - only accepted when sanitized and materially better than deterministic
- `gemini_fallback_deterministic`
  - used when Gemini fails, times out, invents risky claims, or does not materially improve the base copy

## Validation / Representative Cases

Covered at least these representative records:

1. dirty subtitle input
   - prompt-like / system-like subtitle is stripped
   - preview text stays product-sell-point-driven
2. clean product features only
   - preview text and summary points come from clean product features
3. Gemini failure / fallback
   - preview still succeeds
   - deterministic fallback remains stable
4. Gemini success path
   - optimized copy is visibly cleaner than deterministic base
5. Gemini unsafe-claim path
   - invented delivery / certification / shipping style claims are rejected back to deterministic

## Files Changed

- `app/services/email/copy_safety.py`
- `app/services/email/drafts.py`
- `app/services/email/copy_optimizer.py`
- `app/services/email/gemini_optimizer.py`
- `tests/poster2/test_api.py`
- `tests/poster2/test_pipeline.py`
- `docs/poster2/current_branch_execution_log_v1.md`
- `docs/poster2/generation_quality_and_copy_optimization_status_v1.md`
- `docs/poster2/README.md`
- `CLAUDE.md`

## Validation / Tests

- `./.venv/bin/python -m pytest -q tests/poster2/test_api.py` → `21 passed`
- `./.venv/bin/python -m pytest -q tests/test_stage3_email_closure_surface.py` → `2 passed`
- `./.venv/bin/python -m pytest -q tests/poster2/test_pipeline.py -k 'email or poster_record or attachment or draft'` → `5 passed, 255 deselected`
- `./.venv/bin/python -m pytest -q tests/test_frontend_docs_sync.py` → `2 passed`

## Remaining Risks

- live Gemini quality still needs deployed-environment review with real credentials
- current sanitizer is intentionally conservative; some borderline product copy may be dropped if it looks too prompt-like
- this round does not cover send-provider transport quality or deployment-side deliverability

## One-line State

poster2 marketing copy now sanitizes dirty poster-facing text before draft generation, prefers product sell points over subtitle, and accepts Gemini output only when it is cleaner and safely grounded.
