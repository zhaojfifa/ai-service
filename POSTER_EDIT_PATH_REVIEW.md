# Poster Edit Path Review

## Intended normal path

For kitposter requests (`render_mode` like `kitposter1_a` / `kitposter1_b`), the intended path is:

1. `app.main.generate_poster()` receives the request and detects kitposter mode (`app/main.py:1079-1098`).
2. It calls `run_kitposter_state_machine()` (`app/services/glibatree.py:1548-1611`).
3. That delegates to `generate_poster_asset()` (`app/services/glibatree.py:1533-1545`, `1572-1585`).
4. `generate_poster_asset()` prepares a deterministic `locked_frame` and mask (`app/services/glibatree.py:1882-1884`).
5. Because it is kitposter, it calls `_generate_poster_with_vertex(..., force_edit=True)` (`app/services/glibatree.py:1935-1947`).
6. `_generate_poster_with_vertex()` sets `should_edit=True` (`app/services/glibatree.py:933`) and calls `client.edit_bytes(...)` (`966-977`).
7. `VertexImagen3.edit_bytes()` should use the edit model to modify only the masked area, then the code overlays the locked frame again via `_apply_locked_frame()` (`app/services/vertex_imagen3.py`, `app/services/glibatree.py:1025`).
8. The result is uploaded and returned in `GeneratePosterResponse`.

That is the intended “edit pipeline”.

## Actual current runtime path

Based on the provided runtime observation and the inspected code, the actual path is:

1. `generate_poster()` and `run_kitposter_state_machine()` execute normally.
2. `generate_poster_asset()` reaches the Vertex kitposter branch and calls `_generate_poster_with_vertex(..., force_edit=True)`.
3. `_generate_poster_with_vertex()` calls `client.edit_bytes(...)`.
4. `VertexImagen3.edit_bytes()` immediately aborts because edit support is disabled:
   - `if not self.enable_edit or self._edit_model is None: raise RuntimeError(...)`
   - source: `app/services/vertex_imagen3.py:245-248`
5. `generate_poster_asset()` catches that exception and converts it into:
   - `warnings.append("vertex_edit_failed_fallback")`
   - `degraded = True`
   - `degraded_reason = "edit_model_not_enabled"` when the message matches the disabled-edit branch
   - source: `app/services/glibatree.py:1962-1971`
6. Since `primary` is still `None`, kitposter enters the local locked-frame fallback:
   - `warnings.append("kitposter1_locked_frame_fallback")`
   - render a filled template via `_render_template_frame(..., fill_background=True)`
   - source: `app/services/glibatree.py:1977-1997`
7. The fallback image is still uploaded to R2 and returned successfully.

So the live service is currently “success with degraded local fallback”, not “success with edit pipeline”.

## Exact branch where fallback starts

The first fallback-triggering branch is the exception raised by `VertexImagen3.edit_bytes()`:

- `app/services/vertex_imagen3.py:245-248`

The first fallback-handling branch is:

- `app/services/glibatree.py:1962-1971`

The hard local locked-frame fallback begins here:

- `app/services/glibatree.py:1977-1997`

## Why `edit_model=None`

This is directly explained by `app/services/vertex_imagen3.py`:

- `self.enable_edit = os.getenv("VERTEX_IMAGEN_ENABLE_EDIT", "").lower() in {"1", "true", "yes"}` (`line 113`)
- `self.model_edit = self.model_edit_name if self.enable_edit else None` (`line 114`)
- if `self.enable_edit` is false, `_edit_model` is never loaded and stays `None` (`lines 130-137`)

Therefore, the current observed runtime state:

- `enabled=False`
- `edit_model=None`

is the expected code outcome when `VERTEX_IMAGEN_ENABLE_EDIT` is unset or false.

## Is this config, code path, or API incompatibility?

### Proven now

The first proven cause is configuration:

- the edit feature flag is disabled (`VERTEX_IMAGEN_ENABLE_EDIT` false/unset)

This is enough by itself to explain:

- `enabled=False`
- `edit_model=None`
- `vertex_edit_failed_fallback`
- `degraded=true`

### Not yet proven

The following are still possible but not yet proven from code/runtime:

1. `VERTEX_IMAGEN_MODEL_EDIT` may point to a model name unsupported by the current SDK/runtime.
2. The current SDK’s `edit_image` signature may not match the arguments the code passes.
3. The edit API path may still fail on mask/reference-image compatibility even after the flag is enabled.

Those are second-order risks. The current first-order blocker is the disabled feature gate.

## Exact warning sources for `POST /api/generate-poster`

Warning codes found in `app/services/glibatree.py`:

| Warning | Source | Trigger |
| --- | --- | --- |
| `scenario_fallback_used` | `1513-1517` | Added whenever `draft is not None`; currently not tied to a proven runtime fallback event |
| `creative_failed_fallback_to_stable` | `1586-1590` | Only when `quality_mode == "creative"` and first generation attempt raises |
| `vertex_quota_exhausted_fallback` | `1952-1957` | Vertex raises `ResourceExhausted` |
| `vertex_edit_failed_fallback` | `1962-1971` | Kitposter Vertex branch raises generic exception during edit/generate step |
| `vertex_unavailable_fallback` | `1978-1982` | Kitposter and `vertex_imagen_client is None` |
| `kitposter1_locked_frame_fallback` | `1983-1986` | Kitposter and no primary Vertex result is available |

These are the only warning strings proven by search in the current poster path.

## Why output can be successful but visibly wrong

### 1. Edit-model availability issue

The intended masked edit never runs, so the result is not model-edited content. It is a deterministic filled template fallback. This is the main cause of the current “works, but looks wrong” state.

### 2. Template/layout logic issue

The fallback path preserves and fills the locked frame, which is structurally safe but visually conservative. It is meant as a survivability branch, not a high-quality creative branch.

### 3. Data/default-field issue

Frontend payload builders can inject `agent_name` from `messaging.channel`:

- `frontend/app.js:4711`

Because default channel values include `"email"`:

- `frontend/app.js:1616`
- `frontend/app.js:1638`

that text can surface in rendered poster content even though deployment and Vertex are healthy.

### 4. Gallery duplication issue

Two separate code behaviors can create repetitive gallery output:

- gallery prompts are repeated up to four times when only one prompt exists (`app/services/glibatree.py:1769-1805`)
- gallery is padded to four entries with product/scenario fallback assets (`app/services/glibatree.py:1850-1876`)

This is quality degradation from deterministic fallback/padding logic, not deployment failure.

## Minimal code/config fix candidates

### Candidate A

Enable the edit feature flag in runtime config:

- set `VERTEX_IMAGEN_ENABLE_EDIT=1`

Why it helps:

- This is the exact gate that currently prevents `_edit_model` from being initialized.

Risk:

- Low configuration risk.
- Medium runtime uncertainty because the model name / SDK edit call may still fail once the branch is actually exercised.

### Candidate B

Keep the flag enabled and validate the edit model name explicitly:

- current code reads `VERTEX_IMAGEN_EDIT_MODEL` first, then `VERTEX_IMAGEN_MODEL_EDIT`
- source: `app/services/vertex_imagen3.py:109-112`

Why it helps:

- It removes uncertainty between “flag disabled” and “bad model string”.

Risk:

- Low if done as config only.
- Medium if the chosen model identifier is not actually supported by the installed Vertex SDK.

### Candidate C

Improve startup/runtime logging around edit readiness:

- log `enable_edit`
- resolved edit model name
- whether `_edit_model` successfully loaded

Why it helps:

- This would make the next recovery/debug cycle much shorter and safer.

Risk:

- Very low. Observability-only.

### Candidate D

Add a narrow `/healthz` alias.

Why it helps:

- It prevents stale probes from producing false negatives.

Risk:

- Very low. No business-path change.

## Risks of broader changes

- Unifying the two Vertex provider implementations now would be a larger refactor and is not required to restore the edit path.
- Removing gallery padding or changing fallback semantics now would change output behavior broadly and should wait until the intended edit path is stable.
- Renaming env vars without compatibility aliases would create avoidable operator risk in a still-recovering deployment.
