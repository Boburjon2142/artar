from django import template

register = template.Library()


@register.filter(name="phone_href")
def phone_href(value: object) -> str:
    """Return a tel: href from a phone-like string.

    Keeps only digits and leading '+'. Returns empty string if nothing usable.
    """
    if value is None:
        return ""
    s = str(value)
    cleaned = []
    for ch in s.strip():
        if ch.isdigit() or (ch == "+" and not cleaned):
            cleaned.append(ch)
    num = "".join(cleaned)
    return f"tel:{num}" if num else ""

