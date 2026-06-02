"""
Gemini image generation. Decrypts the caller's stored API key and uses the
google-genai SDK; falls back to a REST call if the SDK isn't installed.

Returns the relative MEDIA path of the saved PNG.
"""
import base64
import io
import os
import uuid

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.content_plans.crypto import decrypt


class GeminiError(Exception):
    pass


PLATFORM_ASPECT = {
    "instagram": "1:1",
    "facebook": "1.91:1",
    "linkedin": "1.91:1",
    "x": "16:9",
}


def _api_key_for(user) -> str:
    try:
        record = user.ai_key
    except Exception as exc:  # pragma: no cover - RelatedObjectDoesNotExist
        raise GeminiError("User has no Gemini key on file") from exc

    if not record.gemini_key_encrypted:
        raise GeminiError("User has no Gemini key on file")
    return decrypt(record.gemini_key_encrypted)


def build_prompt(topic: str, platform: str, brand_summary: str = "", override: str = "") -> str:
    if override and override.strip():
        return override.strip()

    aspect = PLATFORM_ASPECT.get(platform, "1:1")
    brand_block = (
        f" Brand style: {brand_summary.strip()}." if brand_summary.strip() else ""
    )
    return (
        f"Create a {aspect} aspect ratio social media image for: {topic}."
        f"{brand_block} Bold, on-brand, high contrast, scroll-stopping. "
        "No text overlays."
    )


def _save_png(plan_id: int, item_id: int, png_bytes: bytes) -> str:
    name = f"content_plans/{plan_id}/{item_id}-{uuid.uuid4().hex[:8]}.png"
    return default_storage.save(name, ContentFile(png_bytes))


def _generate_via_sdk(api_key: str, model: str, prompt: str) -> bytes:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    for cand in getattr(response, "candidates", []) or []:
        content = getattr(cand, "content", None)
        for part in getattr(content, "parts", []) or []:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return inline.data
    raise GeminiError("Gemini SDK returned no image data")


def _generate_via_rest(api_key: str, model: str, prompt: str) -> bytes:
    """Fallback REST call (used when google-genai isn't installed)."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }
    timeout = getattr(settings, "GEMINI_REQUEST_TIMEOUT", 60)
    try:
        r = requests.post(url, json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise GeminiError(f"Gemini REST call failed: {exc}") from exc
    if r.status_code >= 400:
        raise GeminiError(f"Gemini HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    for cand in data.get("candidates", []):
        for part in (cand.get("content") or {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])
    raise GeminiError("Gemini REST returned no image data")


def generate(item, brand_summary: str = "", prompt_override: str = "") -> str:
    """Generate a Gemini image for a ContentPlanItem and save it.

    Returns the path relative to MEDIA_ROOT.
    """
    api_key = _api_key_for(item.plan.user)
    model = (
        item.plan.image_model
        or getattr(item.plan.user.ai_key, "default_image_model", "")
        or getattr(settings, "GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    )

    prompt = build_prompt(item.topic, item.platform, brand_summary, prompt_override)

    try:
        png = _generate_via_sdk(api_key, model, prompt)
    except ImportError:
        png = _generate_via_rest(api_key, model, prompt)
    except GeminiError:
        raise
    except Exception as exc:
        raise GeminiError(f"Gemini generation failed: {exc}") from exc

    saved_path = _save_png(item.plan_id, item.id, png)
    item.image_prompt = prompt
    return saved_path


def validate_api_key(api_key: str) -> bool:
    """Cheap check: list models. Returns True on success."""
    if not api_key:
        return False
    try:
        from google import genai  # type: ignore

        client = genai.Client(api_key=api_key)
        # Iterate one model to confirm.
        for _ in client.models.list():
            return True
        return True
    except ImportError:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models?key="
            f"{api_key}"
        )
        try:
            r = requests.get(url, timeout=15)
            return r.status_code < 400
        except requests.RequestException:
            return False
    except Exception:
        return False
