from __future__ import annotations

from django import template
from django.http import QueryDict
from django.apps import apps
from django.db import models
from django.db.models import Sum, Avg
from django.contrib.auth import get_user_model

register = template.Library()


@register.simple_tag(takes_context=True)
def qurl(context, **kwargs) -> str:
    """Build a querystring preserving existing GET params and updating the given ones.

    Usage in templates:
      href="{% qurl page=2 %}"
      href="{% qurl cpage=comments_page.next_page_number %}"
    """
    request = context.get("request")
    if request is not None:
        query = request.GET.copy()
    else:
        query = QueryDict(mutable=True)

    for key, value in kwargs.items():
        if value is None or value == "":
            query.pop(key, None)
        else:
            query[key] = str(value)

    encoded = query.urlencode()
    return f"?{encoded}" if encoded else ""


@register.filter(name="phone_href")
def phone_href(value: object) -> str:
    """Build tel: URL from a phone number-like value.

    Keeps digits and leading '+'. Returns empty string if invalid.
    """
    if value is None:
        return ""
    s = str(value)
    cleaned = []
    lead = True
    for ch in s.strip():
        if ch.isdigit():
            cleaned.append(ch)
            lead = False
        elif ch == "+" and lead:
            cleaned.append(ch)
            lead = False
    num = "".join(cleaned)
    return f"tel:{num}" if num else ""


def _listing_model():
    candidates = [
        "Art", "Artwork", "ArtItem", "Product", "Item", "Listing", "Ad", "Announcement", "Elon",
    ]
    for name in candidates:
        try:
            return apps.get_model("catalog", name)
        except LookupError:
            continue
    return None


def _author_field(model) -> str | None:
    User = get_user_model()
    for f in model._meta.get_fields():
        if isinstance(f, models.ForeignKey):
            rel = getattr(f.remote_field, "model", None)
            if rel is User or f.name in {"author", "user", "owner", "created_by", "posted_by"}:
                return f.name
    return None


@register.simple_tag
def user_listing_stats(user) -> dict:
    """Return aggregate stats for listings authored by `user`.

    Keys: total, published, drafts, views, avg_rating
    Values default to 0 if fields are missing.
    """
    Model = _listing_model()
    if not Model or not getattr(user, "is_authenticated", False):
        return {"total": 0, "published": 0, "drafts": 0, "views": 0, "avg_rating": 0}

    field_names = {f.name for f in Model._meta.get_fields() if isinstance(f, models.Field)}
    a_field = _author_field(Model)
    if not a_field:
        qs = Model.objects.none()
    else:
        qs = Model.objects.filter(**{a_field: user})

    total = qs.count()

    # Published/drafts detection
    published = drafts = 0
    if "is_published" in field_names:
        published = qs.filter(is_published=True).count()
        drafts = total - published
    elif "status" in field_names:
        published = qs.filter(status__in=["published", "active", "approved"]).count()
        drafts = total - published
    else:
        published = total
        drafts = 0

    # Views sum
    views_field = next((n for n in ["views_count", "view_count", "views"] if n in field_names), None)
    if views_field:
        views = qs.aggregate(v=Sum(views_field))['v'] or 0
    else:
        views = 0

    # Average rating
    rating_field = next((n for n in ["avg_rating", "rating"] if n in field_names), None)
    if rating_field:
        avg_rating = qs.aggregate(a=Avg(rating_field))['a'] or 0
    else:
        avg_rating = 0

    return {"total": total, "published": published, "drafts": drafts, "views": views, "avg_rating": avg_rating}
