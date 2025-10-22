import os
import inspect
import logging
from typing import Optional, Tuple

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

log = logging.getLogger("ai-service")


def _ensure_credentials_from_b64():
    """
    如果设置了 GCP_KEY_B64，则把它写到 /opt/render/project/src/gcp-key.json
    并设置 GOOGLE_APPLICATION_CREDENTIALS 指向该路径。
    """
    key_b64 = os.getenv("GCP_KEY_B64")
    if not key_b64:
        return

    out_path = "/opt/render/project/src/gcp-key.json"
    try:
        import base64
        import pathlib

        pathlib.Path(out_path).write_bytes(base64.b64decode(key_b64))
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = out_path
        log.info("Wrote service account key to %s from GCP_KEY_B64", out_path)
    except Exception as e:  # pragma: no cover - startup diagnostics
        log.exception("Failed to write key from GCP_KEY_B64: %s", e)


def init_vertex():
    """
    初始化 Vertex AI（与 ai-vertex 项目一致）：
    - 从环境变量读取 GCP_PROJECT_ID / GCP_LOCATION（默认 us-central1）
    - 如果设置了 GCP_KEY_B64，则自动落盘并设置 GOOGLE_APPLICATION_CREDENTIALS
    """
    _ensure_credentials_from_b64()

    project = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")
    if not project:
        raise RuntimeError("Missing env GCP_PROJECT_ID")

    vertexai.init(project=project, location=location)
    log.info("[VertexImagen3] project=%s location=%s", project, location)


def _parse_size(size: str) -> Tuple[int, int]:
    # 允许 "1024x1024" 形式，异常则回退 1024x1024
    try:
        w, h = [int(x) for x in size.lower().split("x")]
        if w <= 0 or h <= 0:
            raise ValueError
        return w, h
    except Exception:
        return 1024, 1024


class VertexImagen:
    """
    只负责【生成】能力，使用 imagen-3.0-generate-001。
    """

    def __init__(self, model_name: str = "imagen-3.0-generate-001") -> None:
        self.model_name = model_name
        self._model = ImageGenerationModel.from_pretrained(self.model_name)
        # 读取 generate_images 的参数签名以做兼容
        self._sig_params = set(inspect.signature(self._model.generate_images).parameters.keys())
        log.info(
            "VertexImagen ready with %s; generate_images params=%s",
            self.model_name,
            sorted(self._sig_params),
        )

    def generate_bytes(
        self,
        prompt: str,
        size: str = "1024x1024",
        negative_prompt: Optional[str] = None,
        safety_filter_level: str = "block_few",
        seed: Optional[int] = None,
    ) -> bytes:
        """
        生成一张图片并返回字节（JPEG/PNG）；
        兼容不同 SDK 版本的参数：size / image_dimensions / aspect_ratio。
        """
        w, h = _parse_size(size)

        kwargs = dict(
            prompt=prompt,
            number_of_images=1,
            safety_filter_level=safety_filter_level,
        )
        if negative_prompt and "negative_prompt" in self._sig_params:
            kwargs["negative_prompt"] = negative_prompt
        if seed is not None and "seed" in self._sig_params:
            kwargs["seed"] = seed

        if "size" in self._sig_params:
            kwargs["size"] = f"{w}x{h}"
        elif "image_dimensions" in self._sig_params:
            kwargs["image_dimensions"] = (w, h)
        elif "aspect_ratio" in self._sig_params:
            # 回退到比例（仅支持常见值）
            ratio = f"{w}:{h}"
            allowed = {"1:1", "16:9", "9:16", "4:3", "3:4"}
            kwargs["aspect_ratio"] = ratio if ratio in allowed else "1:1"
        # 否则用 SDK 默认尺寸

        res = self._model.generate_images(**kwargs)
        # 官方对象通常是 res.images[0]._image_bytes
        return res.images[0]._image_bytes
