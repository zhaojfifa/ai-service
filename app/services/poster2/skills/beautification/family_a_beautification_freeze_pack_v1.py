from __future__ import annotations

from ...contracts import TemplateBeautyTokensSpec
from ...template_registry import FAMILY_A_CAMPAIGN_EXPLAINER

SKILL_ID = "family_a_beautification_freeze_pack_v1"

_FAMILY_A_SHELL_SURFACE_PRESETS: dict[str, dict[str, str]] = {
    "glass_light": {
        "--shell-surface-header": "linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 247, 243, 0.76))",
        "--shell-surface-scenario-safe": "linear-gradient(180deg, rgba(255, 255, 255, 0.26), rgba(248, 239, 235, 0.32))",
        "--shell-surface-scenario-real": "linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02))",
        "--shell-surface-product": "linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(250, 242, 239, 0.82))",
        "--shell-surface-bottom": "linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(250, 241, 238, 0.58))",
        "--shell-surface-title-band": "linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(252, 244, 240, 0.78))",
        "--shell-surface-gallery-strip": "rgba(255, 255, 255, 0.70)",
        "--feature-card-surface": "rgba(255, 255, 255, 0.98)",
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
    "campaign_frozen_panel": {
        "--shell-surface-header": "linear-gradient(180deg, rgba(255, 253, 251, 0.98), rgba(246, 241, 238, 0.96))",
        "--shell-surface-scenario-safe": "linear-gradient(180deg, rgba(249, 244, 240, 0.90), rgba(241, 233, 228, 0.94))",
        "--shell-surface-scenario-real": "linear-gradient(180deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.04))",
        "--shell-surface-product": "linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(245, 238, 235, 0.95))",
        "--shell-surface-bottom": "linear-gradient(180deg, rgba(255, 252, 250, 0.90), rgba(247, 241, 238, 0.82))",
        "--shell-surface-title-band": "linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 241, 238, 0.92))",
        "--shell-surface-gallery-strip": "rgba(255, 251, 248, 0.82)",
        "--feature-card-surface": "linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(249, 243, 239, 0.96))",
        "--header-logo-plaque": "linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(249, 243, 239, 0.86))",
        "--header-agent-chip-surface": "linear-gradient(180deg, rgba(255, 246, 244, 0.96), rgba(246, 237, 234, 0.86))",
        "--product-canvas-highlight": "linear-gradient(180deg, rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.00) 46%)",
        "--product-shell-inset": "inset 0 1px 0 rgba(255, 255, 255, 0.84)",
        "--product-shell-outline": "inset 0 0 0 1px rgba(232, 0, 42, 0.08)",
        "--product-shell-glow": "0 18px 38px rgba(232, 0, 42, 0.08)",
        "--annotation-card-surface": "linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(249, 243, 239, 0.94))",
        "--annotation-card-border": "1px solid rgba(232, 0, 42, 0.14)",
        "--annotation-card-shadow": "0 10px 24px rgba(24, 16, 16, 0.10)",
        "--annotation-card-inset": "inset 0 1px 0 rgba(255, 255, 255, 0.90)",
        "--annotation-leader-opacity": "0.82",
        "--annotation-leader-gradient": "linear-gradient(90deg, rgba(232, 0, 42, 0.18), rgba(232, 0, 42, 0.86) 72%, rgba(232, 0, 42, 0.96))",
        "--annotation-leader-height": "2px",
        "--annotation-marker-ring": "rgba(232, 0, 42, 0.14)",
        "--annotation-marker-core-shadow": "0 4px 12px rgba(232, 0, 42, 0.28)",
        "--annotation-marker-size": "14px",
        "--annotation-marker-size-anchored": "16px",
        "--annotation-label-letter-spacing": "0.005em",
        "--title-band-top-rule": "linear-gradient(90deg, rgba(232, 0, 42, 0.18), rgba(232, 0, 42, 0.00))",
        "--gallery-item-surface": "linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 242, 239, 0.84))",
        "--gallery-item-border": "1px solid rgba(232, 0, 42, 0.08)",
    },
}

_FAMILY_A_SHELL_BORDER_PRESETS: dict[str, dict[str, str]] = {
    "soft_line": {
        "--shell-border-accent-alpha": "1a",
        "--shell-border-gallery": "1px solid rgba(255, 255, 255, 0.50)",
        "--shell-border-hero": "1px solid rgba(255, 255, 255, 0.24)",
        "--feature-card-border-alpha": "26",
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

_FAMILY_A_SHELL_SHADOW_PRESETS: dict[str, dict[str, str]] = {
    "none": {
        "--shell-shadow-main": "0 0 0 rgba(0, 0, 0, 0)",
        "--shell-shadow-secondary": "0 0 0 rgba(0, 0, 0, 0)",
        "--feature-card-shadow": "0 0 0 rgba(0, 0, 0, 0)",
        "--gallery-item-shadow": "0 0 0 rgba(0, 0, 0, 0)",
    },
    "soft": {
        "--shell-shadow-main": "0 20px 40px rgba(30, 18, 18, 0.13)",
        "--shell-shadow-secondary": "0 14px 28px rgba(28, 18, 18, 0.10)",
        "--feature-card-shadow": "0 12px 26px rgba(22, 14, 14, 0.11)",
        "--gallery-item-shadow": "0 10px 24px rgba(29, 18, 18, 0.11)",
    },
    "medium": {
        "--shell-shadow-main": "0 22px 42px rgba(26, 18, 18, 0.16)",
        "--shell-shadow-secondary": "0 16px 30px rgba(28, 20, 20, 0.12)",
        "--feature-card-shadow": "0 14px 28px rgba(24, 16, 16, 0.14)",
        "--gallery-item-shadow": "0 12px 24px rgba(31, 22, 22, 0.12)",
    },
}

_FAMILY_A_ACCENT_TONE_PRESETS: dict[str, str] = {
    "warm_red": "#E8002A",
    "brand_gold": "#C69214",
    "cool_blue": "#2D6CDF",
}

_FAMILY_A_TEXT_EMPHASIS_PRESETS: dict[str, dict[str, str]] = {
    "campaign_primary": {
        "brand": "#1A1A1A",
        "agent": "#6F5757",
        "title": "{accent}",
        "subtitle": "{accent}",
        "feature": "#1A1A1A",
    },
    "campaign_frozen": {
        "brand": "#171313",
        "agent": "#735E61",
        "title": "{accent}",
        "subtitle": "#705C66",
        "feature": "#1E191C",
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


def build_beautification_freeze_pack(
    *,
    shell_surface: str,
    shell_border: str,
    shell_shadow: str,
    accent_tone: str,
    text_emphasis: str,
) -> dict[str, object]:
    accent_color = _resolve_accent_color(accent_tone)
    text_colors = _resolve_text_colors(text_emphasis, accent_color)
    css_vars: dict[str, str] = {}
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
    return {
        "family_id": FAMILY_A_CAMPAIGN_EXPLAINER,
        "beauty_tokens": TemplateBeautyTokensSpec(
            shell_surface=shell_surface,
            shell_border=shell_border,
            shell_shadow=shell_shadow,
            accent_tone=accent_tone,
            text_emphasis=text_emphasis,
        ),
        "accent_color": accent_color,
        "text_colors": text_colors,
        "css_vars": css_vars,
    }


def _resolve_shell_surface_vars(shell_surface: str) -> dict[str, str]:
    if shell_surface not in _FAMILY_A_SHELL_SURFACE_PRESETS:
        raise ValueError(f"Unsupported shell_surface: {shell_surface}")
    return dict(_FAMILY_A_SHELL_SURFACE_PRESETS[shell_surface])


def _resolve_shell_border_vars(shell_border: str, accent_color: str) -> dict[str, str]:
    if shell_border not in _FAMILY_A_SHELL_BORDER_PRESETS:
        raise ValueError(f"Unsupported shell_border: {shell_border}")
    preset = _FAMILY_A_SHELL_BORDER_PRESETS[shell_border]
    accent_alpha = preset["--shell-border-accent-alpha"]
    feature_alpha = preset["--feature-card-border-alpha"]
    resolved = {
        "--shell-border-header": f"1px solid {accent_color}{accent_alpha}",
        "--shell-border-hero": preset["--shell-border-hero"],
        "--shell-border-product": f"1px solid {accent_color}{accent_alpha}",
        "--shell-border-bottom": f"1px solid {accent_color}{accent_alpha}",
        "--shell-border-gallery": preset["--shell-border-gallery"],
        "--feature-card-border": f"1px solid {accent_color}{feature_alpha}",
    }
    return resolved


def _resolve_shell_shadow_vars(shell_shadow: str) -> dict[str, str]:
    if shell_shadow not in _FAMILY_A_SHELL_SHADOW_PRESETS:
        raise ValueError(f"Unsupported shell_shadow: {shell_shadow}")
    return dict(_FAMILY_A_SHELL_SHADOW_PRESETS[shell_shadow])


def _resolve_accent_color(accent_tone: str) -> str:
    if accent_tone not in _FAMILY_A_ACCENT_TONE_PRESETS:
        raise ValueError(f"Unsupported accent_tone: {accent_tone}")
    return _FAMILY_A_ACCENT_TONE_PRESETS[accent_tone]


def _resolve_text_colors(text_emphasis: str, accent_color: str) -> dict[str, str]:
    if text_emphasis not in _FAMILY_A_TEXT_EMPHASIS_PRESETS:
        raise ValueError(f"Unsupported text_emphasis: {text_emphasis}")
    preset = _FAMILY_A_TEXT_EMPHASIS_PRESETS[text_emphasis]
    return {key: value.format(accent=accent_color) for key, value in preset.items()}
