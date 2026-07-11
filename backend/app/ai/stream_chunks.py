"""Stream reply text in word chunks for SSE token events."""

from __future__ import annotations

import re


def stream_text_chunks(text: str, *, max_chars: int = 24) -> list[str]:
    """Split assistant reply into SSE-sized chunks (words, bounded length)."""
    if not text:
        return []
    words = re.split(r"(\s+)", text)
    chunks: list[str] = []
    buf = ""
    for part in words:
        if len(buf) + len(part) > max_chars and buf:
            chunks.append(buf)
            buf = part
        else:
            buf += part
    if buf:
        chunks.append(buf)
    return chunks
