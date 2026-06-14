"""
Poster2 Composition Priority Layer — contract-safe, request-level.

The composition strategy is the operator-facing "海报风格策略" choice. Each of the
four closed presets maps to a closed CSS-var bundle that re-prioritises the
composition WITHOUT changing geometry, ownership, bottom-SOP, annotation truth, or
visible_item_count. The bundle is injected through the existing beauty CSS-var
channel (``ResolvedTemplateBehavior.css_var_style()`` -> ``__BEAUTY_CSS_VARS__``),
merged LAST so it layers over the template + relaxation vars.

Levers (all existing, consumed, non-geometry vars):

- ``--scenario-image-treatment`` — the filter on the (real) scenario image inside
  the unchanged scenario region. Receding the scenario (desaturate / brighten /
  soften / slight blur) turns it into atmosphere so the product becomes the first
  visual focus. This is the headline composition lever.
- ``--product-primary-shadow`` — the drop-shadow filter on the product image;
  lifts the product off the surface for a premium, hero feel.
- ``--title-stack-gap`` — title/subtitle stack breathing (text rhythm inside the
  title band).

NOT touched here (handled by the template the strategy selects, or frozen):
product/title/gallery GEOMETRY, region ownership, bottom footprint,
visible_item_count, the gallery item boxes, product annotation slots. Title font
size and gallery surface come from the studio template's own CSS (the puppeteer
title font is CSS-hardcoded, so it cannot be a request-level override).

Invariants (enforced here + by tests):

- ``balanced`` emits **zero** vars -> byte-identical to the un-composed render.
- A preset may only emit keys in :data:`COMPOSITION_CSS_VAR_WHITELIST` (all
  non-geometry surface/text vars).
- Presets are a closed enum; unknown names raise :class:`CompositionError`.
"""
from __future__ import annotations

#: Closed enum of supported composition strategies (operator-facing order).
COMPOSITION_STRATEGIES: tuple[str, ...] = (
    "balanced",
    "studio",
    "product_hero",
    "catalog_clean",
)

DEFAULT_COMPOSITION_STRATEGY = "balanced"

#: Business-language labels for the Stage2 "海报风格策略" selector (closed).
COMPOSITION_STRATEGY_LABELS: dict[str, str] = {
    "balanced": "均衡 Balanced",
    "studio": "棚拍 Studio",
    "product_hero": "产品主角 Product Hero",
    "catalog_clean": "目录净版 Catalog Clean",
}

#: The ONLY CSS custom properties a composition preset is permitted to set. All are
#: existing, consumed, non-geometry surface/text vars.
COMPOSITION_CSS_VAR_WHITELIST: frozenset[str] = frozenset(
    {
        "--scenario-image-treatment",
        "--product-primary-shadow",
        "--title-stack-gap",
    }
)

#: CSS defaults (kept in sync with template_dual_v2.css) for the no-op baseline.
COMPOSITION_BASELINE_CSS_VARS: dict[str, str] = {
    "--scenario-image-treatment": "saturate(0.88) brightness(0.94)",
    "--product-primary-shadow": "drop-shadow(0 18px 30px rgba(0, 0, 0, 0.20))",
    "--title-stack-gap": "8px",
}

_PRESET_CSS_VARS: dict[str, dict[str, str]] = {
    # Balanced MUST stay empty: reproduces the un-composed render exactly.
    "balanced": {},
    # Studio: scenario softens a touch, product lifts gently, title breathes.
    "studio": {
        "--scenario-image-treatment": "saturate(0.78) brightness(0.98) contrast(0.97)",
        "--product-primary-shadow": "drop-shadow(0 24px 42px rgba(0, 0, 0, 0.24))",
        "--title-stack-gap": "14px",
    },
    # Product Hero: scenario recedes to atmosphere (desaturate, brighten, soften,
    # slight blur) so the product is unmistakably the first focus; product lifts
    # strongly.
    "product_hero": {
        "--scenario-image-treatment": "saturate(0.5) brightness(1.05) contrast(0.9) blur(1.5px)",
        "--product-primary-shadow": "drop-shadow(0 32px 56px rgba(0, 0, 0, 0.3))",
        "--title-stack-gap": "14px",
    },
    # Catalog Clean: scenario washed clean (very desaturated, bright, crisp — no
    # blur); product lift moderate; calm, evidence-led.
    "catalog_clean": {
        "--scenario-image-treatment": "saturate(0.42) brightness(1.07) contrast(0.94)",
        "--product-primary-shadow": "drop-shadow(0 22px 40px rgba(0, 0, 0, 0.22))",
        "--title-stack-gap": "12px",
    },
}


class CompositionError(ValueError):
    """Raised for an unknown strategy or a preset that emits a non-whitelisted var."""


def normalize_composition_strategy(strategy: str | None) -> str:
    """Resolve a requested strategy to a valid closed-enum value.

    ``None`` / empty -> :data:`DEFAULT_COMPOSITION_STRATEGY`. Unknown -> raise.
    """
    if strategy is None or strategy == "":
        return DEFAULT_COMPOSITION_STRATEGY
    if strategy not in _PRESET_CSS_VARS:
        raise CompositionError(
            f"Unknown composition_strategy={strategy!r}; expected one of {COMPOSITION_STRATEGIES}"
        )
    return strategy


def assert_composition_vars_non_geometric(css_vars: dict[str, str]) -> None:
    """Raise if any key is outside the non-geometry whitelist (defense in depth)."""
    illegal = set(css_vars) - COMPOSITION_CSS_VAR_WHITELIST
    if illegal:
        raise CompositionError(
            "composition preset emitted non-whitelisted CSS vars "
            f"(possible geometry drift): {sorted(illegal)}"
        )


def composition_css_vars(strategy: str | None) -> dict[str, str]:
    """Return the CSS custom properties for a strategy. ``balanced`` -> ``{}``."""
    resolved = normalize_composition_strategy(strategy)
    css_vars = dict(_PRESET_CSS_VARS[resolved])
    assert_composition_vars_non_geometric(css_vars)
    return css_vars


def composition_report(strategy: str | None) -> dict:
    """Build the audit payload surfaced on the RenderManifest + v2 response."""
    resolved = normalize_composition_strategy(strategy)
    css_vars = composition_css_vars(resolved)
    return {
        "strategy": resolved,
        "label": COMPOSITION_STRATEGY_LABELS.get(resolved, resolved),
        "applies_to_engine": "puppeteer",
        "non_geometric": True,
        "geometry_invariant": True,
        "css_var_keys": sorted(css_vars.keys()),
    }
