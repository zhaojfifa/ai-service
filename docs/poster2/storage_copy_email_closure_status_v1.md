# Storage / Copy / Email Closure — Status v1

## 1. Scope

This document records the first completed closure pass for poster2 after the main poster structure was frozen.

Scope completed in this pass:

- `poster_record` persistence
- backend-generated `email_draft`
- Stage 3 restore / preview / send closure
- Resend-ready send path with safe default `inline_only`

Out of scope and intentionally unchanged:

- poster structure contract
- `bottom` geometry / behavior truth
- `product_annotation` ownership / contract truth
- beautification expansion
- editor-first mail composition

---

## 2. Positioning

This pass does **not** reopen poster layout engineering.
It is a closure slice that moves poster2 from:

> poster generated but disconnected from save / copy / send

into:

> poster generated, persisted, restorable, previewable, and sendable through a backend-owned flow.

The business chain is now treated as:

> input assets -> generate poster -> persist poster_record -> generate email draft -> operator review -> send email

---

## 3. What Changed

### Backend

Files:

- `app/config.py`
- `app/main.py`
- `app/schemas/poster2.py`
- `app/services/poster_records.py`
- `app/services/email/__init__.py`
- `app/services/email/drafts.py`
- `app/services/email/providers.py`
- `app/services/email/resend_provider.py`

Capabilities added:

1. `POST /api/v2/generate-poster`
   - now returns `poster_key`
   - persists `poster_record` after successful generation

2. `GET /api/v2/posters/{poster_key}`
   - restores persisted poster result and closure state

3. `POST /api/v2/email/preview`
   - generates backend-owned `email_draft` from `poster_record`

4. `POST /api/v2/email/send`
   - supports `delivery_mode=inline_only`
   - supports resend path when env is configured
   - persists provider send result (`provider_message_id / status / error`)

### Frontend / Docs mirror

Files:

- `frontend/app.js`
- `frontend/stage3.html`
- `docs/app.js`
- `docs/stage3.html`

Closure changes:

- Stage 2 now carries `?poster_key=...`
- Stage 3 restores by `poster_key`
- Stage 3 calls backend preview endpoint instead of generating copy in the browser
- sessionStorage remains cache-only, not truth-source

---

## 4. New Runtime Truth

### 4.1 Poster truth-source

`poster_record` is now the formal truth-source for closure flow.

Minimum stored surfaces:

- `poster_key`
- `created_at`
- `updated_at`
- `template_id`
- `trace_id`
- `final_hash`
- `final_poster`
- `request_snapshot`
- `render_result`
- `email_draft`
- `email_deliveries`

### 4.2 Email truth-source

Email draft and email send state are backend-owned.

Frontend is now limited to:

- restore
- preview
- light edit
- send trigger

Frontend no longer defines:

- canonical subject
- canonical preview text
- canonical HTML body
- canonical send target payload structure

---

## 5. Minimal Request / Response Shapes

### `POST /api/v2/generate-poster`

Request:

```json
{
  "brand_name": "ChefCraft",
  "agent_name": "Growth Team",
  "title": "Kitchen Upgrade",
  "subtitle": "Smart cooking for everyday use",
  "features": ["A", "B"],
  "product_image": {"url": "https://example.com/product.png"},
  "template_id": "template_dual_v2"
}
```

Response:

```json
{
  "poster_key": "p2_1234567890abcdef",
  "trace_id": "trace-123",
  "final_url": "https://example.com/final.png",
  "final_hash": "bbbb...",
  "template_id": "template_dual_v2"
}
```

### `GET /api/v2/posters/{poster_key}`

```json
{
  "poster_key": "p2_1234567890abcdef",
  "created_at": "2026-04-04T10:00:00+00:00",
  "updated_at": "2026-04-04T10:00:00+00:00",
  "template_id": "template_dual_v2",
  "trace_id": "trace-123",
  "final_hash": "bbbb...",
  "final_poster": {
    "filename": "trace-123-final.png",
    "media_type": "image/png",
    "storage_key": "trace-123",
    "url": "https://example.com/final.png"
  },
  "request_snapshot": {},
  "render_result": {},
  "email_draft": null,
  "email_deliveries": []
}
```

### `POST /api/v2/email/preview`

Request:

```json
{
  "poster_key": "p2_1234567890abcdef"
}
```

Response:

```json
{
  "poster_key": "p2_1234567890abcdef",
  "subject": "ChefCraft | Kitchen Upgrade",
  "preview_text": "Smart cooking for everyday use",
  "html": "<div>...</div>",
  "text": "ChefCraft poster is ready..."
}
```

### `POST /api/v2/email/send`

Request:

```json
{
  "poster_key": "p2_1234567890abcdef",
  "recipient": "user@example.com",
  "subject": "ChefCraft | Kitchen Upgrade",
  "preview_text": "Smart cooking for everyday use",
  "html": "<div>...</div>",
  "text": "ChefCraft poster is ready...",
  "delivery_mode": "inline_only"
}
```

Response:

```json
{
  "poster_key": "p2_1234567890abcdef",
  "provider": "inline_only",
  "delivery_mode": "inline_only",
  "status": "preview_only",
  "recipient": "user@example.com",
  "provider_message_id": null,
  "error": null
}
```

---

## 6. Root Cause Closed

Before this pass:

- Stage 3 still depended on frontend-inferred copy
- old `/api/send-email` path remained the effective mental model
- save / copy / send were not tied to a backend-owned record

This pass closes that by:

- moving closure truth into `poster_record`
- moving draft generation into backend services
- moving send state into backend persistence
- restricting frontend to restore / preview / light edit / send trigger

---

## 7. Acceptance Completed

Validated flow:

1. Stage 2 generates poster and returns `poster_key`
2. Stage 2 URL carries `?poster_key=...`
3. Continue to Stage 3 preserves `poster_key`
4. Stage 3 restores poster from `GET /api/v2/posters/{poster_key}`
5. Stage 3 loads backend-generated preview from `POST /api/v2/email/preview`
6. Light edits update the local preview panel only
7. `POST /api/v2/email/send` persists send result into `poster_record`
8. default `inline_only` path remains safe and non-destructive

Test evidence reported for this closure pass:

- `tests/poster2/test_api.py` -> `13 passed`
- `tests/test_stage3_email_closure_surface.py` -> `2 passed`
- `tests/test_stage2_guard_diagnostics_surface.py -k docs_publish_mirror_contains_same_guard_diagnostics` -> `1 passed`

---

## 8. Deployment Prerequisites For Ops Validation

Resend send-path validation requires deployment env to be present and correct.

Minimum send env:

```env
EMAIL_PROVIDER=resend
EMAIL_SEND_ENABLED=true
EMAIL_RECEIVE_ENABLED=false
RESEND_API_KEY=re_xxxxxxxxx
RESEND_DOMAIN=mail.swiftcraft.ai
EMAIL_FROM_NAME=ChefCraft
EMAIL_FROM_EMAIL=marketing@mail.swiftcraft.ai
EMAIL_REPLY_TO=sales@swiftcraft.ai
EMAIL_DEFAULT_ATTACHMENT_MODE=inline_only
```

This status doc does **not** assert resend production send is fully validated yet.
That remains an environment / deployment verification step.

---

## 9. Remaining Risk

### Open risk kept explicit

- resend formal send still needs deployment-environment proof
- `inline_only` remains the default safe mode by design

### Not considered open in this phase

The following are **not** treated as blockers for ops validation:

- bottom visual-contract debate
- poster structure redesign
- attachment-default support
- richer email editor UI
- beautification follow-up

---

## 10. Governance Outcome

This closure pass should be treated as:

> P0 closure complete; ready for operations validation.

Meaning:

- poster generation stays frozen at the existing contract truth
- storage / copy / email now have a formal backend-owned closure path
- next gate is ops validation, not more closure architecture work

---

## 11. One-line State

> poster2 main poster skeleton remains frozen; Storage / Copy / Email Closure is complete at P0 level; the next gate is operations validation of persisted restore, backend draft preview, and resend-backed formal sending.
