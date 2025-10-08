# app/services/image_gen.py
from __future__ import annotations

import os
import base64
from pathlib import Path

# OpenAI v1 SDK
from openai import OpenAI


def gen_image_to_file(
    prompt: str,
    filename: str = "poster.png",
    width: int = 1024,
    height: int = 1024,
) -> tuple[str, str]:
    """
    用 OpenAI 的 Images API 生成一张图片，保存到 /tmp 下，返回 (file_path, data_uri)

    - prompt: 你的完整提示词（已根据前端输入合成）
    - filename: 输出文件名
    - width/height: 生成尺寸
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
    size = f"{width}x{height}"

    client = OpenAI(api_key=api_key)

    # 生成图片（返回 base64）
    res = client.images.generate(
        model=model,
        prompt=prompt,
        size=size,
        # background="transparent",  # 需要透明背景时打开（某些模型/账号不一定支持）
        n=1,
    )

    b64 = res.data[0].b64_json
    data = base64.b64decode(b64)

    # Render 可写目录：/tmp
    out_path = str(Path("/tmp") / filename)
    with open(out_path, "wb") as f:
        f.write(data)

    data_uri = "data:image/png;base64," + b64
    return out_path, data_uri
