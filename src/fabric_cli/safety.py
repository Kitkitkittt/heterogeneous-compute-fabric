from __future__ import annotations

import re

PUBLIC_PROHIBITED_PATTERNS = (
    re.compile(r"BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY", re.IGNORECASE),
    re.compile(r"\bgh[opsu]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b10(?:\.\d{1,3}){3}\b"),
    re.compile(r"\b172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}\b"),
    re.compile(r"\b192\.168(?:\.\d{1,3}){2}\b"),
    re.compile(r"\b100\.(?:6[4-9]|[78]\d|9\d|1[01]\d|12[0-7])(?:\.\d{1,3}){2}\b"),
    re.compile(r"\b(?:fc|fd|fe[89ab])[0-9a-f]{0,2}:[0-9a-f:]+\b", re.IGNORECASE),
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
    re.compile(r"/(?:home|Users)/[^/\s]+", re.IGNORECASE),
)


def contains_private_identity(value: str) -> bool:
    return any(pattern.search(value) for pattern in PUBLIC_PROHIBITED_PATTERNS)
