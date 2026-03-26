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
_SUPPORTED_BOTTOM_MODES = {"title_gallery_split", "title_only", "gallery_only"}
_SUPPORTED_GALLERY_MODES = {"strip_local_visible_only", "supporting_packshots"}
_SHELL_SURFACE_PRESETS: dict[str, dict[str, str]] = {
    "glass_light": {
        "--shell-surface-header": "linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(252, 245, 243, 0.92))",
        "--shell-surface-scenario-safe": "linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(247, 238, 234, 0.26))",
        "--shell-surface-scenario-real": "linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02))",
        "--shell-surface-product": "linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(250, 242, 240, 0.92))",
        "--shell-surface-bottom": "linear-gradient(180deg, rgba(255, 255, 255, 0.70), rgba(255, 248, 246, 0.56))",
        "--shell-surface-title-band": "linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(255, 248, 245, 0.88))",
        "--shell-surface-gallery-strip": "rgba(255, 255, 255, 0.68)",
        "--feature-card-surface": "rgba(255, 255, 255, 0.95)",
    },
    "panel_clean": {
        "--shell-surface-header": "linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 248, 248, 0.96))",
        "--shell-surface-scenario-safe": "linear-gradient(180deg, rgba(249, 249, 249, 0.94), rgba(240, 240, 240, 0.96))",
        "--shell-surface-scenario-real": "linear-gradient(180deg, rgba(255, 255, 255, 0.12), rgba(250, 250, 250, 0.06))",
        "--shell-surface-product": "linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(246, 246, 246, 0.97))",
        "--shell-surface-bottom": "linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 247, 247, 0.88))",
        "--shell-surface-title-band": "linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(246, 246, 246, 0.94))",
        "--shell-surface-gallery-strip": "rgba(255, 255, 255, 0.84)",
        "--feature-card-surface": "rgba(255, 255, 255, 0.98)",
    },
    "panel_dark_soft": {
        "--shell-surface-header": "linear-gradient(180deg, rgba(44, 42, 46, 0.92), rgba(34, 32, 36, 0.88))",
        "--shell-surface-scenario-safe": "linear-gradient(180deg, rgba(58, 55, 61, 0.78), rgba(41, 39, 44, 0.74))",
        "--shell-surface-scenario-real": "linear-gradient(180deg, rgba(54, 52, 58, 0.48), rgba(34, 32, 36, 0.18))",
        "--shell-surface-product": "linear-gradient(180deg, rgba(53, 50, 57, 0.94), rgba(40, 38, 43, 0.90))",
        "--shell-surface-bottom": "linear-gradient(180deg, rgba(47, 44, 50, 0.82), rgba(36, 34, 38, 0.78))",
        "--shell-surface-title-band": "linear-gradient(180deg, rgba(50, 48, 54, 0.88), rgba(36, 34, 39, 0.82))",
        "--shell-surface-gallery-strip": "rgba(48, 46, 52, 0.76)",
        "--feature-card-surface": "rgba(57, 54, 60, 0.92)",
    },
    "solid_soft": {
        "--shell-surface-header": "rgba(255, 252, 250, 0.98)",
        "--shell-surface-scenario-safe": "rgba(246, 240, 236, 0.92)",
        "--shell-surface-scenario-real": "rgba(255, 255, 255, 0.14)",
        "--shell-surface-product": "rgba(255, 251, 248, 0.98)",
        "--shell-surface-bottom": "rgba(255, 250, 247, 0.92)",
        "--shell-surface-title-band": "rgba(255, 252, 250, 0.96)",
        "--shell-surface-gallery-strip": "rgba(255, 250, 247, 0.82)",
        "--feature-card-surface": "rgba(255, 252, 250, 0.96)",
    },
}
_SHELL_BORDER_PRESETS: dict[str, dict[str, str]] = {
    "soft_line": {
        "--shell-border-accent-alpha": "14",
        "--shell-border-gallery": "1px solid rgba(255, 255, 255, 0.44)",
        "--shell-border-hero": "1px solid rgba(255, 255, 255, 0.24)",
        "--feature-card-border-alpha": "1f",
    },
    "clean_frame": {
        "--shell-border-accent-alpha": "32",
        "--shell-border-gallery": "1px solid rgba(255, 255, 255, 0.58)",
        "--shell-border-hero": "1px solid rgba(255, 255, 255, 0.34)",
        "--feature-card-border-alpha": "36",
    },
    "none": {
        "--shell-border-accent-alpha": "00",
        "--shell-border-gallery": "1px solid rgba(255, 255, 255, 0.00)",
        "--shell-border-hero": "1px solid rgba(255, 255, 255, 0.00)",
        "--feature-card-border-alpha": "00",
    },
}
_SHELL_SHADOW_PRESETS: dict[str, dict[str, str]] = {
    "none": {
        "--shell-shadow-main": "0 0 0 rgba(0, 0, 0, 0)",
        "--shell-shadow-secondary": "0 0 0 rgba(0, 0, 0, 0)",
        "--feature-card-shadow": "0 0 0 rgba(0, 0, 0, 0)",
        "--gallery-item-shadow": "0 0 0 rgba(0, 0, 0, 0)",
    },
    "soft": {
        "--shell-shadow-main": "0 18px 36px rgba(34, 22, 22, 0.11)",
        "--shell-shadow-secondary": "0 12px 26px rgba(31, 22, 22, 0.08)",
        "--feature-card-shadow": "0 12px 24px rgba(24, 16, 16, 0.10)",
        "--gallery-item-shadow": "0 10px 22px rgba(31, 22, 22, 0.10)",
    },
    "medium": {
        "--shell-shadow-main": "0 22px 42px rgba(26, 18, 18, 0.16)",
        "--shell-shadow-secondary": "0 16px 30px rgba(28, 20, 20, 0.12)",
        "--feature-card-shadow": "0 14px 28px rgba(24, 16, 16, 0.14)",
        "--gallery-item-shadow": "0 12px 24px rgba(31, 22, 22, 0.12)",
    },
}
_ACCENT_TONE_PRESETS: dict[str, str] = {
    "warm_red": "#E8002A",
    "brand_gold": "#C69214",
    "cool_blue": "#2D6CDF",
}
_TEXT_EMPHASIS_PRESETS: dict[str, dict[str, str]] = {
    "campaign_primary": {
        "brand": "#1A1A1A",
        "agent": "#6F5757",
        "title": "{accent}",
        "subtitle": "{accent}",
        "feature": "#1A1A1A",
    },
    "editorial_soft": {
        "brand": "#242124",
        "agent": "#7A6E76",
        "title": "{accent}",
        "subtitle": "#8A7A84",
        "feature": "#262228",
    },
    "high_contrast": {
        "brand": "#111111",
        "agent": "#4A4A4A",
        "title": "{accent}",
        "subtitle": "{accent}",
        "feature": "#111111",
    },
}


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
class ResolvedBottomBehavior:
    mode: str
    gallery_mode: str
    requested_gallery_count: int
    visible_item_count: int
    max_gallery_items: int
    title_present: bool
    subtitle_present: bool
    title_slot_rendered: bool
    subtitle_slot_rendered: bool
    title_band_rendered: bool
    gallery_strip_rendered: bool
    bottom_region_rendered: bool
    visible_item_count_policy: str
    gallery_content_policy: str
    collapse_policy: str
    bottom_region_state: str
    collapsed_optional_slots: tuple[str, ...]
    subtitle_slot_state: dict[str, object]
    gallery_slot_states: tuple[dict[str, object], ...]
    css_classes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "gallery_mode": self.gallery_mode,
            "requested_gallery_count": self.requested_gallery_count,
            "visible_item_count": self.visible_item_count,
            "max_gallery_items": self.max_gallery_items,
            "title_present": self.title_present,
            "subtitle_present": self.subtitle_present,
            "title_slot_rendered": self.title_slot_rendered,
            "subtitle_slot_rendered": self.subtitle_slot_rendered,
            "title_band_rendered": self.title_band_rendered,
            "gallery_strip_rendered": self.gallery_strip_rendered,
            "bottom_region_rendered": self.bottom_region_rendered,
            "visible_item_count_policy": self.visible_item_count_policy,
            "gallery_content_policy": self.gallery_content_policy,
            "collapse_policy": self.collapse_policy,
            "bottom_region_state": self.bottom_region_state,
            "collapsed_optional_slots": list(self.collapsed_optional_slots),
            "subtitle_slot_state": dict(self.subtitle_slot_state),
            "gallery_slot_states": [dict(item) for item in self.gallery_slot_states],
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
    bottom_policy: ResolvedBottomBehavior
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
            "bottom_policy": self.bottom_policy.as_dict(),
            "beauty_tokens": {
                "shell_surface": self.beauty_tokens.shell_surface,
                "shell_border": self.beauty_tokens.shell_border,
                "shell_shadow": self.beauty_tokens.shell_shadow,
                "accent_tone": self.beauty_tokens.accent_tone,
                "text_emphasis": self.beauty_tokens.text_emphasis,
            },
            "css_vars": dict(self.css_vars),
        }


def resolve_template_behavior(
    spec: TemplateSpec,
    *,
    feature_count: int | None = None,
    title_text: str | None = None,
    subtitle_text: str | None = None,
    gallery_requested_count: int | None = None,
    gallery_resolved_count: int | None = None,
    bottom_mode: str | None = None,
    gallery_mode: str | None = None,
) -> ResolvedTemplateBehavior:
    modes = spec.behavior_modes
    beauty = spec.beauty_tokens
    hero_mode = _validate_token(modes.hero_mode, _SUPPORTED_HERO_MODES, "hero_mode")
    feature_mode = _validate_token(modes.feature_mode, _SUPPORTED_FEATURE_MODES, "feature_mode")
    resolved_bottom_mode = _validate_token(bottom_mode or modes.bottom_mode, _SUPPORTED_BOTTOM_MODES, "bottom_mode")
    resolved_gallery_mode = _validate_token(gallery_mode or modes.gallery_mode, _SUPPORTED_GALLERY_MODES, "gallery_mode")
    shell_surface = _validate_token(beauty.shell_surface, set(_SHELL_SURFACE_PRESETS), "shell_surface")
    shell_border = _validate_token(beauty.shell_border, set(_SHELL_BORDER_PRESETS), "shell_border")
    shell_shadow = _validate_token(beauty.shell_shadow, set(_SHELL_SHADOW_PRESETS), "shell_shadow")
    accent_tone = _validate_token(beauty.accent_tone, set(_ACCENT_TONE_PRESETS), "accent_tone")
    text_emphasis = _validate_token(beauty.text_emphasis, set(_TEXT_EMPHASIS_PRESETS), "text_emphasis")
    hero_policy = resolve_hero_behavior(hero_mode)
    feature_policy = resolve_feature_behavior(
        feature_mode,
        requested_count=feature_count or 0,
        max_items=len(spec.feature_callouts),
    )
    bottom_policy = resolve_bottom_behavior(
        resolved_bottom_mode,
        gallery_mode=resolved_gallery_mode,
        title_text=title_text,
        subtitle_text=subtitle_text,
        requested_gallery_count=gallery_requested_count or 0,
        resolved_gallery_count=gallery_resolved_count or 0,
        max_items=spec.gallery_slot.count,
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
        bottom_mode=resolved_bottom_mode,
        gallery_mode=resolved_gallery_mode,
        beauty_tokens=TemplateBeautyTokensSpec(
            shell_surface=shell_surface,
            shell_border=shell_border,
            shell_shadow=shell_shadow,
            accent_tone=accent_tone,
            text_emphasis=text_emphasis,
        ),
        hero_policy=hero_policy,
        feature_policy=feature_policy,
        bottom_policy=bottom_policy,
        css_vars=css_vars,
        accent_color=accent_color,
        text_colors=text_colors,
        root_classes=(
            *hero_policy.css_classes,
            _css_mode_class("feature-behavior", feature_mode),
            *bottom_policy.css_classes,
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


def resolve_bottom_behavior(
    bottom_mode: str,
    *,
    gallery_mode: str,
    title_text: str | None,
    subtitle_text: str | None,
    requested_gallery_count: int,
    resolved_gallery_count: int,
    max_items: int,
) -> ResolvedBottomBehavior:
    title_present = bool((title_text or "").strip())
    subtitle_present = bool((subtitle_text or "").strip())
    requested_gallery_count = min(max(requested_gallery_count, 0), max_items)
    visible_item_count = min(max(resolved_gallery_count, 0), max_items)
    title_slot_rendered = title_present and bottom_mode != "gallery_only"
    subtitle_slot_rendered = subtitle_present and bottom_mode != "gallery_only" and title_present

    if bottom_mode == "title_gallery_split":
        title_band_rendered = title_slot_rendered
        gallery_strip_rendered = visible_item_count > 0
        gallery_content_policy = "render_real_gallery_items_in_local_strip_only"
    elif bottom_mode == "title_only":
        title_band_rendered = title_slot_rendered
        gallery_strip_rendered = False
        gallery_content_policy = "collapse_gallery_strip_even_when_gallery_inputs_exist"
    elif bottom_mode == "gallery_only":
        title_band_rendered = False
        gallery_strip_rendered = visible_item_count > 0
        gallery_content_policy = "render_gallery_strip_without_title_band"
    else:
        raise ValueError(f"Unsupported bottom_mode: {bottom_mode}")

    bottom_region_rendered = title_band_rendered or gallery_strip_rendered
    if title_band_rendered and gallery_strip_rendered:
        bottom_region_state = "state-title-gallery"
    elif title_band_rendered:
        bottom_region_state = "state-title-only"
    elif gallery_strip_rendered:
        bottom_region_state = "state-gallery-only"
    else:
        bottom_region_state = "state-hidden"

    subtitle_reason = (
        None
        if subtitle_slot_rendered
        else (
            "subtitle_empty"
            if not subtitle_present
            else ("title_missing" if not title_present else "suppressed_by_bottom_mode")
        )
    )
    subtitle_slot_state = {
        "slot_id": "subtitle_slot",
        "rendered": subtitle_slot_rendered,
        "state": "rendered" if subtitle_slot_rendered else "collapsed",
        "reason_code": subtitle_reason,
        "owner_region": "title_band_region",
    }

    gallery_slot_states: list[dict[str, object]] = []
    collapsed_optional_slots: list[str] = []
    if not subtitle_slot_rendered:
        collapsed_optional_slots.append("subtitle_slot")
    for index in range(max_items):
        slot_id = f"gallery_item_slot_{index + 1}"
        slot_rendered = gallery_strip_rendered and index < visible_item_count
        if slot_rendered:
            reason_code = None
            state = "rendered"
        elif bottom_mode == "title_only":
            reason_code = "suppressed_by_bottom_mode"
            state = "collapsed"
        elif index >= requested_gallery_count:
            reason_code = "gallery_input_missing"
            state = "collapsed"
        elif index >= visible_item_count:
            reason_code = "not_visible_after_resolution"
            state = "collapsed"
        else:
            reason_code = "gallery_strip_hidden"
            state = "collapsed"
        gallery_slot_states.append(
            {
                "slot_id": slot_id,
                "index": index,
                "rendered": slot_rendered,
                "state": state,
                "reason_code": reason_code,
                "owner_region": "gallery_strip_region",
                "gallery_mode": gallery_mode,
            }
        )
        if not slot_rendered:
            collapsed_optional_slots.append(slot_id)

    return ResolvedBottomBehavior(
        mode=bottom_mode,
        gallery_mode=gallery_mode,
        requested_gallery_count=requested_gallery_count,
        visible_item_count=visible_item_count,
        max_gallery_items=max_items,
        title_present=title_present,
        subtitle_present=subtitle_present,
        title_slot_rendered=title_slot_rendered,
        subtitle_slot_rendered=subtitle_slot_rendered,
        title_band_rendered=title_band_rendered,
        gallery_strip_rendered=gallery_strip_rendered,
        bottom_region_rendered=bottom_region_rendered,
        visible_item_count_policy="real_items_capped_to_slots",
        gallery_content_policy=gallery_content_policy,
        collapse_policy="title_band_and_gallery_strip_collapse_independently_under_bottom_mode",
        bottom_region_state=bottom_region_state,
        collapsed_optional_slots=tuple(collapsed_optional_slots),
        subtitle_slot_state=subtitle_slot_state,
        gallery_slot_states=tuple(gallery_slot_states),
        css_classes=(
            _css_mode_class("bottom-mode", bottom_mode),
            _css_mode_class("gallery-mode", gallery_mode),
        ),
    )


def _validate_token(value: str, supported: set[str], field_name: str) -> str:
    if value not in supported:
        raise ValueError(f"Unsupported {field_name}: {value}")
    return value


def _resolve_shell_surface_vars(shell_surface: str) -> dict[str, str]:
    if shell_surface not in _SHELL_SURFACE_PRESETS:
        raise ValueError(f"Unsupported shell_surface: {shell_surface}")
    return dict(_SHELL_SURFACE_PRESETS[shell_surface])


def _resolve_shell_border_vars(shell_border: str, accent_color: str) -> dict[str, str]:
    if shell_border not in _SHELL_BORDER_PRESETS:
        raise ValueError(f"Unsupported shell_border: {shell_border}")
    preset = _SHELL_BORDER_PRESETS[shell_border]
    accent_alpha = preset["--shell-border-accent-alpha"]
    feature_alpha = preset["--feature-card-border-alpha"]
    return {
        "--shell-border-header": f"1px solid {accent_color}{accent_alpha}",
        "--shell-border-hero": preset["--shell-border-hero"],
        "--shell-border-product": f"1px solid {accent_color}{accent_alpha}",
        "--shell-border-bottom": f"1px solid {accent_color}{accent_alpha}",
        "--shell-border-gallery": preset["--shell-border-gallery"],
        "--feature-card-border": f"1px solid {accent_color}{feature_alpha}",
    }


def _resolve_shell_shadow_vars(shell_shadow: str) -> dict[str, str]:
    if shell_shadow not in _SHELL_SHADOW_PRESETS:
        raise ValueError(f"Unsupported shell_shadow: {shell_shadow}")
    return dict(_SHELL_SHADOW_PRESETS[shell_shadow])


def _resolve_accent_color(accent_tone: str) -> str:
    if accent_tone not in _ACCENT_TONE_PRESETS:
        raise ValueError(f"Unsupported accent_tone: {accent_tone}")
    return _ACCENT_TONE_PRESETS[accent_tone]


def _resolve_text_colors(text_emphasis: str, accent_color: str) -> dict[str, str]:
    if text_emphasis not in _TEXT_EMPHASIS_PRESETS:
        raise ValueError(f"Unsupported text_emphasis: {text_emphasis}")
    preset = _TEXT_EMPHASIS_PRESETS[text_emphasis]
    return {key: value.format(accent=accent_color) for key, value in preset.items()}


def _css_mode_class(prefix: str, mode_name: str) -> str:
    return f"{prefix}-{mode_name.replace('_', '-')}"
