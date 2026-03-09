"""Helpers for products app (e.g. age band from DOB)."""
from datetime import date

from .models import AgeBand


def age_from_dob(dob):
    """Return age in years from date of birth. dob: date or YYYY-MM-DD string."""
    if isinstance(dob, str):
        try:
            dob = date.fromisoformat(dob.strip()[:10])
        except ValueError:
            return None
    if not isinstance(dob, date):
        return None
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return max(0, age)


def get_age_band_for_age(age):
    """Return the AgeBand for the given age (int), or None."""
    if age is None:
        return None
    return AgeBand.objects.filter(min_age__lte=age, max_age__gte=age).order_by("sort_order").first()
