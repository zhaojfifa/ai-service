"""
Poster 2.0 — Data Contracts (Single Source of Truth)

Three immutable dataclasses:
  PosterSpec     – caller input
  TemplateSpec   – template structure definition (JSON-driven)
  RenderManifest – auditable output record
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Literal, Optional

from PIL import Image as PILImage

RendererMode = Literal["auto", "pillow", "puppeteer"]


# ---------------------------------------------------------------------------
# PosterSpec — caller input
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AssetRef:
    """Unified asset reference. Accepts https://, r2://key, or data:... URLs."""
    url: str
    key: Optional[str] = None


@dataclass(frozen=True)
class StyleSpec:
    prompt: str = "clean studio background, soft diffused light"
    negative_prompt: str = "text, logo, watermark, UI elements, buttons, people"
    seed: Optional[int] = None
    palette: Optional[tuple[str, ...]] = None  # hex color hints e.g. ("#E8002A",)


@dataclass(frozen=True)
class PosterSpec:
    # --- Text content ---
    brand_name: str
    agent_name: str
    title: str
    subtitle: str
    features: tuple[str, ...]       # 2-4 feature callout labels

    # --- Assets ---
    product_image: AssetRef
    logo: Optional[AssetRef] = None
    scenario_image: Optional[AssetRef] = None
    gallery_images: tuple[AssetRef, ...] = field(default_factory=tuple)

    # --- Style (only for background generation) ---
    style: StyleSpec = field(default_factory=StyleSpec)

    # --- Rendering ---
    template_id: str = "template_dual_v2"
    size: tuple[int, int] = (1024, 1024)
    locale: str = "zh-CN"
    export_format: Literal["png", "jpeg", "webp"] = "png"
    renderer_mode: RendererMode = "auto"


# ---------------------------------------------------------------------------
# TemplateSpec — deterministic layout definition
# ---------------------------------------------------------------------------

@dataclass
class TextSlotSpec:
    x: int
    y: int
    w: int
    h: int
    font_key: str                          # resolved by FontRegistry
    font_size: int
    color: str = "#FFFFFF"
    align: Literal["left", "center", "right"] = "left"
    max_lines: int = 1
    line_height: float = 1.2
    auto_shrink: bool = True
    # Optional CTA pill button: draw filled rounded rect behind text
    bg_color: Optional[str] = None         # e.g. "#E8002A" for red pill button
    bg_radius: int = 0                     # corner radius; 0 = no background


@dataclass
class ImageSlotSpec:
    x: int
    y: int
    w: int
    h: int
    fit: Literal["contain", "cover", "fill"] = "contain"
    bg_color: str = "transparent"
    shadow: bool = False
    radius: int = 0


@dataclass
class GalleryStripSpec:
    x: int
    y: int
    w: int
    h: int
    count: int = 4
    gap: int = 16
    thumb_w: int = 176                     # explicit thumb width avoids rounding
    thumb_radius: int = 4
    show_label: bool = False


@dataclass
class FeatureCalloutSpec:
    """
    One feature callout entry = anchor dot + leader line + text label.

    anchor_radius == 0  →  skip anchor and leader (plain text-only mode).
    """
    # Text content
    label_box: TextSlotSpec

    # Anchor dot on the product edge
    anchor_x: int = 0
    anchor_y: int = 0
    anchor_radius: int = 7              # px; 0 = no dot/line drawn
    anchor_color: str = "#E8002A"

    # Leader line from anchor to label_box
    leader_color: str = "#E8002A"
    leader_width: int = 2


@dataclass
class TemplateSpec:
    template_id: str
    version: str                           # semver; recorded in RenderManifest
    canvas_w: int
    canvas_h: int
    safe_margin: int

    # Fixed structural slots
    logo_slot: ImageSlotSpec
    brand_name_slot: TextSlotSpec
    agent_name_slot: TextSlotSpec          # supports bg_color/bg_radius for CTA pill
    title_slot: TextSlotSpec
    subtitle_slot: TextSlotSpec
    product_slot: ImageSlotSpec
    gallery_slot: GalleryStripSpec

    # Feature callouts: anchor dot + leader line + label text
    feature_callouts: list[FeatureCalloutSpec]
    contract_version: str = "poster2.template.v1"

    # Optional slots
    scenario_slot: Optional[ImageSlotSpec] = None

    # Firefly background hint (never contains text/logo/UI words)
    background_prompt_hint: str = ""

    # ---------- JSON loader ----------

    @classmethod
    def from_json(cls, path: str | Path) -> "TemplateSpec":
        """Load a TemplateSpec from a JSON file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, d: dict) -> "TemplateSpec":
        def text(raw: dict) -> TextSlotSpec:
            # Filter to only known fields to allow forward-compat extra keys
            known = {f.name for f in TextSlotSpec.__dataclass_fields__.values()}  # type: ignore[attr-defined]
            return TextSlotSpec(**{k: v for k, v in raw.items() if k in known})

        def img(raw: dict) -> ImageSlotSpec:
            known = {f.name for f in ImageSlotSpec.__dataclass_fields__.values()}  # type: ignore[attr-defined]
            return ImageSlotSpec(**{k: v for k, v in raw.items() if k in known})

        def gallery(raw: dict) -> GalleryStripSpec:
            known = {f.name for f in GalleryStripSpec.__dataclass_fields__.values()}  # type: ignore[attr-defined]
            return GalleryStripSpec(**{k: v for k, v in raw.items() if k in known})

        def callout(raw: dict) -> FeatureCalloutSpec:
            return FeatureCalloutSpec(
                label_box=text(raw["label_box"]),
                anchor_x=raw.get("anchor_x", 0),
                anchor_y=raw.get("anchor_y", 0),
                anchor_radius=raw.get("anchor_radius", 7),
                anchor_color=raw.get("anchor_color", "#E8002A"),
                leader_color=raw.get("leader_color", "#E8002A"),
                leader_width=raw.get("leader_width", 2),
            )

        # ── feature_callouts (preferred) vs legacy features_slot ──────────
        feature_callouts_raw = d.get("feature_callouts")
        if feature_callouts_raw:
            feature_callouts = [callout(c) for c in feature_callouts_raw]
        else:
            # Legacy: plain text slots → callouts with no anchor/leader
            feature_callouts = [
                FeatureCalloutSpec(label_box=text(f), anchor_radius=0)
                for f in d.get("features_slot", [])
            ]

        scenario_raw = d.get("scenario_slot")
        return cls(
            template_id=d["template_id"],
            version=d["version"],
            contract_version=d.get("contract_version", "poster2.template.v1"),
            canvas_w=d["canvas_w"],
            canvas_h=d["canvas_h"],
            safe_margin=d.get("safe_margin", 48),
            logo_slot=img(d["logo_slot"]),
            brand_name_slot=text(d["brand_name_slot"]),
            agent_name_slot=text(d["agent_name_slot"]),
            title_slot=text(d["title_slot"]),
            subtitle_slot=text(d["subtitle_slot"]),
            feature_callouts=feature_callouts,
            product_slot=img(d["product_slot"]),
            gallery_slot=gallery(d["gallery_slot"]),
            scenario_slot=img(scenario_raw) if scenario_raw else None,
            background_prompt_hint=d.get("background_prompt_hint", ""),
        )


# ---------------------------------------------------------------------------
# ResolvedAssets — PIL Images ready for rendering
# ---------------------------------------------------------------------------

@dataclass
class ResolvedAssets:
    product: PILImage.Image
    logo: Optional[PILImage.Image] = None
    scenario: Optional[PILImage.Image] = None
    gallery: list[PILImage.Image] = field(default_factory=list)


@dataclass
class RenderDebugArtifacts:
    background_layer_url: str = ""
    product_material_layer_url: str = ""
    foreground_layer_url: str = ""
    final_composited_url: str = ""
    renderer_metadata_url: str = ""


# ---------------------------------------------------------------------------
# RenderManifest — auditable output record
# ---------------------------------------------------------------------------

@dataclass
class RenderManifest:
    trace_id: str
    template_id: str
    template_version: str
    template_contract_version: str
    engine_version: str
    renderer_mode: RendererMode
    render_engine_used: str
    foreground_renderer: str
    background_renderer: str

    # Input snapshot (for replay)
    poster_spec_hash: str
    resolved_inputs: dict

    # Layer outputs
    background_url: str
    background_prompt: str
    background_seed: int
    background_model: str

    foreground_url: str
    foreground_hash: str

    final_url: str
    final_hash: str

    # Timing & quality
    timings_ms: dict
    debug_artifacts: RenderDebugArtifacts = field(default_factory=RenderDebugArtifacts)
    fallback_reason_code: Optional[str] = None
    fallback_reason_detail: Optional[str] = None
    degraded: bool = False
    degraded_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
