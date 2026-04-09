# Family A Bottom Region Practical Beautification And Observability v1

## Scope

This step is the second practical-closure pass for Family A.

It is limited to:

- Template A only
- bottom region only
- title / subtitle hierarchy polish
- title-band and gallery-shell polish
- dense-quad gallery item polish
- Stage2 bottom diagnostics visibility

It does not change:

- geometry
- ownership
- bottom mode structure
- Template B

## Objective

Make the Family A bottom region reviewable by operators instead of relying on blind visual tuning.

That means the practical closure must do both:

1. tighten the visual expression of title band / support copy / gallery shell
2. surface the bottom runtime truth that explains what the operator is seeing

## Runtime Truth To Surface

The Stage2 bottom panel must expose backend-controlled Family A truth for:

- `bottom_mode`
- `subtitle_slot.state`
- `title_slot_rendered`
- `subtitle_slot_rendered`
- `gallery_distribution_policy`

These are observability outputs only. They do not define bottom behavior.

## Beautification Boundaries

Allowed:

- title/subtitle hierarchy refinement
- subtitle support-copy kicker treatment
- title-band shell inset / outline refinement
- gallery strip shell inset / outline refinement
- dense-quad gallery item card treatment

Forbidden:

- title-band geometry drift
- gallery-strip geometry drift
- mode changes
- subtitle ownership changes
- gallery distribution logic changes

## Acceptance

This step is accepted only when:

1. title/subtitle hierarchy is visually clearer inside the existing title-band geometry
2. dense-quad gallery items read as a deliberate bottom evidence strip
3. Stage2 bottom diagnostics surfaces the five required fields
4. backend truth and UI diagnostics agree
5. no Template A control-truth regression is introduced
