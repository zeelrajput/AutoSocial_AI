"""
Schedule builder: turns plan inputs into ordered datetime slots in
``Asia/Kolkata`` (then storage in UTC via ``django.utils.timezone``).
"""
from datetime import datetime, timedelta

from django.utils import timezone


def step_for(plan) -> int:
    if plan.frequency == "daily":
        return 1
    if plan.frequency == "alternate":
        return 2
    if plan.frequency == "custom":
        return max(1, int(plan.custom_interval_days or 1))
    return 1


def slots_per_platform(plan) -> int:
    """How many slots (regardless of platform) does this plan need?"""
    step = step_for(plan)
    return max(1, (plan.duration_days + step - 1) // step)


def build(plan):
    """Return a list of timezone-aware datetimes, one per slot.

    Items are expanded per-platform downstream.
    """
    if not plan.start_date or not plan.posting_time:
        return []

    step = step_for(plan)
    n = slots_per_platform(plan)
    out = []
    tz = timezone.get_current_timezone()
    for i in range(n):
        date = plan.start_date + timedelta(days=i * step)
        naive = datetime.combine(date, plan.posting_time)
        aware = timezone.make_aware(naive, tz)
        out.append(aware)
    return out
