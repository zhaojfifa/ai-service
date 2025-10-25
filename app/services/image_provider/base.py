from __future__ import annotations

from typing import Optional, Protocol


class ImageProvider(Protocol):
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
        ...
