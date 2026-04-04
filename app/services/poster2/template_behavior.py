from __future__ import annotations

from dataclasses import dataclass, replace

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
_SUPPORTED_FEATURE_MODES = {"count_driven_callout_stack", "uniform_callout_stack", "product_anchor_callouts"}
_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS = 3  # Fixed; enforces annotation items within primary slot y-range
                                         # (callouts 0-2 have anchor_y 250/350/450, within primary [188,548];
                                         #  callout 3 has anchor_y 550, which falls in the inter-slot gap [548,564])
_SUPPORTED_PRODUCT_ANNOTATION_MODES = {"none", "right_stack_mirror", "product_anchor_callouts"}
_SUPPORTED_PRODUCT_LAYOUT_MODES = {"single_primary", "primary_secondary_dual"}

# Frozen geometry for primary_secondary_dual product layout mode (geometry_mode = primary_secondary_dual_v2).
# Lane model: external right lane — annotation labels (x=784+) are outside the product region right
# boundary (x=756); image-slot sizing is fully independent of label_bounds.
# Primary slot: upper ~67% of the product region; receives all annotation callouts.
# Secondary slot: ~27% of the product region; no callouts, no annotation ownership.
# Bottom breathing room: 20px clear gap between secondary bottom (y=708) and canvas bottom (y=728).
# Parent region (scenario_cover_product_contain): x=456, y=188, w=300, h=540.
# Slot arithmetic: 360 (primary) + 16 (gap) + 144 (secondary) + 20 (breathing) = 540.
# Gap between primary bottom and secondary top: 564-(188+360)=16px.
_PRODUCT_DUAL_PRIMARY_SLOT: dict[str, int] = {"x": 456, "y": 188, "w": 300, "h": 360}
_PRODUCT_DUAL_SECONDARY_SLOT: dict[str, int] = {"x": 456, "y": 564, "w": 300, "h": 144}
_PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT: dict[str, int] = {"x": 456, "y": 188, "w": 300, "h": 540}
_PRODUCT_REGION_OUTER_W = 472
_PRODUCT_CANVAS_SHELL_W = 300

# Fixed product text shell bounds — the reserved text surface to the right of the canvas shell.
# This is a static sibling of product_canvas_shell_layer; it does not collapse with annotation count.
# x=784: product_region_x (456) + canvas_shell_w (300) + 28px gap
# y=216: product_region_y (188) + 28px top pad
# w=144: annotation label slot width (all 3 slots share this width)
# h=276: bottom_of_slot_3 (y=416+h=76=492) − top_of_slot_1 (y=216) = 276 (PR-C: label_box h 60→76)
# Right edge: 784 + 144 = 928 = product_region_x (456) + outer_w (472) ✓
# Does not compete with canvas: text_shell_x (784) > canvas_right (456+300=756) ✓
_PRODUCT_TEXT_SHELL_X = 784
_PRODUCT_TEXT_SHELL_Y = 216
_PRODUCT_TEXT_SHELL_W = 144
_PRODUCT_TEXT_SHELL_H = 276

# Frozen owner surfaces for product_region.
# These are the only surfaces that carry product ownership.
# Annotation shell anchors exclusively to product_primary_slot.
# Secondary slot never becomes an annotation owner.
_FROZEN_PRODUCT_OWNER_SURFACES: frozenset[str] = frozenset({
    "product_canvas_shell_layer",
    "product_text_shell_layer",
    "product_primary_slot",
    "product_secondary_slot",
    "product_image_layer",
    "product_secondary_image_layer",
    "product_annotation_shell_layer",
    "product_annotation_items_layer",
})
_PRODUCT_ANNOTATION_OWNER_SLOT = "product_primary_slot"

# Frozen text layer ownership map: each text layer_id maps to its canonical owner_region.
# These are immutable; no renderer branch or CSS may reassign ownership.
_TEXT_LAYER_OWNER_MAP: dict[str, str] = {
    "header_text_layer": "header_region",
    "title_text_layer": "title_band_region",
    "subtitle_text_layer": "title_band_region",
}

# Frozen annotation slot IDs for product_region text (product_annotation_slot_1/2/3).
# All three slots are owned exclusively by product_region.
_FROZEN_PRODUCT_ANNOTATION_SLOT_IDS: tuple[str, ...] = (
    "product_annotation_slot_1",
    "product_annotation_slot_2",
    "product_annotation_slot_3",
)
_PRODUCT_ANNOTATION_TEXT_OWNER_REGION = "product_region"

_SUPPORTED_BOTTOM_MODES = {
    "title_gallery_split",
    "gallery_only",
    "text_only_expanded",
    "text_gallery_expanded",
}
# Legacy request aliases: applied before validation; never reach the resolver.
_BOTTOM_MODE_ALIASES: dict[str, str] = {
    "title_only": "text_only_expanded",  # title_only superseded by text_only_expanded
}

# Structural expansion: new modes start the bottom shell higher than the frozen baseline (y=728).
# text_only_expanded and text_gallery_expanded share y=640 as the shell top.
# title_gallery_split uses y=680 (PR-6D: +40px total shift from 640 eliminates bottom-image overlap/clipping).
# text_only_expanded shell height = title_band_height (PR-6D: content-proportionate, no dead canvas below).
_EXPANDED_BOTTOM_SHELL_TOPS: dict[str, int] = {
    "title_gallery_split": 680,   # PR-6D: shifted down 40px from 640 (660→680) to fully close bottom-image overlap
    "text_only_expanded": 640,    # PR-6B: shell top fixed; PR-6D: shell height = title_band_height (content-proportionate)
    "text_gallery_expanded": 640, # 384px capacity
}
_SUPPORTED_GALLERY_MODES = {"strip_local_visible_only", "supporting_packshots"}
_SUPPORTED_HEADER_MODES = {"identity_left_agent_right", "brand_block_two_line", "brand_only"}
_SHELL_SURFACE_PRESETS: dict[str, dict[str, str]] = {
    "glass_light": {
        "--shell-surface-header": "linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(252, 245, 243, 0.92))",
        "--shell-surface-scenario-safe": "linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(247, 238, 234, 0.26))",
        "--shell-surface-scenario-real": "linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02))",
        "--shell-surface-product": "linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(250, 242, 240, 0.92))",
        "--shell-surface-bottom": "linear-gradient(180deg, rgba(255, 255, 255, 0.74), rgba(255, 248, 246, 0.60))",
        "--shell-surface-title-band": "linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 248, 245, 0.90))",
        "--shell-surface-gallery-strip": "rgba(255, 255, 255, 0.72)",
        "--feature-card-surface": "rgba(255, 255, 255, 0.96)",
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
_SHELL_SHADOW_PRESETS: dict[str, dict[str, str]] = {
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
class ResolvedHeaderBehavior:
    mode: str
    lane_layout_mode: str               # "single_line" | "two_line" | "brand_only"
    identity_zone_mode: str             # "logo_and_brand" | "brand_only"
    agent_pill_collapse_condition: str  # "always_collapse" | "collapse_when_empty"
    agent_pill_visible: bool
    brand_text_policy: str
    content_priority_policy: str
    requested_brand_text_present: bool
    requested_agent_text_present: bool
    effective_brand_text_present: bool
    effective_agent_text_present: bool
    brand_line_clamp: int
    brand_char_budget: int
    agent_line_clamp: int
    agent_char_budget: int
    layout_metrics: dict[str, int]

    css_classes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "lane_layout_mode": self.lane_layout_mode,
            "identity_zone_mode": self.identity_zone_mode,
            "agent_pill_collapse_condition": self.agent_pill_collapse_condition,
            "agent_pill_visible": self.agent_pill_visible,
            "brand_text_policy": self.brand_text_policy,
            "content_priority_policy": self.content_priority_policy,
            "requested_brand_text_present": self.requested_brand_text_present,
            "requested_agent_text_present": self.requested_agent_text_present,
            "effective_brand_text_present": self.effective_brand_text_present,
            "effective_agent_text_present": self.effective_agent_text_present,
            "brand_line_clamp": self.brand_line_clamp,
            "brand_char_budget": self.brand_char_budget,
            "agent_line_clamp": self.agent_line_clamp,
            "agent_char_budget": self.agent_char_budget,
            "layout_metrics": dict(self.layout_metrics),
            "css_classes": list(self.css_classes),
        }


@dataclass(frozen=True)
class ResolvedHeroBehavior:
    mode: str
    scenario_enabled: bool
    scenario_uses_safe_fill: bool
    scenario_render_policy: str
    product_render_policy: str
    peer_layout_policy: str
    scenario_fit: str
    scenario_anchor: str
    product_fit: str
    product_anchor: str
    layout_metrics: dict[str, int]
    css_classes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "scenario_enabled": self.scenario_enabled,
            "scenario_uses_safe_fill": self.scenario_uses_safe_fill,
            "scenario_render_policy": self.scenario_render_policy,
            "product_render_policy": self.product_render_policy,
            "peer_layout_policy": self.peer_layout_policy,
            "scenario_fit": self.scenario_fit,
            "scenario_anchor": self.scenario_anchor,
            "product_fit": self.product_fit,
            "product_anchor": self.product_anchor,
            "layout_metrics": dict(self.layout_metrics),
            "css_classes": list(self.css_classes),
        }


@dataclass(frozen=True)
class ResolvedProductBehavior:
    annotation_mode: str
    product_layout_mode: str                          # "single_primary" | "primary_secondary_dual"
    product_layout_mode_reason: str
    product_geometry_mode: str
    product_geometry_mode_reason: str
    product_primary_slot: dict[str, int]              # {x, y, w, h} of primary product image region
    product_primary_image_fit: str                    # "contain" | "cover" — fit policy for primary image
    product_secondary_slot: dict[str, int] | None     # {x, y, w, h} of secondary product image region, or None
    product_secondary_slot_rendered: bool
    product_secondary_asset_policy: str
    visible_annotation_count: int
    max_annotation_items: int
    annotation_count_policy: str
    annotation_connector_policy: str
    annotation_marker_policy: str
    annotation_shell_policy: str
    annotation_bounds_policy: str
    text_budget_policy: str
    line_clamp: int
    char_budget: int
    layout_metrics: dict[str, object]
    annotation_items: tuple[dict[str, object], ...]
    css_classes: tuple[str, ...]
    product_text_shell_bounds: dict[str, int]

    def as_dict(self) -> dict[str, object]:
        return {
            "annotation_mode": self.annotation_mode,
            "product_layout_mode": self.product_layout_mode,
            "product_layout_mode_reason": self.product_layout_mode_reason,
            "product_geometry_mode": self.product_geometry_mode,
            "product_geometry_mode_reason": self.product_geometry_mode_reason,
            "product_primary_slot": dict(self.product_primary_slot),
            "product_primary_image_fit": self.product_primary_image_fit,
            "product_secondary_slot": dict(self.product_secondary_slot) if self.product_secondary_slot else None,
            "product_secondary_slot_rendered": self.product_secondary_slot_rendered,
            "product_secondary_asset_policy": self.product_secondary_asset_policy,
            "visible_annotation_count": self.visible_annotation_count,
            "max_annotation_items": self.max_annotation_items,
            "annotation_count_policy": self.annotation_count_policy,
            "annotation_connector_policy": self.annotation_connector_policy,
            "annotation_marker_policy": self.annotation_marker_policy,
            "annotation_shell_policy": self.annotation_shell_policy,
            "annotation_bounds_policy": self.annotation_bounds_policy,
            "text_budget_policy": self.text_budget_policy,
            "line_clamp": self.line_clamp,
            "char_budget": self.char_budget,
            "layout_metrics": dict(self.layout_metrics),
            "annotation_items": [dict(item) for item in self.annotation_items],
            "css_classes": list(self.css_classes),
            "product_text_shell_bounds": dict(self.product_text_shell_bounds),
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
    text_budget_policy: str
    line_clamp: int
    char_budget: int
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
            "text_budget_policy": self.text_budget_policy,
            "line_clamp": self.line_clamp,
            "char_budget": self.char_budget,
            "box_h": self.box_h,
            "gap": self.gap,
            "start_strategy": self.start_strategy,
        }


@dataclass(frozen=True)
class ResolvedBottomBehavior:
    mode: str
    requested_mode: str | None
    effective_mode: str
    mode_override_reason: str
    bottom_layout_mode: str          # structural expansion mode; "none" for frozen baseline modes
    bottom_shell_top: int            # actual y-start of the bottom shell
    gallery_mode: str
    requested_gallery_count: int
    normalized_gallery_count: int
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
    title_band_sizing_mode: str
    title_band_growth_policy: str
    subtitle_overflow_policy: str
    title_text_budget_policy: str
    subtitle_text_budget_policy: str
    content_priority_policy: str
    peer_balance_policy: str
    bottom_peer_balance_policy: str
    gallery_distribution_policy: str
    gallery_shell_frame_policy: str
    gallery_strip_shift_policy: str
    gallery_aspect_policy: str
    gallery_spacing_policy: str
    bottom_text_emphasis_policy: str
    title_band_expansion_policy: str
    title_line_clamp: int
    subtitle_line_clamp: int
    title_char_budget: int
    subtitle_char_budget: int
    layout_metrics: dict[str, object]
    bottom_region_state: str
    collapsed_optional_slots: tuple[str, ...]
    subtitle_slot_state: dict[str, object]
    gallery_slot_states: tuple[dict[str, object], ...]
    css_classes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "requested_mode": self.requested_mode,
            "effective_mode": self.effective_mode,
            "mode_override_reason": self.mode_override_reason,
            "bottom_layout_mode": self.bottom_layout_mode,
            "bottom_shell_top": self.bottom_shell_top,
            "gallery_mode": self.gallery_mode,
            "requested_gallery_count": self.requested_gallery_count,
            "normalized_gallery_count": self.normalized_gallery_count,
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
            "title_band_sizing_mode": self.title_band_sizing_mode,
            "title_band_growth_policy": self.title_band_growth_policy,
            "subtitle_overflow_policy": self.subtitle_overflow_policy,
            "title_text_budget_policy": self.title_text_budget_policy,
            "subtitle_text_budget_policy": self.subtitle_text_budget_policy,
            "content_priority_policy": self.content_priority_policy,
            "peer_balance_policy": self.peer_balance_policy,
            "bottom_peer_balance_policy": self.bottom_peer_balance_policy,
            "gallery_distribution_policy": self.gallery_distribution_policy,
            "gallery_shell_frame_policy": self.gallery_shell_frame_policy,
            "gallery_strip_shift_policy": self.gallery_strip_shift_policy,
            "gallery_aspect_policy": self.gallery_aspect_policy,
            "gallery_spacing_policy": self.gallery_spacing_policy,
            "bottom_text_emphasis_policy": self.bottom_text_emphasis_policy,
            "title_band_expansion_policy": self.title_band_expansion_policy,
            "title_line_clamp": self.title_line_clamp,
            "subtitle_line_clamp": self.subtitle_line_clamp,
            "title_char_budget": self.title_char_budget,
            "subtitle_char_budget": self.subtitle_char_budget,
            "layout_metrics": dict(self.layout_metrics),
            "bottom_region_state": self.bottom_region_state,
            "collapsed_optional_slots": list(self.collapsed_optional_slots),
            "subtitle_slot_state": dict(self.subtitle_slot_state),
            "gallery_slot_states": [dict(item) for item in self.gallery_slot_states],
        }


@dataclass(frozen=True)
class ResolvedTemplateLayoutPolicy:
    content_priority_policy: str
    region_priority_policy: str
    peer_rebalance_policy: str
    layout_density_mode: str
    decision_scope: str
    drivers: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "content_priority_policy": self.content_priority_policy,
            "region_priority_policy": self.region_priority_policy,
            "peer_rebalance_policy": self.peer_rebalance_policy,
            "layout_density_mode": self.layout_density_mode,
            "decision_scope": self.decision_scope,
            "drivers": list(self.drivers),
        }


@dataclass(frozen=True)
class ResolvedTemplateBehavior:
    hero_mode: str
    feature_mode: str
    product_annotation_mode: str
    header_mode: str | None
    bottom_mode: str | None
    gallery_mode: str | None
    beauty_tokens: TemplateBeautyTokensSpec
    hero_policy: ResolvedHeroBehavior
    product_policy: ResolvedProductBehavior
    feature_policy: ResolvedFeatureBehavior
    bottom_policy: ResolvedBottomBehavior
    template_layout_policy: ResolvedTemplateLayoutPolicy
    header_policy: ResolvedHeaderBehavior
    css_vars: dict[str, str]
    accent_color: str
    text_colors: dict[str, str]
    root_classes: tuple[str, ...]

    def css_var_style(self) -> str:
        return "; ".join(f"{key}: {value}" for key, value in self.css_vars.items())

    def root_class_name(self) -> str:
        return " ".join(self.root_classes)

    def as_dict(self) -> dict[str, object]:
        product_annotation_mode = (
            self.feature_mode
            if self.feature_mode == "product_anchor_callouts"
            else "none"
        )
        return {
            "behavior_modes": {
                "hero_mode": self.hero_mode,
                "feature_mode": self.feature_mode,
                "product_annotation_mode": self.product_annotation_mode,
                "product_layout_mode": self.product_policy.product_layout_mode,
                "product_geometry_mode": self.product_policy.product_geometry_mode,
                "header_mode": self.header_mode,
                "bottom_mode": self.bottom_mode,
                "bottom_layout_mode": self.bottom_policy.bottom_layout_mode,
                "gallery_mode": self.gallery_mode,
            },
            "hero_policy": self.hero_policy.as_dict(),
            "product_policy": self.product_policy.as_dict(),
            "feature_policy": self.feature_policy.as_dict(),
            "bottom_policy": self.bottom_policy.as_dict(),
            "template_layout_policy": self.template_layout_policy.as_dict(),
            "header_policy": self.header_policy.as_dict(),
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
    brand_name: str | None = None,
    gallery_requested_count: int | None = None,
    gallery_input_count_normalized: int | None = None,
    gallery_resolved_count: int | None = None,
    bottom_mode: str | None = None,
    gallery_mode: str | None = None,
    agent_name: str | None = None,
    has_product_secondary_asset: bool = False,
) -> ResolvedTemplateBehavior:
    modes = spec.behavior_modes
    beauty = spec.beauty_tokens
    hero_mode = _validate_token(modes.hero_mode, _SUPPORTED_HERO_MODES, "hero_mode")
    feature_mode = _validate_token(modes.feature_mode, _SUPPORTED_FEATURE_MODES, "feature_mode")
    requested_product_annotation_mode = _validate_token(
        modes.product_annotation_mode,
        _SUPPORTED_PRODUCT_ANNOTATION_MODES,
        "product_annotation_mode",
    )
    product_annotation_mode = (
        requested_product_annotation_mode
        if feature_mode == "product_anchor_callouts"
        else "none"
    )
    product_layout_mode = _validate_token(
        modes.product_layout_mode,
        _SUPPORTED_PRODUCT_LAYOUT_MODES,
        "product_layout_mode",
    )
    _raw_bottom_mode = bottom_mode or modes.bottom_mode
    resolved_bottom_mode = _validate_token(
        _BOTTOM_MODE_ALIASES.get(_raw_bottom_mode, _raw_bottom_mode),
        _SUPPORTED_BOTTOM_MODES,
        "bottom_mode",
    )
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
        requested_bottom_mode=bottom_mode,
        template_bottom_mode=modes.bottom_mode,
        gallery_mode=resolved_gallery_mode,
        title_text=title_text,
        subtitle_text=subtitle_text,
        requested_gallery_count=gallery_requested_count or 0,
        normalized_gallery_count=gallery_input_count_normalized if gallery_input_count_normalized is not None else gallery_requested_count or 0,
        resolved_gallery_count=gallery_resolved_count or 0,
        max_items=spec.gallery_slot.count,
    )
    product_policy = resolve_product_behavior(
        spec,
        annotation_mode=product_annotation_mode,
        product_layout_mode=product_layout_mode,
        has_product_secondary_asset=has_product_secondary_asset,
        requested_feature_count=feature_count or 0,
        hero_policy=hero_policy,
    )
    template_layout_policy = resolve_template_layout_policy(
        feature_policy=feature_policy,
        bottom_policy=bottom_policy,
    )
    feature_policy = _apply_template_layout_policy_to_feature(feature_policy, template_layout_policy)
    header_policy = resolve_header_behavior(
        modes.header_mode or "identity_left_agent_right",
        brand_name=brand_name,
        agent_name=agent_name,
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
    css_vars.update(_resolve_bottom_behavior_vars(bottom_policy))
    css_vars.update(_resolve_header_behavior_vars(header_policy))
    return ResolvedTemplateBehavior(
        hero_mode=hero_mode,
        feature_mode=feature_mode,
        product_annotation_mode=product_annotation_mode,
        header_mode=header_policy.mode,
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
        product_policy=product_policy,
        feature_policy=feature_policy,
        bottom_policy=bottom_policy,
        template_layout_policy=template_layout_policy,
        header_policy=header_policy,
        css_vars=css_vars,
        accent_color=accent_color,
        text_colors=text_colors,
        root_classes=(
            *hero_policy.css_classes,
            _css_mode_class("feature-behavior", feature_mode),
            _css_mode_class("layout-density", template_layout_policy.layout_density_mode),
            _css_mode_class("region-priority", template_layout_policy.region_priority_policy),
            _css_mode_class("template-peer-rebalance", template_layout_policy.peer_rebalance_policy),
            *product_policy.css_classes,
            *bottom_policy.css_classes,
            *header_policy.css_classes,
        ),
    )


def resolve_hero_behavior(hero_mode: str) -> ResolvedHeroBehavior:
    if hero_mode == "scenario_cover_product_contain":
        return ResolvedHeroBehavior(
            mode=hero_mode,
            scenario_enabled=True,
            scenario_uses_safe_fill=True,
            scenario_render_policy="scenario_optional_safe_fill_cover",
            product_render_policy="product_contain_centered",
            peer_layout_policy="fixed_dual_hero_peer_regions",
            scenario_fit="cover",
            scenario_anchor="center",
            product_fit="contain",
            product_anchor="center",
            layout_metrics={
                "scenario_region_x": 96,
                "scenario_region_y": 188,
                "scenario_region_w": 288,
                "scenario_region_h": 520,
                "product_region_x": 456,
                "product_region_y": 188,
                "product_region_w": _PRODUCT_REGION_OUTER_W,
                "product_region_h": 540,
                "product_pad_top": 24,
                "product_pad_right": 18,
                "product_pad_bottom": 10,
                "product_pad_left": 18,
            },
            css_classes=(_css_mode_class("hero-mode", hero_mode),),
        )
    if hero_mode == "single_product_focus":
        return ResolvedHeroBehavior(
            mode=hero_mode,
            scenario_enabled=False,
            scenario_uses_safe_fill=False,
            scenario_render_policy="scenario_disabled",
            product_render_policy="product_contain_bottom_weighted",
            peer_layout_policy="single_product_without_scenario_peer",
            scenario_fit="cover",
            scenario_anchor="center",
            product_fit="contain",
            product_anchor="bottom",
            layout_metrics={
                "scenario_region_x": 96,
                "scenario_region_y": 188,
                "scenario_region_w": 288,
                "scenario_region_h": 520,
                "product_region_x": 456,
                "product_region_y": 188,
                "product_region_w": _PRODUCT_REGION_OUTER_W,
                "product_region_h": 540,
                "product_pad_top": 24,
                "product_pad_right": 18,
                "product_pad_bottom": 10,
                "product_pad_left": 18,
            },
            css_classes=(_css_mode_class("hero-mode", hero_mode), "hero-scenario-disabled"),
        )
    raise ValueError(f"Unsupported hero_mode: {hero_mode}")


def resolve_product_behavior(
    spec: TemplateSpec,
    *,
    annotation_mode: str,
    product_layout_mode: str = "single_primary",
    has_product_secondary_asset: bool = False,
    requested_feature_count: int,
    hero_policy: ResolvedHeroBehavior,
) -> ResolvedProductBehavior:
    _validate_token(product_layout_mode, _SUPPORTED_PRODUCT_LAYOUT_MODES, "product_layout_mode")
    effective_product_layout_mode = product_layout_mode
    if product_layout_mode == "single_primary" and has_product_secondary_asset:
        effective_product_layout_mode = "primary_secondary_dual"
        product_layout_mode_reason = "auto_promoted_by_secondary_asset"
    elif product_layout_mode == "primary_secondary_dual":
        product_layout_mode_reason = "template_mode_primary_secondary_dual"
    else:
        product_layout_mode_reason = "single_primary_without_secondary_asset"
    if effective_product_layout_mode == "primary_secondary_dual":
        product_geometry_mode = "primary_secondary_dual_v2"
        product_geometry_mode_reason = "dual_image_geometry_v2_selected"
    else:
        product_geometry_mode = "single_primary_v1"
        product_geometry_mode_reason = "single_image_geometry_baseline"
    max_items = min(len(spec.feature_callouts), _PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS)
    visible_annotation_count = 0 if annotation_mode == "none" else min(max(requested_feature_count, 0), max_items)
    hero_metrics = hero_policy.layout_metrics
    product_region = {
        "x": int(hero_metrics["product_region_x"]),
        "y": int(hero_metrics["product_region_y"]),
        "w": int(hero_metrics["product_region_w"]),
        "h": int(hero_metrics["product_region_h"]),
    }

    # Resolve product slot geometry from layout mode.
    if effective_product_layout_mode == "primary_secondary_dual":
        product_primary_slot: dict[str, int] = dict(_PRODUCT_DUAL_PRIMARY_SLOT)
        product_secondary_slot: dict[str, int] | None = dict(_PRODUCT_DUAL_SECONDARY_SLOT)
        product_secondary_slot_rendered = True
        product_secondary_asset_policy = "secondary_present"
    else:
        product_primary_slot = dict(_PRODUCT_SINGLE_PRIMARY_SLOT_DEFAULT)
        product_secondary_slot = None
        product_secondary_slot_rendered = False
        product_secondary_asset_policy = "secondary_absent_collapsed"

    if annotation_mode == "none":
        annotation_count_policy = "annotations_disabled"
        annotation_connector_policy = "annotation_connectors_disabled"
        annotation_marker_policy = "annotation_markers_disabled"
        annotation_shell_policy = "annotation_shell_collapsed"
        annotation_bounds_policy = "no_annotation_bounds"
        text_budget_policy = "annotation_budget_disabled"
        line_clamp = 0
        char_budget = 0
        annotation_items: list[dict[str, object]] = []
        annotation_shell = {"x": product_region["x"], "y": product_region["y"], "w": 0, "h": 0}
    else:
        char_budget = {1: 44, 2: 38, 3: 32}.get(max(visible_annotation_count, 1), 32)
        line_clamp = 2
        if annotation_mode == "right_stack_mirror":
            annotation_count_policy = "fixed_3_right_stack_annotations"
            annotation_connector_policy = "annotation_connectors_suppressed"
            annotation_marker_policy = "annotation_markers_suppressed"
            annotation_shell_policy = "right_stack_annotation_shell"
            annotation_bounds_policy = "template_label_box_fixed"
            text_budget_policy = "fixed_3_right_stack_two_line_budget"
        elif annotation_mode == "product_anchor_callouts":
            annotation_count_policy = "fixed_3_product_anchor_annotations"
            annotation_connector_policy = "product_anchor_leader_line"
            annotation_marker_policy = "product_anchor_marker"
            annotation_shell_policy = "product_anchor_annotation_shell"
            annotation_bounds_policy = "template_anchor_fixed"
            text_budget_policy = "fixed_3_anchor_three_line_budget"
            line_clamp = 3
        else:
            raise ValueError(f"Unsupported product_annotation_mode: {annotation_mode}")

        annotation_items = []
        left = None
        top = None
        right = None
        bottom = None
        for index, callout in enumerate(spec.feature_callouts[:max_items], start=1):
            label_box = callout.label_box
            annotation_items.append(
                {
                    "slot_id": f"product_annotation_slot_{index}",
                    "anchor_index": index - 1,
                    "anchor_x": int(callout.anchor_x) if annotation_mode == "product_anchor_callouts" else None,
                    "anchor_y": int(callout.anchor_y) if annotation_mode == "product_anchor_callouts" else None,
                    "anchor_color": callout.anchor_color if annotation_mode == "product_anchor_callouts" else None,
                    "label_bounds": {
                        "x": int(label_box.x),
                        "y": int(label_box.y),
                        "w": int(label_box.w),
                        "h": int(label_box.h),
                    },
                    "connector_policy": annotation_connector_policy,
                    "marker_policy": annotation_marker_policy,
                    "positions_source": "template_spec_fixed",
                }
            )
            left = int(label_box.x) if left is None else min(left, int(label_box.x))
            top = int(label_box.y) if top is None else min(top, int(label_box.y))
            right = int(label_box.x + label_box.w) if right is None else max(right, int(label_box.x + label_box.w))
            bottom = int(label_box.y + label_box.h) if bottom is None else max(bottom, int(label_box.y + label_box.h))
        annotation_shell = {
            "x": int(left or product_region["x"]),
            "y": int(top or product_region["y"]),
            "w": int((right - left) if left is not None and right is not None else 0),
            "h": int((bottom - top) if top is not None and bottom is not None else 0),
        }

    layout_metrics = {
        "product_region_x": product_region["x"],
        "product_region_y": product_region["y"],
        "product_region_w": product_region["w"],
        "product_region_h": product_region["h"],
        "product_canvas_shell_x": product_region["x"],
        "product_canvas_shell_y": product_region["y"],
        "product_canvas_shell_w": _PRODUCT_CANVAS_SHELL_W,
        "product_canvas_shell_h": product_region["h"],
        "product_primary_slot_x": product_primary_slot["x"],
        "product_primary_slot_y": product_primary_slot["y"],
        "product_primary_slot_w": product_primary_slot["w"],
        "product_primary_slot_h": product_primary_slot["h"],
        "product_secondary_slot_x": product_secondary_slot["x"] if product_secondary_slot else None,
        "product_secondary_slot_y": product_secondary_slot["y"] if product_secondary_slot else None,
        "product_secondary_slot_w": product_secondary_slot["w"] if product_secondary_slot else None,
        "product_secondary_slot_h": product_secondary_slot["h"] if product_secondary_slot else None,
        "annotation_shell_x": int(annotation_shell["x"]),
        "annotation_shell_y": int(annotation_shell["y"]),
        "annotation_shell_w": int(annotation_shell["w"]),
        "annotation_shell_h": int(annotation_shell["h"]),
        "product_text_shell_x": _PRODUCT_TEXT_SHELL_X,
        "product_text_shell_y": _PRODUCT_TEXT_SHELL_Y,
        "product_text_shell_w": _PRODUCT_TEXT_SHELL_W,
        "product_text_shell_h": _PRODUCT_TEXT_SHELL_H,
    }

    return ResolvedProductBehavior(
        annotation_mode=annotation_mode,
        product_layout_mode=effective_product_layout_mode,
        product_layout_mode_reason=product_layout_mode_reason,
        product_geometry_mode=product_geometry_mode,
        product_geometry_mode_reason=product_geometry_mode_reason,
        product_primary_slot=product_primary_slot,
        product_primary_image_fit=hero_policy.product_fit,
        product_secondary_slot=product_secondary_slot,
        product_secondary_slot_rendered=product_secondary_slot_rendered,
        product_secondary_asset_policy=product_secondary_asset_policy,
        visible_annotation_count=visible_annotation_count,
        max_annotation_items=max_items,
        annotation_count_policy=annotation_count_policy,
        annotation_connector_policy=annotation_connector_policy,
        annotation_marker_policy=annotation_marker_policy,
        annotation_shell_policy=annotation_shell_policy,
        annotation_bounds_policy=annotation_bounds_policy,
        text_budget_policy=text_budget_policy,
        line_clamp=line_clamp,
        char_budget=char_budget,
        layout_metrics=layout_metrics,
        annotation_items=tuple(annotation_items),
        css_classes=(
            _css_mode_class("product-annotation", annotation_mode),
            _css_mode_class("product-annotation-count", str(visible_annotation_count)),
        ),
        product_text_shell_bounds={
            "x": _PRODUCT_TEXT_SHELL_X,
            "y": _PRODUCT_TEXT_SHELL_Y,
            "w": _PRODUCT_TEXT_SHELL_W,
            "h": _PRODUCT_TEXT_SHELL_H,
        },
    )


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
            text_budget_policy="count_scaled_two_line_budget",
            line_clamp=2,
            char_budget=_resolve_feature_char_budget(clamped_count, feature_mode),
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
            text_budget_policy="uniform_two_line_budget",
            line_clamp=2,
            char_budget=_resolve_feature_char_budget(clamped_count, feature_mode),
            box_h=int(layout_spec["box_h"]),
            gap=int(layout_spec["gap"]),
            start_strategy="centered_in_region",
        )
    if feature_mode == "product_anchor_callouts":
        # Fixed 3 anchor points on the product image; positions are template-spec-defined.
        # No drag-and-drop, no dynamic slot count beyond 3.
        anchor_visible = min(max(requested_count, 0), _PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS)
        anchor_clamped = min(max(anchor_visible, 1), _PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS)
        anchor_char_budgets = {1: 44, 2: 38, 3: 32}
        anchor_box_h = _FEATURE_MODE_LAYOUT_SPECS[anchor_clamped]["box_h"]
        return ResolvedFeatureBehavior(
            mode=feature_mode,
            requested_item_count=requested_count,
            visible_item_count=anchor_visible,
            max_items=_PRODUCT_ANCHOR_CALLOUTS_MAX_ITEMS,
            visible_item_count_policy="fixed_3_anchor_points",
            connector_policy="product_anchor_leader_line",
            box_policy="anchor_fixed_position",
            truncation_policy="three_line_clamp",
            collapse_policy="collapse_when_empty",
            text_budget_policy="anchor_fixed_budget",
            line_clamp=3,
            char_budget=anchor_char_budgets[anchor_clamped],
            box_h=int(anchor_box_h),
            gap=0,
            start_strategy="template_anchor_fixed",
        )
    raise ValueError(f"Unsupported feature_mode: {feature_mode}")


def resolve_feature_layout_mode(count: int, feature_mode: str) -> tuple[int, dict[str, int | str]]:
    policy = resolve_feature_behavior(feature_mode, requested_count=count, max_items=4)
    return min(max(policy.visible_item_count, 1), 4), {
        "box_h": policy.box_h,
        "gap": policy.gap,
        "connector_policy": policy.connector_policy,
    }


def resolve_template_layout_policy(
    *,
    feature_policy: ResolvedFeatureBehavior,
    bottom_policy: ResolvedBottomBehavior,
) -> ResolvedTemplateLayoutPolicy:
    feature_dense = feature_policy.visible_item_count >= 3
    bottom_copy_dense = bottom_policy.title_band_sizing_mode == "expanded" or bottom_policy.subtitle_line_clamp >= 2
    bottom_gallery_dense = bottom_policy.visible_item_count >= 3
    drivers: list[str] = []
    if bottom_copy_dense:
        drivers.append("bottom_copy_dense")
    if bottom_gallery_dense:
        drivers.append("bottom_gallery_dense")
    if feature_dense:
        drivers.append("feature_region_dense")
    if bottom_policy.gallery_strip_rendered:
        drivers.append("bottom_gallery_present")
    if bottom_policy.title_band_rendered:
        drivers.append("bottom_title_band_present")

    if feature_dense and (bottom_copy_dense or bottom_gallery_dense):
        return ResolvedTemplateLayoutPolicy(
            content_priority_policy="bottom_copy_first_feature_stack_second",
            region_priority_policy="bottom_and_feature_dual_density",
            peer_rebalance_policy="feature_compacts_before_template_reflow",
            layout_density_mode="multi_region_dense",
            decision_scope="template_level_feature_bottom_rebalance",
            drivers=tuple(drivers),
        )
    if bottom_copy_dense or bottom_gallery_dense:
        return ResolvedTemplateLayoutPolicy(
            content_priority_policy="bottom_region_priority_before_template_shift",
            region_priority_policy="bottom_region_priority",
            peer_rebalance_policy="bottom_local_rebalance_only",
            layout_density_mode="bottom_dense",
            decision_scope="bottom_local_behavior_with_template_awareness",
            drivers=tuple(drivers),
        )
    if feature_dense:
        return ResolvedTemplateLayoutPolicy(
            content_priority_policy="feature_region_priority_before_bottom_shift",
            region_priority_policy="feature_region_priority",
            peer_rebalance_policy="feature_local_compaction_only",
            layout_density_mode="feature_dense",
            decision_scope="feature_local_behavior_with_template_awareness",
            drivers=tuple(drivers),
        )
    return ResolvedTemplateLayoutPolicy(
        content_priority_policy="balanced_local_region_preservation",
        region_priority_policy="local_region_autonomy",
        peer_rebalance_policy="local_region_behavior_only",
        layout_density_mode="balanced",
        decision_scope="local_region_behavior_only",
        drivers=tuple(drivers),
    )


def _apply_template_layout_policy_to_feature(
    feature_policy: ResolvedFeatureBehavior,
    template_layout_policy: ResolvedTemplateLayoutPolicy,
) -> ResolvedFeatureBehavior:
    if (
        template_layout_policy.peer_rebalance_policy == "feature_compacts_before_template_reflow"
        and feature_policy.visible_item_count >= 3
    ):
        return replace(
            feature_policy,
            box_h=max(feature_policy.box_h - 4, 56),
            gap=max(feature_policy.gap - 2, 8),
            char_budget=max(feature_policy.char_budget - 6, 20),
            start_strategy="top_weighted_compact_region",
        )
    return feature_policy


def _resolve_feature_char_budget(clamped_count: int, feature_mode: str) -> int:
    if feature_mode == "uniform_callout_stack":
        return {1: 36, 2: 32, 3: 28, 4: 24}[clamped_count]
    return {1: 38, 2: 34, 3: 28, 4: 24}[clamped_count]


def resolve_header_behavior(
    header_mode: str,
    *,
    brand_name: str | None = None,
    agent_name: str | None = None,
) -> ResolvedHeaderBehavior:
    _validate_token(header_mode, _SUPPORTED_HEADER_MODES, "header_mode")
    requested_brand_text_present = bool(brand_name)
    requested_agent_text_present = bool(agent_name)
    effective_brand_name = (brand_name or "").strip()
    effective_agent_name = (agent_name or "").strip()
    effective_brand_text_present = bool(effective_brand_name)
    effective_agent_text_present = bool(effective_agent_name)

    if header_mode == "identity_left_agent_right":
        lane_layout_mode = "single_line"
        identity_zone_mode = "logo_and_brand"
        agent_pill_collapse_condition = "collapse_when_empty"
        brand_text_policy = "single_line_brand_lockup"
        content_priority_policy = "brand_identity_priority_over_agent"
        brand_line_clamp = 1
        brand_char_budget = 40
        agent_line_clamp = 2
        agent_char_budget = 52
        layout_metrics = {
            "header_banner_left": 72,
            "header_banner_top": 56,
            "header_banner_width": 880,
            "header_banner_height": 104,
            "header_inner_left": 104,
            "header_inner_right": 112,
            "header_inner_top": 72,
            "header_inner_height": 56,
            "header_side_width": 228,
            "header_logo_width": 120,
            "header_logo_height": 64,
            "header_logo_gap": 20,
            "brand_slot_x": 244,
            "brand_slot_y": 88,
            "brand_slot_w": 416,
            "brand_slot_h": 36,
            "agent_slot_x": 684,
            "agent_slot_y": 96,
            "agent_slot_w": 228,
            "agent_slot_h": 36,
        }
    elif header_mode == "brand_block_two_line":
        lane_layout_mode = "two_line"
        identity_zone_mode = "logo_and_brand"
        agent_pill_collapse_condition = "collapse_when_empty"
        brand_text_policy = "two_line_brand_lockup"
        content_priority_policy = "brand_copy_priority_under_two_line_lockup"
        brand_line_clamp = 2
        brand_char_budget = 72
        agent_line_clamp = 1
        agent_char_budget = 28
        layout_metrics = {
            "header_banner_left": 72,
            "header_banner_top": 56,
            "header_banner_width": 880,
            "header_banner_height": 120,
            "header_inner_left": 104,
            "header_inner_right": 112,
            "header_inner_top": 68,
            "header_inner_height": 72,
            "header_side_width": 228,
            "header_logo_width": 120,
            "header_logo_height": 64,
            "header_logo_gap": 18,
            "brand_slot_x": 244,
            "brand_slot_y": 76,
            "brand_slot_w": 416,
            "brand_slot_h": 52,
            "agent_slot_x": 684,
            "agent_slot_y": 96,
            "agent_slot_w": 228,
            "agent_slot_h": 18,
        }
    elif header_mode == "brand_only":
        lane_layout_mode = "single_line"
        identity_zone_mode = "brand_only"
        agent_pill_collapse_condition = "always_collapse"
        brand_text_policy = "brand_only_single_line_lockup"
        content_priority_policy = "brand_only_priority"
        brand_line_clamp = 1
        brand_char_budget = 52
        agent_line_clamp = 1
        agent_char_budget = 0
        layout_metrics = {
            "header_banner_left": 72,
            "header_banner_top": 56,
            "header_banner_width": 880,
            "header_banner_height": 96,
            "header_inner_left": 104,
            "header_inner_right": 104,
            "header_inner_top": 74,
            "header_inner_height": 48,
            "header_side_width": 0,
            "header_logo_width": 0,
            "header_logo_height": 0,
            "header_logo_gap": 0,
            "brand_slot_x": 104,
            "brand_slot_y": 82,
            "brand_slot_w": 808,
            "brand_slot_h": 32,
            "agent_slot_x": 912,
            "agent_slot_y": 96,
            "agent_slot_w": 0,
            "agent_slot_h": 0,
        }
    else:
        raise ValueError(f"Unsupported header_mode: {header_mode}")

    agent_pill_visible = (
        False
        if agent_pill_collapse_condition == "always_collapse"
        else effective_agent_text_present
    )

    css_classes: tuple[str, ...] = (
        _css_mode_class("header-mode", header_mode),
        _css_mode_class("header-identity", identity_zone_mode),
    )
    if not agent_pill_visible:
        css_classes = (*css_classes, "header-agent-collapsed")
    if brand_line_clamp > 1:
        css_classes = (*css_classes, "header-brand-wrap")
    if agent_line_clamp > 1:
        css_classes = (*css_classes, "header-agent-wrap")

    return ResolvedHeaderBehavior(
        mode=header_mode,
        lane_layout_mode=lane_layout_mode,
        identity_zone_mode=identity_zone_mode,
        agent_pill_collapse_condition=agent_pill_collapse_condition,
        agent_pill_visible=agent_pill_visible,
        brand_text_policy=brand_text_policy,
        content_priority_policy=content_priority_policy,
        requested_brand_text_present=requested_brand_text_present,
        requested_agent_text_present=requested_agent_text_present,
        effective_brand_text_present=effective_brand_text_present,
        effective_agent_text_present=effective_agent_text_present,
        brand_line_clamp=brand_line_clamp,
        brand_char_budget=brand_char_budget,
        agent_line_clamp=agent_line_clamp,
        agent_char_budget=agent_char_budget,
        layout_metrics=layout_metrics,
        css_classes=css_classes,
    )


def _resolve_header_behavior_vars(header_policy: ResolvedHeaderBehavior) -> dict[str, str]:
    metrics = header_policy.layout_metrics
    return {
        "--header-banner-left": f"{int(metrics['header_banner_left'])}px",
        "--header-banner-top": f"{int(metrics['header_banner_top'])}px",
        "--header-banner-width": f"{int(metrics['header_banner_width'])}px",
        "--header-banner-height": f"{int(metrics['header_banner_height'])}px",
        "--header-inner-left": f"{int(metrics['header_inner_left'])}px",
        "--header-inner-right": f"{int(metrics['header_inner_right'])}px",
        "--header-inner-top": f"{int(metrics['header_inner_top'])}px",
        "--header-inner-height": f"{int(metrics['header_inner_height'])}px",
        "--header-side-width": f"{int(metrics['header_side_width'])}px",
        "--header-logo-width": f"{int(metrics['header_logo_width'])}px",
        "--header-logo-height": f"{int(metrics['header_logo_height'])}px",
        "--header-logo-gap": f"{int(metrics['header_logo_gap'])}px",
        "--header-brand-line-clamp": str(header_policy.brand_line_clamp),
        "--header-agent-line-clamp": str(header_policy.agent_line_clamp),
    }


def resolve_bottom_behavior(
    bottom_mode: str,
    *,
    requested_bottom_mode: str | None = None,
    template_bottom_mode: str | None = None,
    gallery_mode: str,
    title_text: str | None,
    subtitle_text: str | None,
    requested_gallery_count: int,
    normalized_gallery_count: int,
    resolved_gallery_count: int,
    max_items: int,
) -> ResolvedBottomBehavior:
    title_present = bool((title_text or "").strip())
    subtitle_present = bool((subtitle_text or "").strip())
    title_length = len((title_text or "").strip())
    subtitle_length = len((subtitle_text or "").strip())
    requested_gallery_count = min(max(requested_gallery_count, 0), max_items)
    normalized_gallery_count = min(max(normalized_gallery_count, 0), max_items)
    visible_item_count = min(max(resolved_gallery_count, 0), max_items)
    requested_runtime_mode = requested_bottom_mode or bottom_mode
    # bottom_mode is already canonical (alias applied by caller via _BOTTOM_MODE_ALIASES)
    resolved_bottom_layout_mode = bottom_mode  # always mirrors .mode
    actual_bottom_shell_top = _EXPANDED_BOTTOM_SHELL_TOPS.get(bottom_mode, 728)
    if requested_bottom_mode is None:
        mode_override_reason = "template_default_applied"
    elif requested_runtime_mode != bottom_mode:
        mode_override_reason = "legacy_alias_canonicalized"
    elif template_bottom_mode is not None and requested_runtime_mode == template_bottom_mode:
        mode_override_reason = "requested_matches_template_default"
    else:
        mode_override_reason = "request_override_applied"

    title_slot_rendered = title_present and bottom_mode != "gallery_only"
    subtitle_slot_rendered = subtitle_present and bottom_mode != "gallery_only" and title_present

    if bottom_mode == "title_gallery_split":
        title_band_rendered = title_slot_rendered
        gallery_strip_rendered = visible_item_count > 0
        gallery_content_policy = "render_real_gallery_items_in_local_strip_only"
    elif bottom_mode == "text_only_expanded":
        title_band_rendered = title_slot_rendered
        gallery_strip_rendered = False
        gallery_content_policy = "collapse_gallery_strip_expanded_text_only_mode"
    elif bottom_mode == "text_gallery_expanded":
        title_band_rendered = title_slot_rendered
        gallery_strip_rendered = visible_item_count > 0
        gallery_content_policy = "render_gallery_strip_in_expanded_text_gallery_mode"
    elif bottom_mode == "gallery_only":
        title_band_rendered = False
        gallery_strip_rendered = visible_item_count > 0
        gallery_content_policy = "render_gallery_strip_without_title_band"
    else:
        raise ValueError(f"Unsupported bottom_mode: {bottom_mode}")

    (
        title_band_sizing_mode,
        title_band_growth_policy,
        subtitle_overflow_policy,
        title_text_budget_policy,
        subtitle_text_budget_policy,
        content_priority_policy,
        peer_balance_policy,
        bottom_peer_balance_policy,
        gallery_distribution_policy,
        gallery_shell_frame_policy,
        gallery_strip_shift_policy,
        gallery_aspect_policy,
        gallery_spacing_policy,
        bottom_text_emphasis_policy,
        title_line_clamp,
        subtitle_line_clamp,
        title_char_budget,
        subtitle_char_budget,
        layout_metrics,
    ) = _resolve_bottom_layout_policies(
        bottom_mode=resolved_bottom_layout_mode,
        gallery_mode=gallery_mode,
        title_slot_rendered=title_slot_rendered,
        subtitle_slot_rendered=subtitle_slot_rendered,
        gallery_strip_rendered=gallery_strip_rendered,
        title_length=title_length,
        subtitle_length=subtitle_length,
        visible_item_count=visible_item_count,
        bottom_shell_top=actual_bottom_shell_top,
    )
    title_band_expansion_policy = str(layout_metrics["title_band_expansion_policy"])

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
        slot_layout = next(
            (item for item in layout_metrics["gallery_item_layouts"] if item["slot_id"] == slot_id),
            None,
        )
        if slot_rendered:
            reason_code = None
            state = "rendered"
        elif index >= normalized_gallery_count:
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
                "distribution_policy": gallery_distribution_policy,
                "bounds": (
                    {
                        "x": int(slot_layout["x"]),
                        "y": int(slot_layout["y"]),
                        "w": int(slot_layout["w"]),
                        "h": int(slot_layout["h"]),
                    }
                    if slot_layout is not None
                    else None
                ),
                "local_bounds": (
                    {
                        "x": int(slot_layout["local_x"]),
                        "y": int(slot_layout["local_y"]),
                        "w": int(slot_layout["w"]),
                        "h": int(slot_layout["h"]),
                    }
                    if slot_layout is not None
                    else None
                ),
            }
        )
        if not slot_rendered:
            collapsed_optional_slots.append(slot_id)

    return ResolvedBottomBehavior(
        mode=bottom_mode,
        requested_mode=requested_bottom_mode,
        effective_mode=bottom_mode,
        mode_override_reason=mode_override_reason,
        bottom_layout_mode=resolved_bottom_layout_mode,
        bottom_shell_top=actual_bottom_shell_top,
        gallery_mode=gallery_mode,
        requested_gallery_count=requested_gallery_count,
        normalized_gallery_count=normalized_gallery_count,
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
        title_band_sizing_mode=title_band_sizing_mode,
        title_band_growth_policy=title_band_growth_policy,
        subtitle_overflow_policy=subtitle_overflow_policy,
        title_text_budget_policy=title_text_budget_policy,
        subtitle_text_budget_policy=subtitle_text_budget_policy,
        content_priority_policy=content_priority_policy,
        peer_balance_policy=peer_balance_policy,
        bottom_peer_balance_policy=bottom_peer_balance_policy,
        gallery_distribution_policy=gallery_distribution_policy,
        gallery_shell_frame_policy=gallery_shell_frame_policy,
        gallery_strip_shift_policy=gallery_strip_shift_policy,
        gallery_aspect_policy=gallery_aspect_policy,
        gallery_spacing_policy=gallery_spacing_policy,
        bottom_text_emphasis_policy=bottom_text_emphasis_policy,
        title_band_expansion_policy=title_band_expansion_policy,
        title_line_clamp=title_line_clamp,
        subtitle_line_clamp=subtitle_line_clamp,
        title_char_budget=title_char_budget,
        subtitle_char_budget=subtitle_char_budget,
        layout_metrics=layout_metrics,
        bottom_region_state=bottom_region_state,
        collapsed_optional_slots=tuple(collapsed_optional_slots),
        subtitle_slot_state=subtitle_slot_state,
        gallery_slot_states=tuple(gallery_slot_states),
        css_classes=(
            _css_mode_class("bottom-mode", bottom_mode),
            _css_mode_class("bottom-layout-mode", resolved_bottom_layout_mode),
            _css_mode_class("gallery-mode", gallery_mode),
            _css_mode_class("title-band-size", title_band_sizing_mode),
            _css_mode_class("subtitle-overflow", subtitle_overflow_policy),
            _css_mode_class("bottom-peer-balance", peer_balance_policy),
            _css_mode_class("gallery-distribution", gallery_distribution_policy),
        ),
    )


def _resolve_bottom_layout_policies(
    *,
    bottom_mode: str,
    gallery_mode: str,
    title_slot_rendered: bool,
    subtitle_slot_rendered: bool,
    gallery_strip_rendered: bool,
    title_length: int,
    subtitle_length: int,
    visible_item_count: int,
    bottom_shell_top: int = 728,
) -> tuple[str, str, str, str, str, str, str, str, str, str, str, str, int, int, int, int, dict[str, object]]:
    # bottom_shell_top is injected from the caller; expanded modes override frozen baseline (y=728).
    # title_gallery_split and text_gallery_expanded share identical layout policies.
    if bottom_mode == "title_gallery_split":
        bottom_mode = "text_gallery_expanded"
    title_band_top = bottom_shell_top
    title_content_pad_left = 40
    title_content_pad_right = 40

    if not title_slot_rendered:
        title_band_sizing_mode = "collapsed"
        title_band_growth_policy = "title_band_collapsed_without_title"
        subtitle_overflow_policy = "suppressed_with_title_band"
        title_text_budget_policy = "no_title_band_budget"
        subtitle_text_budget_policy = "no_subtitle_budget"
        content_priority_policy = "gallery_priority_without_title_band"
        peer_balance_policy = "gallery_strip_only"
        bottom_peer_balance_policy = "gallery_only_bottom_rebalance"
        bottom_text_emphasis_policy = "gallery_only_neutral_text"
        title_line_clamp = 0
        subtitle_line_clamp = 0
        title_char_budget = 0
        subtitle_char_budget = 0
        title_band_height = 0
        title_content_top = title_band_top
        title_content_height = 0
        title_content_pad_top = 0
        title_content_pad_bottom = 0
        title_stack_gap = 0
    elif bottom_mode == "text_only_expanded":
        # PR-6B: shell starts at y=640. No gallery.
        # PR-6C: title band is content-proportionate (160–220px).
        # PR-6D: shell height = title_band_height (no dead canvas below active text band).
        # Text is centered within the title band with proportionate padding.
        content_priority_policy = "expanded_text_only_full_copy_priority"
        peer_balance_policy = "expanded_title_band_only"
        bottom_peer_balance_policy = "expanded_text_only_rebalance"
        bottom_text_emphasis_policy = "expanded_text_strong_emphasis"
        if subtitle_slot_rendered and subtitle_length > 48:
            title_band_sizing_mode = "expanded"
            title_band_growth_policy = "grow_for_expanded_text_only_dense_copy"
            subtitle_overflow_policy = "three_line_clamp_inside_expanded_title_band"
            title_text_budget_policy = "three_line_title_budget_expanded_text_only"
            subtitle_text_budget_policy = "three_line_support_copy_budget_expanded"
            title_line_clamp = 3
            subtitle_line_clamp = 3
            title_char_budget = 72
            subtitle_char_budget = 80
            title_band_height = 220  # PR-6D: shell height = title_band_height (3+3 lines)
            title_content_pad_top = 28
            title_content_pad_bottom = 28
            title_stack_gap = 10
        elif subtitle_slot_rendered and subtitle_length > 28:
            title_band_sizing_mode = "expanded"
            title_band_growth_policy = "grow_for_expanded_text_only_moderate_copy"
            subtitle_overflow_policy = "two_line_clamp_inside_expanded_title_band"
            title_text_budget_policy = "two_line_title_budget_expanded_text_only"
            subtitle_text_budget_policy = "two_line_support_copy_budget_expanded"
            title_line_clamp = 2
            subtitle_line_clamp = 2
            title_char_budget = 64
            subtitle_char_budget = 64
            title_band_height = 196  # PR-6D: shell height = title_band_height (2+2 lines)
            title_content_pad_top = 30
            title_content_pad_bottom = 30
            title_stack_gap = 10
        elif subtitle_slot_rendered:
            title_band_sizing_mode = "standard"
            title_band_growth_policy = "standard_expanded_text_only_with_subtitle"
            subtitle_overflow_policy = "single_line_ellipsis_inside_expanded_title_band"
            title_text_budget_policy = "two_line_title_budget_with_subtitle_expanded"
            subtitle_text_budget_policy = "single_line_support_copy_budget_expanded"
            title_line_clamp = 2
            subtitle_line_clamp = 1
            title_char_budget = 56
            subtitle_char_budget = 44
            title_band_height = 176  # PR-6D: shell height = title_band_height (2+1 lines)
            title_content_pad_top = 32
            title_content_pad_bottom = 32
            title_stack_gap = 10
        else:
            title_band_sizing_mode = "compact"
            title_band_growth_policy = "compact_expanded_text_only_without_subtitle"
            subtitle_overflow_policy = "subtitle_collapsed"
            title_text_budget_policy = "title_priority_budget_expanded_text_only"
            subtitle_text_budget_policy = "subtitle_collapsed_budget"
            title_line_clamp = 2
            subtitle_line_clamp = 0
            title_char_budget = 52
            subtitle_char_budget = 0
            title_band_height = 160  # PR-6D: shell height = title_band_height (2 lines title only, compact)
            title_content_pad_top = 40
            title_content_pad_bottom = 40
            title_stack_gap = 0
        title_content_top = title_band_top
        title_content_height = title_band_height
    elif bottom_mode == "text_gallery_expanded":
        # Structural expansion: shell starts at y=640 (384px capacity). Has gallery.
        # Materially larger title+subtitle capacity than frozen baseline while keeping gallery strip.
        dense_copy = subtitle_length > 28 or title_length > 20
        if subtitle_slot_rendered and dense_copy and visible_item_count <= 2:
            title_band_sizing_mode = "expanded"
            title_band_growth_policy = "grow_title_band_expanded_text_gallery_light_gallery"
            subtitle_overflow_policy = "two_line_clamp_inside_expanded_split_title_band"
            title_text_budget_policy = "expanded_title_budget_light_gallery_peer"
            subtitle_text_budget_policy = "two_line_support_copy_budget_expanded"
            content_priority_policy = "expanded_text_priority_with_light_gallery"
            peer_balance_policy = "expanded_title_growth_with_light_gallery"
            bottom_peer_balance_policy = "expanded_copy_priority_spacious_gallery"
            bottom_text_emphasis_policy = "expanded_copy_priority_strong_title"
            title_line_clamp = 2
            subtitle_line_clamp = 2
            title_char_budget = 72
            subtitle_char_budget = 60
            title_band_height = 192
            title_content_pad_top = 18
            title_content_pad_bottom = 14
            title_stack_gap = 8
        elif subtitle_slot_rendered and dense_copy and visible_item_count == 3:
            title_band_sizing_mode = "standard"
            title_band_growth_policy = "temper_growth_expanded_text_gallery_triplet"
            subtitle_overflow_policy = "two_line_clamp_inside_expanded_split_title_band"
            title_text_budget_policy = "expanded_title_budget_triplet_gallery_peer"
            subtitle_text_budget_policy = "two_line_support_copy_budget_expanded"
            content_priority_policy = "expanded_balanced_text_and_gallery_priority"
            peer_balance_policy = "expanded_dense_copy_with_triplet_gallery"
            bottom_peer_balance_policy = "expanded_triplet_gallery_and_copy_co_balance"
            bottom_text_emphasis_policy = "expanded_balanced_triplet_text_emphasis"
            title_line_clamp = 2
            subtitle_line_clamp = 2
            title_char_budget = 60
            subtitle_char_budget = 56
            title_band_height = 176
            title_content_pad_top = 20
            title_content_pad_bottom = 16
            title_stack_gap = 8
        elif subtitle_slot_rendered and dense_copy and visible_item_count >= 4:
            # Dense quad in expanded mode: 2-line title + 1-line subtitle minimum
            title_band_sizing_mode = "standard"
            title_band_growth_policy = "hold_growth_expanded_text_gallery_quad"
            subtitle_overflow_policy = "single_line_ellipsis_inside_expanded_split_title_band"
            title_text_budget_policy = "expanded_title_budget_quad_gallery_peer"
            subtitle_text_budget_policy = "single_line_support_copy_budget_expanded"
            content_priority_policy = "expanded_gallery_count_priority_with_text_preserved"
            peer_balance_policy = "expanded_gallery_preserved_with_full_title"
            bottom_peer_balance_policy = "expanded_quad_gallery_with_full_title"
            bottom_text_emphasis_policy = "expanded_quad_text_emphasis"
            title_line_clamp = 2
            subtitle_line_clamp = 1
            title_char_budget = 52
            subtitle_char_budget = 48
            title_band_height = 168
            title_content_pad_top = 22
            title_content_pad_bottom = 18
            title_stack_gap = 6
        elif subtitle_slot_rendered:
            title_band_sizing_mode = "standard"
            title_band_growth_policy = "hold_standard_expanded_text_gallery_with_subtitle"
            subtitle_overflow_policy = "single_line_ellipsis_inside_expanded_split_title_band"
            title_text_budget_policy = "expanded_two_line_title_budget_with_gallery_peer"
            subtitle_text_budget_policy = "single_line_support_copy_budget_expanded"
            content_priority_policy = "expanded_balanced_text_and_gallery_priority"
            peer_balance_policy = "expanded_balanced_title_band_and_gallery_strip"
            bottom_peer_balance_policy = "expanded_balanced_bottom_regions"
            bottom_text_emphasis_policy = "expanded_balanced_bottom_text_emphasis"
            title_line_clamp = 2
            subtitle_line_clamp = 1
            title_char_budget = 60
            subtitle_char_budget = 40
            title_band_height = 168
            title_content_pad_top = 24
            title_content_pad_bottom = 20
            title_stack_gap = 8
        elif title_length > 20:
            title_band_sizing_mode = "standard"
            title_band_growth_policy = "hold_standard_expanded_text_gallery_long_title"
            subtitle_overflow_policy = "subtitle_collapsed"
            title_text_budget_policy = "expanded_two_line_title_budget_with_gallery_peer"
            subtitle_text_budget_policy = "subtitle_collapsed_budget"
            content_priority_policy = "expanded_title_priority_with_gallery_support"
            peer_balance_policy = "expanded_balanced_title_band_and_gallery_strip"
            bottom_peer_balance_policy = "expanded_title_priority_gallery_support"
            bottom_text_emphasis_policy = "expanded_title_priority_text_emphasis"
            title_line_clamp = 2
            subtitle_line_clamp = 0
            title_char_budget = 60
            subtitle_char_budget = 0
            title_band_height = 160
            title_content_pad_top = 26
            title_content_pad_bottom = 22
            title_stack_gap = 0
        else:
            title_band_sizing_mode = "compact"
            title_band_growth_policy = "keep_compact_expanded_text_gallery_light_copy"
            subtitle_overflow_policy = "subtitle_collapsed"
            title_text_budget_policy = "expanded_title_priority_budget_light_copy"
            subtitle_text_budget_policy = "subtitle_collapsed_budget"
            content_priority_policy = "expanded_gallery_support_with_compact_title"
            peer_balance_policy = "expanded_title_compact_with_light_gallery"
            bottom_peer_balance_policy = "expanded_compact_title_with_gallery_support"
            bottom_text_emphasis_policy = "expanded_compact_light_text_emphasis"
            title_line_clamp = 2
            subtitle_line_clamp = 0
            title_char_budget = 52
            subtitle_char_budget = 0
            title_band_height = 148
            title_content_pad_top = 28
            title_content_pad_bottom = 24
            title_stack_gap = 0
        title_content_top = title_band_top
        title_content_height = title_band_height
    else:
        dense_copy = subtitle_length > 36 or title_length > 24
        if subtitle_slot_rendered and dense_copy and visible_item_count <= 2:
            title_band_sizing_mode = "expanded"
            title_band_growth_policy = "grow_title_band_for_support_copy_priority"
            subtitle_overflow_policy = "two_line_clamp_inside_split_title_band"
            title_text_budget_policy = "balanced_title_budget_under_dense_bottom_split"
            subtitle_text_budget_policy = "two_line_support_copy_budget"
            content_priority_policy = "title_and_subtitle_priority_over_gallery_density"
            peer_balance_policy = "title_growth_allowed_with_light_gallery"
            bottom_peer_balance_policy = "copy_priority_with_spacious_gallery"
            bottom_text_emphasis_policy = "copy_priority_strong_title"
            title_line_clamp = 1 if subtitle_length > 58 and title_length > 20 else 2
            subtitle_line_clamp = 2
            title_char_budget = 36 if title_line_clamp == 1 else 42
            subtitle_char_budget = 48
            title_band_height = 160
            title_content_pad_top = 16
            title_content_pad_bottom = 10
            title_stack_gap = 6
        elif subtitle_slot_rendered and dense_copy and visible_item_count == 3:
            title_band_sizing_mode = "standard"
            title_band_growth_policy = "temper_growth_for_triplet_gallery_balance"
            subtitle_overflow_policy = "two_line_clamp_inside_split_title_band"
            title_text_budget_policy = "balanced_title_budget_with_triplet_gallery_peer"
            subtitle_text_budget_policy = "two_line_support_copy_budget"
            content_priority_policy = "balanced_text_and_gallery_priority"
            peer_balance_policy = "balanced_dense_copy_with_triplet_gallery"
            bottom_peer_balance_policy = "triplet_gallery_and_copy_co_balance"
            bottom_text_emphasis_policy = "balanced_triplet_text_emphasis"
            title_line_clamp = 2
            subtitle_line_clamp = 2
            title_char_budget = 38
            subtitle_char_budget = 44
            title_band_height = 152
            title_content_pad_top = 18
            title_content_pad_bottom = 12
            title_stack_gap = 6
        elif subtitle_slot_rendered and dense_copy and visible_item_count >= 4:
            title_band_sizing_mode = "standard"
            title_band_growth_policy = "hold_growth_under_dense_quad_pressure"
            subtitle_overflow_policy = "single_line_ellipsis_inside_split_title_band"
            title_text_budget_policy = "gallery_priority_title_budget_under_dense_quad"
            subtitle_text_budget_policy = "single_line_support_copy_budget"
            content_priority_policy = "gallery_count_priority_with_text_compaction"
            peer_balance_policy = "gallery_priority_under_dense_quad"
            bottom_peer_balance_policy = "quad_gallery_priority_over_copy_growth"
            bottom_text_emphasis_policy = "compact_quad_text_emphasis"
            title_line_clamp = 1 if subtitle_length > 48 else 2
            subtitle_line_clamp = 1
            title_char_budget = 20 if title_line_clamp == 1 else 36
            subtitle_char_budget = 24
            title_band_height = 144
            title_content_pad_top = 22
            title_content_pad_bottom = 18
            title_stack_gap = 6
        elif subtitle_slot_rendered:
            title_band_sizing_mode = "standard"
            title_band_growth_policy = "hold_standard_title_band_with_balanced_gallery"
            subtitle_overflow_policy = "single_line_ellipsis_inside_split_title_band"
            title_text_budget_policy = "two_line_title_budget_with_balanced_gallery_peer"
            subtitle_text_budget_policy = "single_line_support_copy_budget"
            content_priority_policy = "balanced_text_and_gallery_priority"
            peer_balance_policy = "balanced_title_band_and_gallery_strip"
            bottom_peer_balance_policy = "balanced_bottom_regions"
            bottom_text_emphasis_policy = "balanced_bottom_text_emphasis"
            title_line_clamp = 2
            subtitle_line_clamp = 1
            title_char_budget = 40
            subtitle_char_budget = 28
            title_band_height = 144
            title_content_pad_top = 22
            title_content_pad_bottom = 18
            title_stack_gap = 8
        elif title_length > 28:
            title_band_sizing_mode = "standard"
            title_band_growth_policy = "hold_standard_title_band_for_long_title"
            subtitle_overflow_policy = "subtitle_collapsed"
            title_text_budget_policy = "two_line_title_budget_with_gallery_peer"
            subtitle_text_budget_policy = "subtitle_collapsed_budget"
            content_priority_policy = "title_priority_with_gallery_support"
            peer_balance_policy = "balanced_title_band_and_gallery_strip"
            bottom_peer_balance_policy = "title_priority_with_gallery_support"
            bottom_text_emphasis_policy = "title_priority_text_emphasis"
            title_line_clamp = 2
            subtitle_line_clamp = 0
            title_char_budget = 38
            subtitle_char_budget = 0
            title_band_height = 144
            title_content_pad_top = 24
            title_content_pad_bottom = 18
            title_stack_gap = 0
        else:
            title_band_sizing_mode = "compact"
            title_band_growth_policy = "keep_compact_title_band_for_light_copy"
            subtitle_overflow_policy = "subtitle_collapsed"
            title_text_budget_policy = "title_priority_budget_with_light_copy"
            subtitle_text_budget_policy = "subtitle_collapsed_budget"
            content_priority_policy = "gallery_support_with_compact_title"
            peer_balance_policy = "title_compact_with_light_gallery"
            bottom_peer_balance_policy = "compact_title_with_gallery_support"
            bottom_text_emphasis_policy = "compact_light_text_emphasis"
            title_line_clamp = 2
            subtitle_line_clamp = 0
            title_char_budget = 34
            subtitle_char_budget = 0
            title_band_height = 128
            title_content_pad_top = 26
            title_content_pad_bottom = 20
            title_stack_gap = 0
        title_content_top = title_band_top
        title_content_height = title_band_height

    peer_gap = _resolve_bottom_peer_gap(
        bottom_mode=bottom_mode,
        visible_item_count=visible_item_count if gallery_strip_rendered else 0,
        title_band_sizing_mode=title_band_sizing_mode,
        peer_balance_policy=peer_balance_policy,
    )
    # When gallery strip renders without a title band (gallery_only mode), position the
    # gallery shell at the bottom shell top so items render inside the shell region.
    # The old hardcoded 888 was a legacy placeholder that placed items outside the shell.
    gallery_shell_top = (
        title_band_top + title_band_height + peer_gap
        if gallery_strip_rendered and title_slot_rendered
        else (title_band_top if gallery_strip_rendered else title_band_top + title_band_height)
    )
    (
        gallery_strip_shift_policy,
        gallery_shell_height,
        gallery_items_top,
        gallery_items_height,
    ) = _resolve_gallery_strip_vertical_metrics(
        gallery_mode=gallery_mode,
        visible_item_count=visible_item_count if gallery_strip_rendered else 0,
        peer_balance_policy=peer_balance_policy,
        gallery_shell_top=gallery_shell_top,
    )
    (
        gallery_distribution_policy,
        gallery_shell_frame_policy,
        gallery_aspect_policy,
        gallery_spacing_policy,
        gallery_item_layouts,
    ) = _resolve_gallery_distribution_layout(
        gallery_mode=gallery_mode,
        visible_item_count=visible_item_count if gallery_strip_rendered else 0,
        gallery_items_top=gallery_items_top,
        gallery_items_height=gallery_items_height,
        gallery_shell_height=gallery_shell_height,
    )
    bottom_shell_height = _resolve_bottom_shell_height(
        bottom_mode=bottom_mode,
        bottom_shell_top=bottom_shell_top,
        title_slot_rendered=title_slot_rendered,
        gallery_strip_rendered=gallery_strip_rendered,
        title_band_top=title_band_top,
        title_band_height=title_band_height,
        gallery_shell_top=gallery_shell_top,
        gallery_shell_height=gallery_shell_height,
    )
    gallery_shell_x, gallery_shell_w, gallery_shell_radius, gallery_item_radius = _resolve_gallery_shell_frame_metrics(
        visible_item_count=visible_item_count if gallery_strip_rendered else 0,
        gallery_distribution_policy=gallery_distribution_policy,
        gallery_items=gallery_item_layouts,
    )
    title_slot_y, title_slot_h, subtitle_slot_y, subtitle_slot_h = _resolve_bottom_text_slot_metrics(
        bottom_mode=bottom_mode,
        title_band_sizing_mode=title_band_sizing_mode,
        title_content_top=title_content_top,
        title_content_height=title_content_height,
        title_content_pad_top=title_content_pad_top,
        title_content_pad_bottom=title_content_pad_bottom,
        title_stack_gap=title_stack_gap,
        title_line_clamp=title_line_clamp,
        subtitle_line_clamp=subtitle_line_clamp,
        subtitle_slot_rendered=subtitle_slot_rendered,
    )

    # PR-6: Title band horizontal expansion.
    # When gallery strip is absent, expand the title band (and subtitle text slot)
    # to fill the full bottom shell width (x=96, w=832), matching gallery_slot geometry.
    # Standard (gallery present): x=112, w=800, matching title_slot template spec.
    # Subtitle inset from title band edge: 40px on each side (matches frozen subtitle_slot spec).
    _BOTTOM_SHELL_X = 96
    _BOTTOM_SHELL_W = 832
    _TITLE_BAND_DEFAULT_X = 112
    _TITLE_BAND_DEFAULT_W = 800
    _SUBTITLE_INSET = 40
    if title_slot_rendered and not gallery_strip_rendered:
        title_band_x = _BOTTOM_SHELL_X
        title_band_w = _BOTTOM_SHELL_W
        title_band_expansion_policy = "full_width_title_band_no_gallery"
    else:
        title_band_x = _TITLE_BAND_DEFAULT_X
        title_band_w = _TITLE_BAND_DEFAULT_W
        title_band_expansion_policy = (
            "standard_title_band_with_gallery"
            if gallery_strip_rendered
            else "no_title_band_rendered"
        )
    subtitle_slot_x = title_band_x + _SUBTITLE_INSET
    subtitle_slot_w = title_band_w - 2 * _SUBTITLE_INSET

    return (
        title_band_sizing_mode,
        title_band_growth_policy,
        subtitle_overflow_policy,
        title_text_budget_policy,
        subtitle_text_budget_policy,
        content_priority_policy,
        peer_balance_policy,
        bottom_peer_balance_policy,
        gallery_distribution_policy,
        gallery_shell_frame_policy,
        gallery_strip_shift_policy,
        gallery_aspect_policy,
        gallery_spacing_policy,
        bottom_text_emphasis_policy,
        title_line_clamp,
        subtitle_line_clamp,
        title_char_budget,
        subtitle_char_budget,
        {
            "bottom_shell_top": bottom_shell_top,
            "bottom_shell_height": bottom_shell_height,
            "title_band_top": title_band_top,
            "title_band_height": title_band_height,
            "title_content_top": title_content_top,
            "title_content_height": title_content_height,
            "title_content_pad_top": title_content_pad_top,
            "title_content_pad_right": title_content_pad_right,
            "title_content_pad_bottom": title_content_pad_bottom,
            "title_content_pad_left": title_content_pad_left,
            "title_stack_gap": title_stack_gap,
            "gallery_shell_top": gallery_shell_top,
            "gallery_shell_height": gallery_shell_height,
            "gallery_shell_x": gallery_shell_x,
            "gallery_shell_w": gallery_shell_w,
            "gallery_shell_radius": gallery_shell_radius,
            "gallery_items_top": gallery_items_top,
            "gallery_items_height": gallery_items_height,
            "gallery_item_radius": gallery_item_radius,
            "gallery_item_layouts": gallery_item_layouts,
            "peer_gap": peer_gap,
            "title_slot_y": title_slot_y,
            "title_slot_height": title_slot_h,
            "subtitle_slot_y": subtitle_slot_y,
            "subtitle_slot_height": subtitle_slot_h,
            "title_band_x": title_band_x,
            "title_band_w": title_band_w,
            "subtitle_slot_x": subtitle_slot_x,
            "subtitle_slot_w": subtitle_slot_w,
            "title_band_expansion_policy": title_band_expansion_policy,
        },
    )


def _resolve_bottom_text_slot_metrics(
    *,
    bottom_mode: str,
    title_band_sizing_mode: str,
    title_content_top: int,
    title_content_height: int,
    title_content_pad_top: int,
    title_content_pad_bottom: int,
    title_stack_gap: int,
    title_line_clamp: int,
    subtitle_line_clamp: int,
    subtitle_slot_rendered: bool,
) -> tuple[int, int, int, int]:
    available_top = title_content_top + title_content_pad_top
    available_height = max(title_content_height - title_content_pad_top - title_content_pad_bottom, 0)
    title_slot_height = 54 if title_line_clamp <= 1 else (72 if subtitle_slot_rendered else 80)
    subtitle_slot_height = 0 if not subtitle_slot_rendered else (28 if subtitle_line_clamp <= 1 else 44)
    stack_gap = title_stack_gap if subtitle_slot_rendered else 0
    used_height = title_slot_height + subtitle_slot_height + stack_gap
    if used_height > available_height and subtitle_slot_rendered:
        overflow = used_height - available_height
        title_slot_height = max(title_slot_height - min(overflow, 8), 48 if title_line_clamp <= 1 else 64)
        used_height = title_slot_height + subtitle_slot_height + stack_gap
    if used_height > available_height and subtitle_slot_rendered:
        overflow = used_height - available_height
        subtitle_slot_height = max(subtitle_slot_height - overflow, 24 if subtitle_line_clamp <= 1 else 40)
        used_height = title_slot_height + subtitle_slot_height + stack_gap
    offset = max((available_height - used_height) // 2, 0)
    title_slot_y = available_top + offset
    subtitle_slot_y = title_slot_y + title_slot_height + stack_gap if subtitle_slot_rendered else title_slot_y + title_slot_height
    return title_slot_y, title_slot_height, subtitle_slot_y, subtitle_slot_height


def _resolve_gallery_distribution_layout(
    *,
    gallery_mode: str,
    visible_item_count: int,
    gallery_items_top: int,
    gallery_items_height: int,
    gallery_shell_height: int,
) -> tuple[str, str, str, str, list[dict[str, int | str]]]:
    if visible_item_count <= 0:
        return "gallery_collapsed", "gallery_collapsed", "gallery_collapsed", "gallery_collapsed", []

    layout_table: dict[str, dict[int, tuple[str, str, str, int, int]]] = {
        "strip_local_visible_only": {
            1: ("single_center_focus", "single_showcase_frame", "single_gallery_focus_aspect", "centered_single_spacing", 288, 0),
            2: ("balanced_pair", "pair_showcase_frame", "spacious_pair_aspect", "relaxed_pair_spacing", 280, 16),
            3: ("balanced_triplet", "triplet_balanced_frame", "balanced_triplet_aspect", "balanced_triplet_spacing", 220, 12),
            4: ("dense_quad", "quad_strip_frame", "compact_quad_aspect", "compact_quad_spacing", 196, 16),
        },
        "supporting_packshots": {
            1: ("single_packshot_focus", "single_showcase_frame", "single_packshot_aspect", "centered_single_spacing", 240, 0),
            2: ("supporting_pair", "pair_showcase_frame", "supporting_pair_aspect", "supporting_pair_spacing", 220, 18),
            3: ("supporting_triplet", "triplet_balanced_frame", "supporting_triplet_aspect", "supporting_triplet_spacing", 196, 12),
            4: ("dense_quad", "quad_strip_frame", "compact_quad_aspect", "compact_quad_spacing", 196, 16),
        },
    }
    mode_table = layout_table.get(gallery_mode, layout_table["strip_local_visible_only"])
    distribution_policy, gallery_shell_frame_policy, gallery_aspect_policy, gallery_spacing_policy, item_width, gap = mode_table[
        min(max(visible_item_count, 1), 4)
    ]
    strip_width = 832
    strip_left = 96
    used_width = item_width * visible_item_count + gap * max(visible_item_count - 1, 0)
    local_start_x = max((strip_width - used_width) // 2, 0)
    local_y = max((gallery_shell_height - gallery_items_height) // 2, 0)
    layouts: list[dict[str, int | str]] = []
    for index in range(visible_item_count):
        local_x = local_start_x + index * (item_width + gap)
        x = strip_left + local_x
        layouts.append(
            {
                "slot_id": f"gallery_item_slot_{index + 1}",
                "index": index,
                "x": x,
                "y": gallery_items_top,
                "w": item_width,
                "h": gallery_items_height,
                "local_x": local_x,
                "local_y": local_y,
            }
        )
    return distribution_policy, gallery_shell_frame_policy, gallery_aspect_policy, gallery_spacing_policy, layouts


def _resolve_bottom_peer_gap(
    *,
    bottom_mode: str,
    visible_item_count: int,
    title_band_sizing_mode: str,
    peer_balance_policy: str,
) -> int:
    if bottom_mode != "title_gallery_split" or visible_item_count <= 0:
        return 0
    if peer_balance_policy == "gallery_priority_under_dense_quad":
        return 10
    if peer_balance_policy == "balanced_dense_copy_with_triplet_gallery":
        return 12
    if peer_balance_policy == "title_growth_allowed_with_light_gallery":
        return 14
    if title_band_sizing_mode == "compact":
        return 18
    return 16


def _resolve_gallery_strip_vertical_metrics(
    *,
    gallery_mode: str,
    visible_item_count: int,
    peer_balance_policy: str,
    gallery_shell_top: int,
) -> tuple[int, int, int]:
    if visible_item_count <= 0:
        return "gallery_collapsed", 0, gallery_shell_top, 0
    vertical_table: dict[str, dict[int, tuple[str, int, int]]] = {
        "strip_local_visible_only": {
            1: ("single_gallery_centered_shift", 88, 68),
            2: ("downshift_for_spacious_pair", 100, 80),
            3: ("balanced_triplet_shift", 80, 60),
            4: ("tight_quad_shift", 68, 52),
        },
        "supporting_packshots": {
            1: ("single_gallery_centered_shift", 84, 64),
            2: ("downshift_for_supporting_pair", 76, 58),
            3: ("balanced_triplet_shift", 72, 54),
            4: ("tight_quad_shift", 68, 52),
        },
    }
    shift_policy, shell_height, item_height = vertical_table.get(gallery_mode, vertical_table["strip_local_visible_only"])[
        min(max(visible_item_count, 1), 4)
    ]
    if peer_balance_policy == "gallery_priority_under_dense_quad":
        shell_height = max(shell_height - 4, item_height + 12)
    inner_pad_y = max((shell_height - item_height) // 2, 0)
    return shift_policy, shell_height, gallery_shell_top + inner_pad_y, item_height


def _resolve_gallery_shell_frame_metrics(
    *,
    visible_item_count: int,
    gallery_distribution_policy: str,
    gallery_items: list[dict[str, int | str]],
) -> tuple[int, int, int, int]:
    if visible_item_count <= 0 or not gallery_items:
        return 96, 832, 20, 14
    frame_by_policy: dict[str, tuple[int, int]] = {
        "single_center_focus": (18, 24),
        "single_packshot_focus": (16, 24),
        "balanced_pair": (16, 24),
        "supporting_pair": (14, 22),
        "balanced_triplet": (14, 22),
        "supporting_triplet": (12, 20),
        "dense_quad": (0, 20),
    }
    item_radius_by_policy: dict[str, int] = {
        "single_center_focus": 18,
        "single_packshot_focus": 18,
        "balanced_pair": 18,
        "supporting_pair": 16,
        "balanced_triplet": 16,
        "supporting_triplet": 16,
        "dense_quad": 14,
    }
    frame_pad_x, shell_radius = frame_by_policy.get(gallery_distribution_policy, (0, 20))
    first = gallery_items[0]
    last = gallery_items[-1]
    left = max(int(first["x"]) - frame_pad_x, 96)
    right = min(int(last["x"]) + int(last["w"]) + frame_pad_x, 928)
    width = max(right - left, 0)
    return left, width, shell_radius, item_radius_by_policy.get(gallery_distribution_policy, 14)


def _resolve_bottom_shell_height(
    *,
    bottom_mode: str,
    bottom_shell_top: int,
    title_slot_rendered: bool,
    gallery_strip_rendered: bool,
    title_band_top: int,
    title_band_height: int,
    gallery_shell_top: int,
    gallery_shell_height: int,
) -> int:
    if bottom_mode == "gallery_only":
        return gallery_shell_height
    if bottom_mode == "text_only_expanded":
        # PR-6D: shell height matches title_band_height (content-proportionate, 160–220px).
        # No dead canvas below the active text band. Shell top stays at 640.
        return title_band_height
    bottom_edges: list[int] = []
    if title_slot_rendered:
        bottom_edges.append(title_band_top + title_band_height)
    if gallery_strip_rendered:
        bottom_edges.append(gallery_shell_top + gallery_shell_height)
    if not bottom_edges:
        return 0
    return max(bottom_edges) - bottom_shell_top


def _resolve_bottom_behavior_vars(policy: ResolvedBottomBehavior) -> dict[str, str]:
    layout = policy.layout_metrics
    subtitle_line_clamp = max(policy.subtitle_line_clamp, 1)
    title_line_clamp = max(policy.title_line_clamp, 1)
    return {
        "--bottom-shell-top": f"{int(layout['bottom_shell_top'])}px",
        "--bottom-shell-height": f"{int(layout['bottom_shell_height'])}px",
        "--title-band-top": f"{int(layout['title_band_top'])}px",
        "--title-band-height": f"{int(layout['title_band_height'])}px",
        "--title-content-top": f"{int(layout['title_content_top'])}px",
        "--title-content-height": f"{int(layout['title_content_height'])}px",
        "--title-content-pad-top": f"{int(layout['title_content_pad_top'])}px",
        "--title-content-pad-right": f"{int(layout['title_content_pad_right'])}px",
        "--title-content-pad-bottom": f"{int(layout['title_content_pad_bottom'])}px",
        "--title-content-pad-left": f"{int(layout['title_content_pad_left'])}px",
        "--title-stack-gap": f"{int(layout['title_stack_gap'])}px",
        "--gallery-shell-top": f"{int(layout['gallery_shell_top'])}px",
        "--gallery-shell-height": f"{int(layout['gallery_shell_height'])}px",
        "--gallery-shell-left": f"{int(layout['gallery_shell_x'])}px",
        "--gallery-shell-width": f"{int(layout['gallery_shell_w'])}px",
        "--gallery-shell-radius": f"{int(layout['gallery_shell_radius'])}px",
        "--gallery-items-top": f"{int(layout['gallery_items_top'])}px",
        "--gallery-items-height": f"{int(layout['gallery_items_height'])}px",
        "--gallery-item-radius": f"{int(layout['gallery_item_radius'])}px",
        "--bottom-title-letter-spacing": _resolve_bottom_title_letter_spacing(policy.bottom_text_emphasis_policy),
        "--bottom-subtitle-opacity": _resolve_bottom_subtitle_opacity(policy.bottom_text_emphasis_policy),
        "--title-line-clamp": str(title_line_clamp),
        "--subtitle-line-clamp": str(subtitle_line_clamp),
        "--title-band-left": f"{int(layout['title_band_x'])}px",
        "--title-band-width": f"{int(layout['title_band_w'])}px",
    }


def _resolve_bottom_title_letter_spacing(policy: str) -> str:
    table = {
        "copy_priority_strong_title": "0.01em",
        "balanced_triplet_text_emphasis": "0.008em",
        "compact_quad_text_emphasis": "0em",
        "balanced_bottom_text_emphasis": "0.006em",
        "title_only_strong_emphasis": "0.012em",
        "title_priority_text_emphasis": "0.01em",
        "compact_light_text_emphasis": "0.004em",
        "gallery_only_neutral_text": "0em",
        # Expanded mode text emphasis policies
        "expanded_text_strong_emphasis": "0.014em",
        "expanded_copy_priority_strong_title": "0.012em",
        "expanded_balanced_triplet_text_emphasis": "0.01em",
        "expanded_quad_text_emphasis": "0.008em",
        "expanded_balanced_bottom_text_emphasis": "0.008em",
        "expanded_title_priority_text_emphasis": "0.012em",
        "expanded_compact_light_text_emphasis": "0.006em",
    }
    return table.get(policy, "0.006em")


def _resolve_bottom_subtitle_opacity(policy: str) -> str:
    table = {
        "copy_priority_strong_title": "0.92",
        "balanced_triplet_text_emphasis": "0.94",
        "compact_quad_text_emphasis": "0.86",
        "balanced_bottom_text_emphasis": "0.9",
        "title_only_strong_emphasis": "0.92",
        "title_priority_text_emphasis": "0.9",
        "compact_light_text_emphasis": "0.88",
        "gallery_only_neutral_text": "0.86",
        # Expanded mode text emphasis policies
        "expanded_text_strong_emphasis": "0.94",
        "expanded_copy_priority_strong_title": "0.94",
        "expanded_balanced_triplet_text_emphasis": "0.94",
        "expanded_quad_text_emphasis": "0.92",
        "expanded_balanced_bottom_text_emphasis": "0.92",
        "expanded_title_priority_text_emphasis": "0.92",
        "expanded_compact_light_text_emphasis": "0.9",
    }
    return table.get(policy, "0.9")


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
