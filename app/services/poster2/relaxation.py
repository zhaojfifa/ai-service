"""
Poster2 Visual Relaxation Layer — contract-safe, non-geometric beautification.

Relaxation presets reduce the "too tightly fitted / mechanically packed" feel of
a poster by adjusting ONLY surface + negative-space CSS custom properties that
are already defined and consumed by the template stylesheet. They are injected
through the existing beauty-token CSS-var channel
(``ResolvedTemplateBehavior.css_var_style()`` -> ``__BEAUTY_CSS_VARS__`` on
``#poster-root``). A preset is purely additive on top of the frozen Family A
beautification freeze pack.

Hard invariants (enforced here + by tests + by the quality guard):

- ``none`` emits **zero** variables, so a poster rendered with ``relaxation_preset
  = none`` (or omitted) is byte-identical to the pre-relaxation render. This is
  what keeps the existing golden hashes stable.
- A preset may only emit keys in :data:`RELAXATION_CSS_VAR_WHITELIST`. Every key
  is an existing, consumed, **non-geometry** spacing/surface var. Slot / region /
  anchor / annotation geometry vars (``--product-shell-*``, ``--gallery-shell-*``,
  ``--title-band-*``, ``--*-region-*``, anchor coordinates, ...) are deliberately
  excluded, so a preset can never move a boundary or touch bottom-SOP /
  product-annotation truth.
- Presets are a closed enum; unknown names raise :class:`RelaxationError`.

Scope note (documented implementation deviation from the taxonomy plan §4):
the plan proposed eight token families. Investigation of the live CSS + freeze
pack showed that several of them are not safely usable as injected overrides:

- ``--peer-region-gap`` is defined but consumed nowhere (an inert no-op).
- No scenario<->product seam variable exists; a seam mask would require new
  geometry / markup, which is out of bounds.
- ``--shell-shadow-*``, ``--shell-surface-*``, ``--accent-tone`` are already
  authored by the Family A beautification freeze pack (often warm-tinted, e.g.
  shadow ``rgba(26,18,18,...)``). Overriding them from relaxation would re-tint /
  mask frozen Family A surface truth, so they are deliberately left to the freeze
  pack.

- ``--product-content-pad-*`` is consumed by ``.layer-product-content`` but the
  product image slot inside it is absolutely positioned (fixed left/top/w/h), so
  the padding does not actually move the product — another effective no-op.
  Genuinely giving the product more room means shrinking the product slot, which
  is a GEOMETRY change and belongs to a future geometry style-variant template,
  not to the (non-geometric) relaxation layer.

This first implementation therefore wires the two provably-safe, effective, non
-freeze-pack-owned, non-geometry levers:

- ``--title-stack-gap`` — the gap between the title and subtitle text inside the
  title band (text rhythm; space inside a region).
- ``--product-primary-shadow`` — the drop-shadow filter on the product image,
  which lifts/floats the product for a calmer, more "designed" product area
  without moving its box. (A neutral drop-shadow the freeze pack does not own.)

Both change surface / space, never a region boundary. See
``docs/poster2/template_taxonomy_and_visual_relaxation_plan_v1.md``.
"""
from __future__ import annotations

#: Closed enum of supported relaxation presets.
RELAXATION_PRESETS: tuple[str, ...] = ("none", "airy", "premium_soft", "dense_safe")

#: Preset that reproduces today's render exactly.
DEFAULT_RELAXATION_PRESET = "none"

#: The ONLY CSS custom properties a relaxation preset is permitted to set.
#: All are existing, consumed, non-geometry spacing/surface vars in
#: ``app/templates_html/template_dual_v2.css``.
RELAXATION_CSS_VAR_WHITELIST: frozenset[str] = frozenset(
    {
        # text/title-stack breathing: gap between the title and subtitle text
        # inside the title band (.layer-title-band-layout). Space inside a
        # region, not a region boundary.
        "--title-stack-gap",
        # product lift: drop-shadow filter on the product image
        # (.product-fit-contain img). Floats the product for a calmer product
        # area. A visual filter only — does not change the product's box.
        "--product-primary-shadow",
    }
)

#: CSS defaults as authored in template_dual_v2.css. Used so a preset can be read
#: as a delta from baseline and so tests can assert the "none" no-op and detect
#: drift between this module and the stylesheet.
RELAXATION_BASELINE_CSS_VARS: dict[str, str] = {
    "--title-stack-gap": "8px",
    "--product-primary-shadow": "drop-shadow(0 18px 30px rgba(0, 0, 0, 0.20))",
}

# Per-preset CSS var overrides. "none" MUST stay empty.
_PRESET_CSS_VARS: dict[str, dict[str, str]] = {
    "none": {},
    "airy": {
        # Open up the title/subtitle stack and float the product on a deeper,
        # softer drop-shadow.
        "--title-stack-gap": "14px",
        "--product-primary-shadow": "drop-shadow(0 26px 44px rgba(0, 0, 0, 0.26))",
    },
    "premium_soft": {
        "--title-stack-gap": "12px",
        "--product-primary-shadow": "drop-shadow(0 30px 52px rgba(0, 0, 0, 0.22))",
    },
    "dense_safe": {
        # Tighter than default but kept above a safe floor; never collapses to 0.
        "--title-stack-gap": "6px",
        "--product-primary-shadow": "drop-shadow(0 12px 22px rgba(0, 0, 0, 0.22))",
    },
}


class RelaxationError(ValueError):
    """Raised for an unknown preset name or a preset that emits a geometry var."""


def normalize_relaxation_preset(preset: str | None) -> str:
    """Resolve a requested preset to a valid closed-enum value.

    ``None`` / empty string -> :data:`DEFAULT_RELAXATION_PRESET` ("none").
    Unknown values raise :class:`RelaxationError`.
    """
    if preset is None or preset == "":
        return DEFAULT_RELAXATION_PRESET
    if preset not in _PRESET_CSS_VARS:
        raise RelaxationError(
            f"Unknown relaxation_preset={preset!r}; expected one of {RELAXATION_PRESETS}"
        )
    return preset


def assert_relaxation_vars_non_geometric(css_vars: dict[str, str]) -> None:
    """Raise if any key is outside the non-geometry whitelist (defense in depth)."""
    illegal = set(css_vars) - RELAXATION_CSS_VAR_WHITELIST
    if illegal:
        raise RelaxationError(
            "relaxation preset emitted non-whitelisted CSS vars "
            f"(possible geometry drift): {sorted(illegal)}"
        )


def relaxation_css_vars(preset: str | None) -> dict[str, str]:
    """Return the CSS custom properties for a preset.

    ``none`` returns ``{}`` (a true no-op). The result is validated against the
    non-geometry whitelist before being returned.
    """
    resolved = normalize_relaxation_preset(preset)
    css_vars = dict(_PRESET_CSS_VARS[resolved])
    assert_relaxation_vars_non_geometric(css_vars)
    return css_vars


def relaxation_report(preset: str | None, *, source: str = "template") -> dict:
    """Build the audit payload surfaced on the RenderManifest + v2 response.

    ``source`` records where the preset came from (currently always the template
    spec). ``applies_to_engine`` documents that relaxation is a Puppeteer-only
    CSS effect; the Pillow fallback ignores it.
    """
    resolved = normalize_relaxation_preset(preset)
    css_vars = relaxation_css_vars(resolved)
    return {
        "preset": resolved,
        "source": source,
        "applies_to_engine": "puppeteer",
        "pillow_compatible": False,
        "non_geometric": True,
        "geometry_invariant": True,
        "css_var_keys": sorted(css_vars.keys()),
    }
