from __future__ import annotations
import re

_DIGITS_ONLY = re.compile(r"[^0-9]")

def sanitize_line(text: str) -> str:
    """
    Clean one line of OCR output.
    Strict mode: ONLY keeps 0-9.
    """
    text = text.strip()
    return _DIGITS_ONLY.sub("", text)

def sanitize_prediction(lines: list[str]) -> str:
    return "\n".join(sanitize_line(line) for line in lines)