"""Thin wrapper around the shared Zettalgor caption generator."""
from apps.content_plans.services.zettalgor import generate_caption


def generate(topic: str, platform: str, brand_summary: str = "") -> dict:
    return generate_caption(topic, platform, brand_summary)
