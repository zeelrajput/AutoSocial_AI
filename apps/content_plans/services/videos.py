"""
Gemini Veo video generation.

Submits a Veo generation job using the user's stored Gemini API key, polls
the long-running operation until it completes, downloads the rendered mp4
and saves it to MEDIA. Returns the relative MEDIA path of the saved file.

Falls back to the REST API when google-genai isn't installed.
"""
import os
import time
import uuid

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.content_plans.crypto import decrypt


class VeoError(Exception):
    pass


PLATFORM_ASPECT = {
    "instagram": "9:16",
    "facebook": "16:9",
    "linkedin": "16:9",
    "x": "16:9",
}


def _api_key_for(user) -> str:
    try:
        record = user.ai_key
    except Exception as exc:  # pragma: no cover
        raise VeoError("User has no Gemini key on file") from exc
    if not record.gemini_key_encrypted:
        raise VeoError("User has no Gemini key on file")
    return decrypt(record.gemini_key_encrypted)


def build_prompt(
    topic: str, platform: str, brand_summary: str = "", override: str = ""
) -> str:
    if override and override.strip():
        return override.strip()
    aspect = PLATFORM_ASPECT.get(platform, "9:16")
    brand_block = (
        f" Brand style: {brand_summary.strip()}." if brand_summary.strip() else ""
    )
    return (
        f"Create a short {aspect} aspect ratio social media video for: {topic}."
        f"{brand_block} 5-8 seconds. Cinematic, smooth camera motion, "
        "on-brand, scroll-stopping. No text overlays. No watermark."
    )


def _save_mp4(plan_id: int, item_id: int, mp4_bytes: bytes) -> str:
    name = f"content_plans/{plan_id}/{item_id}-{uuid.uuid4().hex[:8]}.mp4"
    return default_storage.save(name, ContentFile(mp4_bytes))


# ---------------------------------------------------------------------------
# SDK path
# ---------------------------------------------------------------------------

def _generate_via_sdk(
    api_key: str, model: str, prompt: str, aspect_ratio: str
) -> bytes:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    client = genai.Client(api_key=api_key)

    cfg_kwargs = {"aspect_ratio": aspect_ratio}
    # Older SDK builds may not accept aspect_ratio; ignore on TypeError.
    try:
        config = types.GenerateVideosConfig(**cfg_kwargs)
    except TypeError:
        config = types.GenerateVideosConfig()

    operation = client.models.generate_videos(
        model=model,
        prompt=prompt,
        config=config,
    )

    poll_every = getattr(settings, "GEMINI_VIDEO_POLL_INTERVAL", 10)
    poll_timeout = getattr(settings, "GEMINI_VIDEO_TIMEOUT", 600)
    waited = 0
    while not getattr(operation, "done", False):
        if waited >= poll_timeout:
            raise VeoError("Veo generation timed out")
        time.sleep(poll_every)
        waited += poll_every
        operation = client.operations.get(operation)

    response = getattr(operation, "response", None) or getattr(
        operation, "result", None
    )
    videos = getattr(response, "generated_videos", None) or []
    if not videos:
        raise VeoError("Veo SDK returned no video data")

    video_obj = videos[0].video
    # SDK >= 0.4 exposes .video_bytes; otherwise download_url + auth header.
    raw = getattr(video_obj, "video_bytes", None)
    if raw:
        return raw

    download_url = getattr(video_obj, "uri", None) or getattr(
        video_obj, "download_uri", None
    )
    if download_url:
        sep = "&" if "?" in download_url else "?"
        r = requests.get(
            f"{download_url}{sep}key={api_key}",
            timeout=getattr(settings, "GEMINI_REQUEST_TIMEOUT", 60),
        )
        if r.status_code >= 400:
            raise VeoError(f"Veo download HTTP {r.status_code}: {r.text[:200]}")
        return r.content

    raise VeoError("Veo SDK returned no downloadable video URL")


# ---------------------------------------------------------------------------
# REST fallback
# ---------------------------------------------------------------------------

_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _generate_via_rest(
    api_key: str, model: str, prompt: str, aspect_ratio: str
) -> bytes:
    submit_url = f"{_BASE}/models/{model}:predictLongRunning?key={api_key}"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"aspectRatio": aspect_ratio},
    }
    timeout = getattr(settings, "GEMINI_REQUEST_TIMEOUT", 60)
    try:
        r = requests.post(submit_url, json=payload, timeout=timeout)
    except requests.RequestException as exc:
        raise VeoError(f"Veo submit failed: {exc}") from exc
    if r.status_code >= 400:
        raise VeoError(f"Veo submit HTTP {r.status_code}: {r.text[:300]}")
    op = r.json()
    op_name = op.get("name")
    if not op_name:
        raise VeoError("Veo submit returned no operation name")

    # Poll
    poll_url = f"{_BASE}/{op_name}?key={api_key}"
    poll_every = getattr(settings, "GEMINI_VIDEO_POLL_INTERVAL", 10)
    poll_timeout = getattr(settings, "GEMINI_VIDEO_TIMEOUT", 600)
    waited = 0
    while True:
        if waited >= poll_timeout:
            raise VeoError("Veo generation timed out")
        time.sleep(poll_every)
        waited += poll_every
        pr = requests.get(poll_url, timeout=timeout)
        if pr.status_code >= 400:
            raise VeoError(f"Veo poll HTTP {pr.status_code}: {pr.text[:200]}")
        data = pr.json()
        if data.get("done"):
            op = data
            break

    err = op.get("error")
    if err:
        raise VeoError(f"Veo failed: {err}")

    # Find the video URI in the response payload
    resp = op.get("response", {})
    videos = (
        resp.get("generatedVideos")
        or resp.get("generated_videos")
        or resp.get("videos")
        or []
    )
    if not videos:
        # Some responses nest under generateVideoResponse
        gvr = resp.get("generateVideoResponse") or {}
        videos = gvr.get("generatedSamples") or []

    if not videos:
        raise VeoError("Veo REST returned no video data")

    first = videos[0]
    uri = (
        (first.get("video") or {}).get("uri")
        or first.get("uri")
        or first.get("downloadUri")
    )
    if not uri:
        raise VeoError("Veo REST returned no downloadable video URL")

    sep = "&" if "?" in uri else "?"
    dl = requests.get(f"{uri}{sep}key={api_key}", timeout=timeout)
    if dl.status_code >= 400:
        raise VeoError(f"Veo download HTTP {dl.status_code}: {dl.text[:200]}")
    return dl.content


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------

def generate(item, brand_summary: str = "", prompt_override: str = "") -> str:
    """Generate a Veo video for a ContentPlanItem and save it.

    Returns the path relative to MEDIA_ROOT.
    """
    api_key = _api_key_for(item.plan.user)

    model = (
        item.plan.video_model
        or getattr(item.plan.user.ai_key, "default_video_model", "")
        or getattr(settings, "GEMINI_VIDEO_MODEL", "veo-3.0-fast-generate-001")
    )
    aspect = PLATFORM_ASPECT.get(item.platform, "9:16")
    prompt = build_prompt(item.topic, item.platform, brand_summary, prompt_override)

    try:
        mp4 = _generate_via_sdk(api_key, model, prompt, aspect)
    except ImportError:
        mp4 = _generate_via_rest(api_key, model, prompt, aspect)
    except VeoError:
        raise
    except Exception as exc:
        raise VeoError(f"Veo generation failed: {exc}") from exc

    saved_path = _save_mp4(item.plan_id, item.id, mp4)
    item.video_prompt = prompt
    return saved_path
