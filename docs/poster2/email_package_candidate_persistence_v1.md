# Email Package Candidate Persistence v1

Task: **POSTER2-EMAIL-PACKAGE-CANDIDATE-PERSISTENCE-V1**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.

Lets both route packages (Fiche / Affiche) coexist, be compared, and be selected at send time — minimal and
deterministic. No body redesign, no banner polishing, no send-provider rebuild, no `products[]`, no batch/customer
send, P2A demo untouched.

---

## 1. Why a single selected visual was insufficient

The operator workflow is: generate Fiche → generate Affiche → **compare both** → pick one → send. With only a scalar
`selected_email_body_visual`, switching modes made the other route's package feel lost / not directly sendable, and the
send response did not state *which* package was sent. (Underneath, both candidates already coexisted in
`poster_candidates`; what was missing was a surfaced **package layer** + explicit send selection + staleness.)

## 2. New email package candidate model

A read-only endpoint exposes both packages, built from the same deterministic assembly as preview/send (no
reconstruction):

```
GET /api/v2/workbench/{workbench_key}/email/packages
-> { workbench_key, selected_email_body_visual, content_updated_at, workbench_updated_at,
     email_package_candidates: { fiche: {...}, affiche: {...} } }
```

Each candidate: `package_type, status, preview_ready, send_ready, subject, preview_text, html, text, body_visual_url,
container_profile, container_visual_variant, banner_variant, missing_required_fields, package_updated_at,
content_updated_at, workbench_updated_at, is_stale, staleness_status, stale_reason, source_content_version,
package_content_version`.

## 3. Fiche package fields

```
poster_key = null, uses_poster_generation = false, generated_from = workbench_truth,
supporting_media_count, product_image_count, gallery_image_count, container_visual_variant = ttt_product_sheet_container
```

## 4. Affiche package fields

```
poster_key, standalone_poster_url, email_body_visual_url, email_body_visual_contract_pass,
available_attachment_types, container_visual_variant = ttt2_campaign_container
```

## 5. Switching behavior

Both candidates persist independently in `poster_candidates`; selecting Fiche never deletes the Affiche package and
vice-versa (verified by `test_switching_selection_keeps_both_packages`). Regenerating the **currently selected**
candidate still clears the scalar selection (existing deterministic rule), but the other route's package is untouched.

## 6. Send-time selection behavior

```
WorkbenchEmailSendRequest.selected_email_package (optional) MUST equal the persisted selected route -> else 422
  selected_package_mismatch (unambiguous send).
The trial UI's "发送这个版本" PATCHes /selected-visual to that route, then sends with selected_email_package=<route>.
Send response now reports: sent_package_type, selected_email_body_visual, body_visual_poster_key,
  container_visual_variant, real_email_sent (true only with a provider_message_id).
```

The send path itself is unchanged (same provider, same `_resolve_workbench_email_package`, byte-identical to preview).

## 7. Staleness / maybe-stale behavior

```
content_version : a monotonic counter bumped ONLY when product_truth / product_assets / email_banner change
                  (NOT on selection or candidate generation) — robust to same-second timestamps.
each candidate captures the content_version it was generated against.
staleness_status = maybe_stale  when  package_content_version < workbench content_version  (content changed after gen)
                 = fresh        otherwise
also surfaced for display: content_updated_at, package_updated_at, workbench_updated_at, stale_reason.
```

A stale package is flagged (not silently sent with old content); the operator re-generates it from Step 2.

## 8. Banner decision

```
The current banner is ACCEPTED as the interim internal-baseline-testing default (brand_standard_header /
campaign_poster_header). The FINAL brand-level banner requires designer-provided Brand Standard Header and Campaign
Poster Header assets/spec (see banner_asset_audit_and_design_brief_v1.md — no usable CUISTANCE banner master exists
in the source assets). No banner polishing was done in this task.
```

## 9. Remaining HOLD

```
customer send                HOLD
customer batch send          HOLD
products[] / multi-product   HOLD
P2A demo backend mapping     HOLD
final designer banner assets HOLD (designer brief delivered; awaiting assets)
```
