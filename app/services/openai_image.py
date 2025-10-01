# app/services/openai_image.py
from __future__ import annotations
import base64
from uuid import uuid4
from typing import Optional

from openai import OpenAI


def generate_image_with_openai(
    prompt: str,
    api_key: str,
    base_url: Optional[str] = None,
    size: str = "1024x1024",
) -> str:
    """
    调用 OpenAI 图片模型生成海报，返回在容器 /tmp 下保存的 PNG 文件路径。
    """
    client = OpenAI(api_key=api_key, base_url=base_url or None)

    # gpt-image-1 支持 prompt → image
    resp = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=size,
        quality="high",
    )
    b64_png = resp.data[0].b64_json
    img_bytes = base64.b64decode(b64_png)

    out_path = f"/tmp/poster_{uuid4().hex}.png"
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    return out_path
