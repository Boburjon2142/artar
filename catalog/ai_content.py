import base64
import json
import logging
import urllib.request
import urllib.error
from typing import Iterable, Dict, Any

from django.conf import settings

logger = logging.getLogger(__name__)


def _build_image_parts(images: Iterable[bytes]) -> list:
    parts = []
    for img in images:
        b64 = base64.b64encode(img).decode("ascii")
        parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            }
        )
    return parts


def analyze_content(title: str, description: str, images: Iterable[bytes], target_lang: str = "en") -> Dict[str, Any]:
    """
    Use OpenAI to auto-suggest tags, style, category, title/description/hashtags.
    Returns a dict with possible keys: title, description, tags, hashtags, style, category, summary.
    If API key is missing or request fails, returns {}.
    """
    if not settings.OPENAI_API_KEY:
        return {}

    sys_prompt = (
        "You are a concise content analyzer for an art marketplace. "
        f"Answer in language code '{target_lang}'. "
        "Given a title/description and optional images, respond in JSON with keys: "
        "title (suggested improved title), description (concise improved description), "
        "tags (array of 3-7 short tags), style (short style/medium string), "
        "category (one-word or short phrase), hashtags (array of 3-6 hashtags without #), "
        "summary (1-2 sentence plain summary). Do not add extra keys."
    )

    content_parts = [
        {"type": "text", "text": f"Title: {title or '-'}\nDescription: {description or '-'}"}
    ]
    image_parts = _build_image_parts(images)
    if image_parts:
        content_parts.extend(image_parts)

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": content_parts},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
    except urllib.error.HTTPError as exc:
        # Gracefully degrade on rate limits or other HTTP errors
        logger.warning("AI content analysis HTTPError %s: %s", getattr(exc, "code", None), exc)
        return {}
    except Exception as exc:
        logger.exception("AI content analysis failed: %s", exc)
        return {}
