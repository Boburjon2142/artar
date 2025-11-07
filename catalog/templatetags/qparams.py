from __future__ import annotations

from django import template
from django.http import QueryDict

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

