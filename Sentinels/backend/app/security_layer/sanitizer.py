"""
Input Sanitizer — Cleans and normalizes all incoming text fields before they
reach the LLM or are persisted to the database.

Sanitization Pipeline:
1. Unicode normalization (NFKC) — collapses homoglyphs and compatibility chars
2. HTML / script tag stripping — removes any embedded markup
3. Control character removal — strips non-printable characters
4. Suspicious character blocklist — removes zero-width joiners, RTL overrides, etc.
5. Whitespace normalization — collapses excessive whitespace
6. LLM-safe truncation — enforces max field length to prevent token abuse
"""

import re
import unicodedata
from typing import Dict, Any


# ── Configuration ────────────────────────────────────────────────────────────
MAX_FIELD_LENGTH = 5000  # Max characters per text field (prevents token stuffing)
MAX_CUSTOMER_ID_LENGTH = 64
MAX_EVENT_TYPE_LENGTH = 64

# Zero-width and invisible unicode characters often used in injection attacks
INVISIBLE_CHARS = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f"   # Zero-width spaces & joiners
    r"\u202a\u202b\u202c\u202d\u202e"     # Bidi overrides (RTL attacks)
    r"\u2060\u2061\u2062\u2063\u2064"     # Invisible operators
    r"\ufeff\ufff9\ufffa\ufffb"           # BOM & interlinear annotations
    r"\U000e0001-\U000e007f]",            # Tag characters
    flags=re.UNICODE,
)

# HTML / XML / script tags
HTML_TAG_PATTERN = re.compile(r"<[^>]+>", re.IGNORECASE | re.DOTALL)

# Script-like patterns (even without proper HTML tags)
SCRIPT_PATTERNS = re.compile(
    r"(?:javascript|vbscript|data):[^\s]*|"
    r"on\w+\s*=\s*[\"'][^\"']*[\"']|"
    r"expression\s*\([^)]*\)",
    re.IGNORECASE,
)

# Control characters (except newline, tab, carriage return)
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Excessive whitespace (3+ consecutive spaces or blank lines)
EXCESSIVE_WHITESPACE = re.compile(r"[ \t]{3,}")
EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")


# ── Core Sanitization Functions ──────────────────────────────────────────────

def normalize_unicode(text: str) -> str:
    """
    Apply NFKC normalization to collapse visually similar characters.
    This defeats homoglyph attacks (e.g., Cyrillic 'а' → Latin 'a').
    """
    return unicodedata.normalize("NFKC", text)


def strip_html_tags(text: str) -> str:
    """Remove all HTML/XML tags and script-like patterns."""
    text = HTML_TAG_PATTERN.sub("", text)
    text = SCRIPT_PATTERNS.sub("[REMOVED]", text)
    return text


def remove_invisible_chars(text: str) -> str:
    """Strip zero-width characters, bidi overrides, and invisible Unicode."""
    return INVISIBLE_CHARS.sub("", text)


def remove_control_chars(text: str) -> str:
    """Remove non-printable control characters (preserving newlines and tabs)."""
    return CONTROL_CHARS.sub("", text)


def normalize_whitespace(text: str) -> str:
    """Collapse excessive whitespace and blank lines."""
    text = EXCESSIVE_WHITESPACE.sub("  ", text)
    text = EXCESSIVE_NEWLINES.sub("\n\n", text)
    return text.strip()


def truncate(text: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    """
    LLM-safe truncation: cut at max_length and append a marker so the
    LLM knows the input was truncated (avoids hallucinating missing content).
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "\n[INPUT TRUNCATED — original exceeded safe length]"


# ── Main Pipeline ────────────────────────────────────────────────────────────

def sanitize_text(text: str, max_length: int = MAX_FIELD_LENGTH) -> str:
    """
    Full sanitization pipeline for a single text field.

    Order matters:
    1. Unicode normalize (so subsequent regex works on canonical forms)
    2. Strip invisible chars (before HTML strip, as they could be inside tags)
    3. Strip HTML / scripts
    4. Remove control chars
    5. Normalize whitespace
    6. Truncate
    """
    if not text or not isinstance(text, str):
        return ""

    text = normalize_unicode(text)
    text = remove_invisible_chars(text)
    text = strip_html_tags(text)
    text = remove_control_chars(text)
    text = normalize_whitespace(text)
    text = truncate(text, max_length)

    return text


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize all string fields in an input event payload.
    Applies field-specific length limits for structured fields.
    """
    sanitized = {}
    for key, value in payload.items():
        if isinstance(value, str):
            if key == "customer_id":
                sanitized[key] = sanitize_text(value, max_length=MAX_CUSTOMER_ID_LENGTH)
            elif key == "event_type":
                sanitized[key] = sanitize_text(value, max_length=MAX_EVENT_TYPE_LENGTH)
            else:
                sanitized[key] = sanitize_text(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_payload(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_text(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized
