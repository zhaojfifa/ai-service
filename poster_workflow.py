"""Command-line helper for generating marketing poster assets.

This utility mirrors the three-step web workflow:

1. Validate and preview the poster layout requirements.
2. Generate an image and prompt using the Glibatree helper (with mock fallback).
3. Optionally send the generated poster via email through the configured SMTP server.

The script accepts a JSON configuration describing the poster inputs and, optionally,
email delivery details. Example usage::

    python poster_workflow.py --input examples/sample_workflow.json --output-dir out/
    python poster_workflow.py --input config.json --send-email

Outputs are printed to stdout and, when ``--output-dir`` is provided, written to files
for easier sharing.
"""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

from app.schemas import PosterImage, PosterInput, SendEmailRequest
from app.services.email_sender import send_email
from app.services.glibatree import generate_poster_asset
from app.services.poster import (
    build_glibatree_prompt,
    compose_marketing_email,
    render_layout_preview,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate marketing poster assets")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the JSON file containing poster (and optional email) data",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to write the generated preview, prompt, email and poster image",
    )
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="Send the generated poster via email when email settings are provided",
    )
    return parser.parse_args()


def load_configuration(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


TModel = TypeVar("TModel")


def _model_validate(model: Type[TModel], data: Dict[str, Any]) -> TModel:
    """Support both Pydantic v1 (``parse_obj``) and v2 (``model_validate``)."""
    if hasattr(model, "model_validate"):
        return model.model_validate(data)  # type: ignore[attr-defined]
    return model.parse_obj(data)  # type: ignore[attr-defined]


def _model_dump(instance: Any) -> Dict[str, Any]:
    """Return a plain ``dict`` regardless of the installed Pydantic version."""
    if hasattr(instance, "model_dump"):
        return instance.model_dump()  # type: ignore[attr-defined]
    return instance.dict()  # type: ignore[attr-defined]


def parse_poster_input(config: Dict[str, Any]) -> PosterInput:
    poster_config = config.get("poster", config)
    return _model_validate(PosterInput, poster_config)


def parse_email_payload(
    config: Dict[str, Any],
    poster: PosterInput,
    poster_image: PosterImage,
    default_body: str,
) -> Optional[SendEmailRequest]:
    email_config = config.get("email")
    if not email_config:
        return None

    payload: Dict[str, Any] = {
        "recipient": email_config["recipient"],
        "subject": email_config.get(
            "subject", f"{poster.brand_name} · {poster.product_name} 营销海报"
        ),
        "body": email_config.get("body", default_body),
        "attachment": _model_dump(poster_image),
    }
    return _model_validate(SendEmailRequest, payload)


def export_outputs(
    output_dir: Path,
    preview: str,
    prompt: str,
    email_body: str,
    poster_image: PosterImage,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "layout_preview.txt").write_text(preview, encoding="utf-8")
    (output_dir / "glibatree_prompt.txt").write_text(prompt, encoding="utf-8")
    (output_dir / "email_body.txt").write_text(email_body, encoding="utf-8")

    image_path = output_dir / poster_image.filename
    _header, encoded = poster_image.data_url.split(",", 1)
    binary = base64.b64decode(encoded)
    image_path.write_bytes(binary)

    metadata = {
        "filename": poster_image.filename,
        "media_type": poster_image.media_type,
        "width": poster_image.width,
        "height": poster_image.height,
    }
    (output_dir / "poster_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    args = parse_args()
    config = load_configuration(args.input)
    poster = parse_poster_input(config)

    preview = render_layout_preview(poster)
    prompt = build_glibatree_prompt(poster)
    poster_image = generate_poster_asset(poster, prompt, preview)
    email_body = compose_marketing_email(poster, poster_image.filename)

    print("=== 环节 1 · 版式预览 ===")
    print(preview)
    print("\n=== 环节 2 · Glibatree 提示词 ===")
    print(prompt)
    print("\n=== 环节 2 · 海报生成 ===")
    print(
        f"生成文件：{poster_image.filename} ({poster_image.media_type}, "
        f"{poster_image.width}x{poster_image.height})"
    )

    print("\n=== 环节 3 · 营销邮件草稿 ===")
    print(email_body)

    if args.output_dir:
        export_outputs(args.output_dir, preview, prompt, email_body, poster_image)
        print(f"\n已将全部生成结果保存至：{args.output_dir.resolve()}")

    if args.send_email:
        email_request = parse_email_payload(config, poster, poster_image, email_body)
        if not email_request:
            raise SystemExit("未在配置中找到邮箱信息，无法发送邮件。")
        response = send_email(email_request)
        print(f"\n邮件发送状态：{response.status} — {response.detail}")


if __name__ == "__main__":
    main()
