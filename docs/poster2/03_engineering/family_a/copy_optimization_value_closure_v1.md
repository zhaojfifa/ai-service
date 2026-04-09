# Family A Copy Optimization Value Closure v1

## Scope

Template A only.

This step tightens copy optimization from a pilot switch into an operator-reviewable tool with:

- real suggestion output
- real changed-field evidence
- accept / reject controls only when actionable
- complete lineage visibility in backend metadata and Stage2

Excluded:

- Template B
- geometry changes
- ownership changes
- control-truth changes
- renderer-defined truth

## Rules

- Gemini may optimize `title`, `subtitle`, and `annotation` text only
- Gemini may not define mode, ownership, geometry, or layout
- renderer executes backend-resolved truth
- Family A runtime remains the oracle

## Closure Requirements

When `mode = off`:

- backend still emits a non-empty `copy_optimization_review`
- UI does not show dead `Accept` / `Reject` controls
- UI shows a disabled reason

When `mode = suggest | apply`:

- backend must emit `optimized_text`
- `changed_fields` must reflect material copy differences
- UI and metadata both show:
  - `requested_text`
  - `sanitized_text`
  - `optimized_text`
  - `rendered_text`

## Practical Surface

This closure uses:

- backend `copy_optimization_review`
- Stage2 optimization summary panel
- operator accept / reject state
- fixed Family A annotation-count guard

## Acceptance

Accepted only when all hold:

1. `copy_optimization_review` is never an empty shell for Template A
2. mode-off runs show a disabled reason instead of dead controls
3. mode-on runs surface actual suggestion lineage and field diffs
4. accepted optimization changes copy only, not control truth
5. annotation count remains fixed
