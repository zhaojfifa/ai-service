# CUISTANCE Email Poster Trial — Baseline v1

Status: **first internally-testable baseline — NOT a final product release.**
Branch: `trial/poster2-cuistance-psd-email-container-last-mile-v1`.
Tag: `poster2-cuistance-email-trial-baseline-v1` (local annotated tag; **not pushed** unless the Owner authorizes).

---

## 1. Branch and HEAD commit

```
branch : trial/poster2-cuistance-psd-email-container-last-mile-v1
HEAD   : c4b988a (this baseline doc commit is on top; the tag targets the baseline-doc commit)
```

Key commits in this baseline:

```
c4b988a docs: email package send binding remote verify (PASS — Affiche sends Affiche)
8aa7ba8 fix : bind send action to selected email package (P0 send-binding fix)
ce28295 feat: persist email package candidates for send selection
a0087d4 feat: migrate cuistance email containers to ttt references
920a5ac fix : make cuistance banner a composite module
7e16d66 fix : finalize banner product variants (designer review -> recommend designer base)
01ad5b8 docs: audit banner assets (no usable CUISTANCE banner master; designer brief)
```

## 2. Tag name

```
poster2-cuistance-email-trial-baseline-v1
```

## 3. What is accepted (internally testable)

```
- Fiche / simple product sheet email route (basic test route)
- Affiche / target poster email route (basic test route)
- ttt / ttt2 email container migration (ttt_product_sheet_container, ttt2_campaign_container)
- internal REAL send via the shared mainline Resend provider (owner/test-gated; provider_message_id proven)
- email package candidate comparison layer (both routes coexist; GET /email/packages)
- send-time package selection bound to the chosen package (sent_package_type verified; P0 fixed)
- staleness (maybe_stale) signal via monotonic content_version
- replaceable banner/header module with logo/contrast/fallback diagnostics
```

Remote-verified PASS: Fiche/Affiche previews, package compare, send-time selection, Affiche real send
(`provider=resend`, `provider_message_id` present), mismatch guard (`422 selected_package_mismatch`).

## 4. What is only interim

```
- Banner / header VISUAL: brand_standard_header (Fiche) / campaign_poster_header (Affiche) are clean and route-correct
  but reviewed as PASS_WITH_NITS — a flat dark plate, not a premium designer banner (see designer review v1).
- Body layout polish: ttt/ttt2 containers are accepted for body/layout; further refinement is optional.
- Copy quality: subject/intro/CTA are deterministic from truth (Gemini optimizer bounded by the truth contract);
  copy is functional, not finely tuned.
```

## 5. Remaining HOLD

```
- customer send                 HOLD
- customer batch send           HOLD
- products[] / multi-product     HOLD
- P2A demo backend mapping       HOLD
- final designer banner assets   HOLD (no usable CUISTANCE banner master exists in source; designer brief delivered)
```

## 6. Next optimization tracks

```
1. Banner design assets — commission the designer Brand Standard Header + Campaign Poster Header master
   (the only path from PASS_WITH_NITS to premium native; engineering ceiling reached on a solid plate).
2. AI copy optimization under the truth boundary — improve subject/intro/CTA quality while never mutating
   product_truth / confirmed parameters (post-sanitization + grounded-claim rejection stay in force).
3. Container visual refinement — minor ttt/ttt2 spacing/typography polish once the banner master lands.
4. Product / input UX refinement — material intake + truth/parameter editing flow (P2 demo direction, still HOLD
   for backend mapping).
```

## 7. Evidence summary

```
- internal Resend real send EXISTS and is proven (e.g. provider_message_id b2c8b594-... at remote verify v1).
- Fiche/Affiche preview + package compare + send-time selection flows EXIST and are remote-verified.
- NO customer send; NO batch send; real send is owner/test-gated (confirm_send + delivery_mode=resend + provider env).
- Banner asset audit: NO usable CUISTANCE banner master in source (PSD top banner is Technitalia/Codimatel);
  only logo_01.jpg (logo-only). Designer brief written.
```

This baseline is suitable for **internal trial testing**, not customer rollout.
