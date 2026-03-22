# P1 Puppeteer Pilot Plan

## Goal

Ship the first structured foreground rendering pilot on the existing `poster2` path without moving work back to `glibatree`.

## Delivered Scope

1. Add renderer abstraction to `poster2`.
2. Keep Pillow as the deterministic fallback engine.
3. Add structured HTML template assets for `template_dual_v2`.
4. Expose renderer selection and renderer metadata at the request/response boundary.
5. Keep AI limited to background generation.
6. Add focused tests for selection, metadata, contract loading, and route compatibility.

## Deferred

- broad multi-template rollout
- browser pooling and performance optimization
- template authoring tools
- wider prompt tuning work

## Rollout Notes

- Start with `renderer_mode=puppeteer` only for controlled pilot traffic.
- Keep route default on `auto`, with runtime default resolving to `pillow` unless explicitly changed.
- Use manifest metadata to audit actual engine usage before widening adoption.
