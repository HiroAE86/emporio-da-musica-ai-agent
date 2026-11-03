"""Redact customer identifiers before sending conversation text to a model."""

import re


def model_safe(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[redacted email]", text)
    text = re.sub(r"(?<!\w)(?:\+?\d[\d ()-]{7,}\d)(?!\w)", "[redacted phone]", text)
    return re.sub(
        r"\b((?:pedido|order|ordem)\s*(?:n[ºo.]?\s*)?[:#-]?\s*)[A-Z0-9][A-Z0-9-]{2,}\b",
        r"\1[redacted order id]",
        text,
        flags=re.IGNORECASE,
    )
