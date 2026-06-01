"""Thin wrapper exposing the brand-summary call as its own module."""
from apps.content_plans.services.zettalgor import generate_brand_summary


def summarise(snapshot: dict, num_topics: int) -> dict:
    return generate_brand_summary(snapshot, max(1, num_topics))
