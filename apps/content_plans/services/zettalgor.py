"""
Shared client for the Zettalgor chat-completions API. Used for caption,
hashtag, brand-summary, and topic generation.
"""
import json
import re

import requests
from django.conf import settings


class ZettalgorError(Exception):
    pass


def _post(prompt: str, *, timeout: int = 60) -> str:
    url = getattr(settings, "ZETTALGOR_API_URL", "")
    api_key = getattr(settings, "ZETTALGOR_API_KEY", "")
    model = getattr(settings, "ZETTALGOR_MODEL", "ZAi8")

    if not url:
        raise ZettalgorError("ZETTALGOR_API_URL is not configured")

    try:
        response = requests.post(
            url,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise ZettalgorError(f"Zettalgor request failed: {exc}") from exc

    if response.status_code >= 400:
        raise ZettalgorError(
            f"Zettalgor API {response.status_code}: {response.text[:200]}"
        )

    data = response.json()
    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )


def _clean_text(content: str) -> str:
    """Strip backslashes, quotes, and 'Caption:'/'Hashtags:' labels."""
    content = content.replace("\\n", "\n").replace("\\", "").replace('"', "")
    content = re.sub(r"(?i)caption:\s*", "", content)
    content = re.sub(r"(?i)hashtags:\s*", "", content)
    return content.strip()


def generate_caption(topic: str, platform: str, brand_summary: str = "") -> dict:
    """Generate a caption + hashtags pair for a single post.

    Returns ``{"caption": str, "hashtags": str}``.
    """
    brand_block = (
        f"\nBrand context: {brand_summary.strip()}\n" if brand_summary.strip() else ""
    )
    prompt = f"""
Generate one social media caption with hashtags.

Platform: {platform}
Topic: {topic}{brand_block}

Return only this format:
Caption: ...
Hashtags: ...
"""
    raw = _post(prompt)
    cleaned = _clean_text(raw)

    caption_lines, hashtag_lines = [], []
    for line in cleaned.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            hashtag_lines.append(line)
        else:
            caption_lines.append(line)

    return {
        "caption": " ".join(caption_lines).strip(),
        "hashtags": " ".join(hashtag_lines).strip(),
    }


def generate_brand_summary(snapshot: dict, num_topics: int) -> dict:
    """Summarise a website snapshot and propose post topics.

    Returns ``{"summary": str, "keywords": [..], "topics": [..]}``.
    """
    title = snapshot.get("title", "")
    description = snapshot.get("description", "")
    headings = " | ".join(snapshot.get("headings", [])[:20])
    excerpt = (snapshot.get("excerpt") or "")[:3500]

    prompt = f"""
You are a senior social media strategist analysing a brand's website.

Website title: {title}
Meta description: {description}
Headings: {headings}
Body excerpt: {excerpt}

Respond ONLY with valid JSON in this exact shape:
{{
  "summary": "3-sentence brand summary covering what the brand does, who it serves, and tone.",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "topics": ["topic 1", "topic 2", ... {num_topics} topics total]
}}
"""
    raw = _post(prompt)

    # Try to find a JSON block in the response.
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    payload_str = match.group(0) if match else raw.strip()
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as exc:
        raise ZettalgorError(f"Brand summary JSON parse failed: {exc}") from exc

    topics = payload.get("topics") or []
    # Pad / truncate to requested length.
    if len(topics) < num_topics:
        # Backfill with generic topics derived from keywords / title.
        keywords = payload.get("keywords") or []
        i = 0
        while len(topics) < num_topics:
            topics.append(
                f"{title or 'Brand'} highlight #{len(topics)+1}"
                + (f" – {keywords[i % len(keywords)]}" if keywords else "")
            )
            i += 1
    topics = topics[:num_topics]

    return {
        "summary": payload.get("summary", "").strip(),
        "keywords": payload.get("keywords", [])[:10],
        "topics": topics,
    }
