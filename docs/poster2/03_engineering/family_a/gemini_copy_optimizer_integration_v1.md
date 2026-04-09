# Family A Gemini Copy Optimizer Integration v1

## Scope

This step is bounded to Family A practical closure only.

Included:

- Template A title optimization trace
- Template A bottom support-copy subtitle optimization trace
- Template A annotation copy optimization trace
- operator accept / reject state
- backend metadata + Stage2 diagnostics visibility

Excluded:

- Template B
- geometry changes
- ownership changes
- control-truth changes
- renderer-defined truth

## Oracle

Family A runtime remains the oracle:

- `template_id = template_dual_v2`
- `hero_mode = scenario_cover_product_contain`
- `feature_mode = product_anchor_callouts`
- `product_annotation_mode = product_anchor_callouts`
- `bottom_mode = title_gallery_split`
- `gallery_mode = strip_local_visible_only`

Gemini may optimize copy only.
Gemini may not define layout, geometry, ownership, region order, or behavior mode.

## Integration Surface

The optimizer path is intentionally narrow and explicit:

1. request carries `copy_optimization`
2. pipeline builds a Family A-only `copy_optimization_review`
3. rendered text stays on backend-approved truth
4. Stage2 shows the lineage and stores operator accept / reject state

## Lineage Requirements

Each optimized Family A text surface must preserve:

- `requested_text`
- `sanitized_text`
- `optimized_text`
- `rendered_text`

For this step, the optimized surfaces are:

- `title`
- `subtitle`
- `annotation_items`

## Operator Contract

Stage2 may send:

- `mode = off | suggest | apply`
- `decision = pending | accepted | rejected`
- accepted title / subtitle / annotation overrides

Accepted overrides are advisory copy inputs only.
They do not change behavior modes or ownership.

## Control Guards

- annotation feature count may not increase
- optimization may rewrite existing annotation copy only
- renderer consumes the resolved text truth
- metadata remains backend-owned

## Acceptance

Accepted only when all hold:

1. Family A output keys remain stable
2. copy optimization review is emitted from backend
3. Stage2 exposes optimization trace
4. operator can accept / reject optimization without changing control truth
5. Template B remains untouched
