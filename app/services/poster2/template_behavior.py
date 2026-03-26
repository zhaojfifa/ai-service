from __future__ import annotations

from dataclasses import dataclass

from .contracts import TemplateBeautyTokensSpec, TemplateBehaviorModesSpec, TemplateSpec

_FEATURE_MODE_LAYOUT_SPECS: dict[int, dict[str, int | str]] = {
    1: {"box_h": 80, "gap": 0, "connector_policy": "single_center"},
    2: {"box_h": 76, "gap": 18, "connector_policy": "balanced_pair"},
    3: {"box_h": 72, "gap": 16, "connector_policy": "compact_triplet"},
    4: {"box_h": 60, "gap": 12, "connector_policy": "dense_quad"},
}
_UNIFORM_FEATURE_MODE_LAYOUT_SPECS: dict[int, dict[str, int | str]] = {
    1: {"box_h": 68, "gap": 0, "connector_policy": "uniform_stack"},
    2: {"box_h": 68, "gap": 14, "connector_policy": "uniform_stack"},
    3: {"box_h": 68, "gap": 12, "connector_policy": "uniform_stack"},
    4: {"box_h": 68, "gap": 10, "connector_policy": "uniform_stack"},
}

_SUPPORTED_HERO_MODES = {"scenario_cover_product_contain", "single_product_focus"}
_SUPPORTED_FEATURE_MODES = {"count_driven_callout_stack", "uniform_callout_stack"}
_SUPPORTED_SHELL_SURFACES = {"glass_light"}
_SUPPORTED_SHELL_BORDERS = {"soft_line"}
_SUPPORTED_SHELL_SHADOWS = {"soft"}
_SUPPORTED_ACCENT_TONES = {"warm_red"}
_SUPPORTED_TEXT_EMPHASIS = {"campaign_primary"}


@dataclass(frozen=True)
class ResolvedHeroBehavior:
    mode: str
    scenario_enabled: bool
    scenario_uses_safe_fill: bool
    scenario_fit: str
    scenario_anchor: str
    product_fit: str
    product_anchor: str
    css_classes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "scenario_enabled": self.scenario_enabled,
            "scenario_uses_safe_fill": self.scenario_uses_safe_fill,
            "scenario_fit": self.scenario_fit,
            "scenario_anchor": self.scenario_anchor,
            "product_fit": self.product_fit,
            "product_anchor": self.product_anchor,
            "css_classes": list(self.css_classes),
        }


@dataclass(frozen=True)
class ResolvedFeatureBehavior:
    mode: str
    requested_item_count: int
    visible_item_count: int
    max_items: int
    visible_item_count_policy: str
    connector_policy: str
    box_policy: str
    truncation_policy: str
    collapse_policy: str
    line_clamp: int
    box_h: int
    gap: int
    start_strategy: str

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "requested_item_count": self.requested_item_count,
            "visible_item_count": self.visible_item_count,
            "max_items": self.max_items,
            "visible_item_count_policy": self.visible_item_count_policy,
            "connector_policy": self.connector_policy,
            "box_policy": self.box_policy,
            "truncation_policy": self.truncation_policy,
            "collapse_policy": self.collapse_policy,
            "line_clamp": self.line_clamp,
            "box_h": self.box_h,
            "gap": self.gap,
            "start_strategy": self.start_strategy,
        }


@dataclass(frozen=True)
class ResolvedTemplateBehavior:
    hero_mode: str
    feature_mode: str
    header_mode: str | None
    bottom_mode: str | None
    gallery_mode: str | None
    beauty_tokens: TemplateBeautyTokensSpec
    hero_policy: ResolvedHeroBehavior
    feature_policy: ResolvedFeatureBehavior
    css_vars: dict[str, str]
    accent_color: str
    text_colors: dict[str, str]
    root_classes: tuple[str, ...]

    def css_var_style(self) -> str:
        return "; ".join(f"{key}: {value}" for key, value in self.css_vars.items())

    def root_class_name(self) -> str:
        return " ".join(self.root_classes)

    def as_dict(self) -> dict[str, object]:
        return {
            "behavior_modes": {
                "hero_mode": self.hero_mode,
                "feature_mode": self.feature_mode,
                "header_mode": self.header_mode,
                "bottom_mode": self.bottom_mode,
                "gallery_mode": self.gallery_mode,
            },
            "hero_policy": self.hero_policy.as_dict(),
            "feature_policy": self.feature_policy.as_dict(),
            "beauty_tokens": {
                "shell_surface": self.beauty_tokens.shell_surface,
                "shell_border": self.beauty_tokens.shell_border,
                "shell_shadow": self.beauty_tokens.shell_shadow,
                "accent_tone": self.beauty_tokens.accent_tone,
                "text_emphasis": self.beauty_tokens.text_emphasis,
            },
            "css_vars": dict(self.css_vars),
        }


def resolve_template_behavior(spec: TemplateSpec, *, feature_count: int | None = None) -> ResolvedTemplateBehavior:
    modes = spec.behavior_modes
    beauty = spec.beauty_tokens
    hero_mode = _validate_token(modes.hero_mode, _SUPPORTED_HERO_MODES, "hero_mode")
    feature_mode = _validate_token(modes.feature_mode, _SUPPORTED_FEATURE_MODES, "feature_mode")
    shell_surface = _validate_token(beauty.shell_surface, _SUPPORTED_SHELL_SURFACES, "shell_surface")
    shell_border = _validate_token(beauty.shell_border, _SUPPORTED_SHELL_BORDERS, "shell_border")
    shell_shadow = _validate_token(beauty.shell_shadow, _SUPPORTED_SHELL_SHADOWS, "shell_shadow")
    accent_tone = _validate_token(beauty.accent_tone, _SUPPORTED_ACCENT_TONES, "accent_tone")
    text_emphasis = _validate_token(beauty.text_emphasis, _SUPPORTED_TEXT_EMPHASIS, "text_emphasis")
    hero_policy = resolve_hero_behavior(hero_mode)
    feature_policy = resolve_feature_behavior(
        feature_mode,
        requested_count=feature_count or 0,
        max_items=len(spec.feature_callouts),
    )

    accent_color = _resolve_accent_color(accent_tone)
    text_colors = _resolve_text_colors(text_emphasis, accent_color)
    css_vars = {}
    css_vars.update(_resolve_shell_surface_vars(shell_surface))
    css_vars.update(_resolve_shell_border_vars(shell_border, accent_color))
    css_vars.update(_resolve_shell_shadow_vars(shell_shadow))
    css_vars.update(
        {
            "--accent-tone": accent_color,
            "--text-color-brand": text_colors["brand"],
            "--text-color-agent": text_colors["agent"],
            "--text-color-title": text_colors["title"],
            "--text-color-subtitle": text_colors["subtitle"],
            "--text-color-feature": text_colors["feature"],
        }
    )
    return ResolvedTemplateBehavior(
        hero_mode=hero_mode,
        feature_mode=feature_mode,
        header_mode=modes.header_mode,
        bottom_mode=modes.bottom_mode,
        gallery_mode=modes.gallery_mode,
        beauty_tokens=TemplateBeautyTokensSpec(
            shell_surface=shell_surface,
            shell_border=shell_border,
            shell_shadow=shell_shadow,
            accent_tone=accent_tone,
            text_emphasis=text_emphasis,
        ),
        hero_policy=hero_policy,
        feature_policy=feature_policy,
        css_vars=css_vars,
        accent_color=accent_color,
        text_colors=text_colors,
        root_classes=(
            *hero_policy.css_classes,
            _css_mode_class("feature-behavior", feature_mode),
        ),
    )


def resolve_hero_behavior(hero_mode: str) -> ResolvedHeroBehavior:
    if hero_mode == "scenario_cover_product_contain":
        return ResolvedHeroBehavior(
            mode=hero_mode,
            scenario_enabled=True,
            scenario_uses_safe_fill=True,
            scenario_fit="cover",
            scenario_anchor="center",
            product_fit="contain",
            product_anchor="bottom",
            css_classes=(_css_mode_class("hero-mode", hero_mode),),
        )
    if hero_mode == "single_product_focus":
        return ResolvedHeroBehavior(
            mode=hero_mode,
            scenario_enabled=False,
            scenario_uses_safe_fill=False,
            scenario_fit="cover",
            scenario_anchor="center",
            product_fit="contain",
            product_anchor="bottom",
            css_classes=(_css_mode_class("hero-mode", hero_mode), "hero-scenario-disabled"),
        )
    raise ValueError(f"Unsupported hero_mode: {hero_mode}")


def resolve_feature_behavior(
    feature_mode: str,
    *,
    requested_count: int,
    max_items: int,
) -> ResolvedFeatureBehavior:
    visible_item_count = min(max(requested_count, 0), max_items)
    clamped_count = min(max(visible_item_count, 1), 4)
    if feature_mode == "count_driven_callout_stack":
        layout_spec = _FEATURE_MODE_LAYOUT_SPECS[clamped_count]
        return ResolvedFeatureBehavior(
            mode=feature_mode,
            requested_item_count=requested_count,
            visible_item_count=visible_item_count,
            max_items=max_items,
            visible_item_count_policy="real_items_capped_to_slots",
            connector_policy=str(layout_spec["connector_policy"]),
            box_policy="count_scaled_stack",
            truncation_policy="two_line_clamp",
            collapse_policy="collapse_when_empty",
            line_clamp=2,
            box_h=int(layout_spec["box_h"]),
            gap=int(layout_spec["gap"]),
            start_strategy="centered_in_region",
        )
    if feature_mode == "uniform_callout_stack":
        layout_spec = _UNIFORM_FEATURE_MODE_LAYOUT_SPECS[clamped_count]
        return ResolvedFeatureBehavior(
            mode=feature_mode,
            requested_item_count=requested_count,
            visible_item_count=visible_item_count,
            max_items=max_items,
            visible_item_count_policy="real_items_capped_to_slots",
            connector_policy=str(layout_spec["connector_policy"]),
            box_policy="uniform_compact_stack",
            truncation_policy="two_line_clamp",
            collapse_policy="collapse_when_empty",
            line_clamp=2,
            box_h=int(layout_spec["box_h"]),
            gap=int(layout_spec["gap"]),
            start_strategy="centered_in_region",
        )
    raise ValueError(f"Unsupported feature_mode: {feature_mode}")


def resolve_feature_layout_mode(count: int, feature_mode: str) -> tuple[int, dict[str, int | str]]:
    policy = resolve_feature_behavior(feature_mode, requested_count=count, max_items=4)
    return min(max(policy.visible_item_count, 1), 4), {
        "box_h": policy.box_h,
        "gap": policy.gap,
        "connector_policy": policy.connector_policy,
    }


def _validate_token(value: str, supported: set[str], field_name: str) -> str:
    if value not in supported:
        raise ValueError(f"Unsupported {field_name}: {value}")
    return value


def _resolve_shell_surface_vars(shell_surface: str) -> dict[str, str]:
    if shell_surface != "glass_light":
        raise ValueError(f"Unsupported shell_surface: {shell_surface}")
    return {
        "--shell-surface-header": "linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(252, 245, 243, 0.92))",
        "--shell-surface-scenario-safe": "linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(247, 238, 234, 0.26))",
        "--shell-surface-scenario-real": "linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02))",
        "--shell-surface-product": "linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(250, 242, 240, 0.92))",
        "--shell-surface-bottom": "linear-gradient(180deg, rgba(255, 255, 255, 0.70), rgba(255, 248, 246, 0.56))",
        "--shell-surface-title-band": "linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(255, 248, 245, 0.88))",
        "--shell-surface-gallery-strip": "rgba(255, 255, 255, 0.68)",
        "--feature-card-surface": "rgba(255, 255, 255, 0.95)",
    }


def _resolve_shell_border_vars(shell_border: str, accent_color: str) -> dict[str, str]:
    if shell_border != "soft_line":
        raise ValueError(f"Unsupported shell_border: {shell_border}")
    return {
        "--shell-border-header": f"1px solid {accent_color}14",
        "--shell-border-hero": "1px solid rgba(255, 255, 255, 0.24)",
        "--shell-border-product": f"1px solid {accent_color}14",
        "--shell-border-bottom": f"1px solid {accent_color}10",
        "--shell-border-gallery": "1px solid rgba(255, 255, 255, 0.44)",
        "--feature-card-border": f"1px solid {accent_color}1f",
    }


def _resolve_shell_shadow_vars(shell_shadow: str) -> dict[str, str]:
    if shell_shadow != "soft":
        raise ValueError(f"Unsupported shell_shadow: {shell_shadow}")
    return {
        "--shell-shadow-main": "0 18px 36px rgba(34, 22, 22, 0.11)",
        "--shell-shadow-secondary": "0 12px 26px rgba(31, 22, 22, 0.08)",
        "--feature-card-shadow": "0 12px 24px rgba(24, 16, 16, 0.10)",
        "--gallery-item-shadow": "0 10px 22px rgba(31, 22, 22, 0.10)",
    }


def _resolve_accent_color(accent_tone: str) -> str:
    if accent_tone != "warm_red":
        raise ValueError(f"Unsupported accent_tone: {accent_tone}")
    return "#E8002A"


def _resolve_text_colors(text_emphasis: str, accent_color: str) -> dict[str, str]:
    if text_emphasis != "campaign_primary":
        raise ValueError(f"Unsupported text_emphasis: {text_emphasis}")
    return {
        "brand": "#1A1A1A",
        "agent": "#6F5757",
        "title": accent_color,
        "subtitle": accent_color,
        "feature": "#1A1A1A",
    }


def _css_mode_class(prefix: str, mode_name: str) -> str:
    return f"{prefix}-{mode_name.replace('_', '-')}"
