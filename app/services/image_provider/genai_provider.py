from __future__ import annotations

import os
from typing import Optional

from google import genai


class GenAIGoogleImagen:
    """google-genai SDK based Imagen generator."""

    def __init__(self) -> None:
        api_key = os.environ["GOOGLE_API_KEY"]
        self.client = genai.Client(api_key=api_key)
        self.model = os.getenv("GENAI_IMAGEN_MODEL", "imagen-3.0-generate-001")

    def generate(
        self,
        prompt: str,
        *,
        width: int = 1024,
        height: int = 1024,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        guidance_scale: Optional[float] = None,
    ) -> bytes:
        response = self.client.images.generate(
            model=self.model,
            prompt=prompt,
            negative_prompt=negative_prompt,
            number_of_images=1,
            size=f"{width}x{height}",
            guidance=guidance_scale,
            seed=seed,
            safety_filter_level="block_some",
            add_watermark=True,
        )

        if not response.images:
            raise RuntimeError("google-genai returned no images")

        image = response.images[0]
        data = getattr(image, "data", None)
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)

        if hasattr(image, "as_bytes"):
            return bytes(image.as_bytes())

        inline_data = getattr(image, "inline_data", None)
        if inline_data and hasattr(inline_data, "data"):
            return bytes(inline_data.data)

        raise RuntimeError("Unable to extract image bytes from google-genai response")
