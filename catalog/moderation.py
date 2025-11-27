import base64
import json
import logging
import os
import urllib.request
from difflib import SequenceMatcher
from typing import Iterable, Tuple

from django.conf import settings

logger = logging.getLogger(__name__)


def _call_openai_moderation(text: str) -> Tuple[bool, float, dict]:
    """Return flagged, score, details using OpenAI moderation API."""
    payload = {"model": "omni-moderation-latest", "input": text}
    req = urllib.request.Request(
        "https://api.openai.com/v1/moderations",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    res = data["results"][0]
    score = max(res["category_scores"].values() or [0])
    flagged = res.get("flagged", False) or score >= settings.MODERATION_THRESHOLD
    return flagged, score, res.get("categories", {})


def _call_openai_image_moderation(img_bytes: bytes) -> Tuple[bool, float, str]:
    """Use vision model to ask if image unsafe; return flagged, score, reason."""
    b64 = base64.b64encode(img_bytes).decode("ascii")
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are a strict content safety checker. Reply with 'SAFE' or 'UNSAFE' and a short reason.",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Is this image unsafe? Check for nudity, violence, self-harm, illegal, personal data."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            },
        ],
        "temperature": 0,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"].lower()
    flagged = "unsafe" in content
    return flagged, 1.0 if flagged else 0.0, content


def check_duplicates(title: str, existing_titles: Iterable[str]) -> Tuple[bool, float]:
    """Detect near-duplicate titles."""
    title_norm = title.strip().lower()
    best = 0.0
    for t in existing_titles:
        s = SequenceMatcher(None, title_norm, t.strip().lower()).ratio()
        best = max(best, s)
        if best >= settings.MODERATION_DUP_THRESHOLD:
            return True, best
    return False, best


def moderate_content(title: str, description: str, images: Iterable[bytes], existing_titles: Iterable[str]):
    """
    Run text + image moderation and duplicate check.
    Returns (ok: bool, message: str).
    """
    if not settings.MODERATION_ENABLED:
        return True, ""

    text = f"{title}\n\n{description}"
    try:
        flagged, score, _ = _call_openai_moderation(text)
        if flagged:
            return False, "Content blocked by AI moderation (text)."
    except Exception as exc:
        logger.exception("Text moderation failed: %s", exc)

    try:
        dup_flag, dup_score = check_duplicates(title, existing_titles)
        if dup_flag:
            return False, "Duplicate or very similar listing title detected."
    except Exception as exc:
        logger.exception("Duplicate check failed: %s", exc)

    for img in images:
        try:
            flagged, _, reason = _call_openai_image_moderation(img)
            if flagged:
                return False, "Image blocked by AI moderation."
        except Exception as exc:
            logger.exception("Image moderation failed: %s", exc)

    return True, ""
