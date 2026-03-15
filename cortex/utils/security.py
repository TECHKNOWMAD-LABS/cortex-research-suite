"""Security utilities for input sanitization, injection detection, and validation.

Enterprise-grade input safety for LLM pipelines.
"""

from __future__ import annotations

import hashlib
import re
import json
from typing import Any

from cortex.config.settings import SecurityConfig


# Pre-compiled patterns for prompt injection detection
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous\s+)?instructions?", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*[:=]", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system\s+)?secrets?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+", re.IGNORECASE),
    re.compile(r"<\s*/?script", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
]


class InputValidationError(Exception):
    """Raised when input fails security validation."""


def sanitize_input(
    text: str,
    *,
    max_length: int = 50_000,
    strip_control_chars: bool = True,
    check_injection: bool = True,
) -> str:
    """Sanitize and validate input text for LLM consumption.

    Args:
        text: Raw input text.
        max_length: Maximum allowed character count.
        strip_control_chars: Remove non-printable control characters.
        check_injection: Check for common prompt injection patterns.

    Returns:
        Sanitized text.

    Raises:
        InputValidationError: If input fails validation.
    """
    if not isinstance(text, str):
        raise InputValidationError(f"Expected string input, got {type(text).__name__}")

    if len(text) > max_length:
        raise InputValidationError(f"Input exceeds maximum length ({len(text)} > {max_length})")

    if strip_control_chars:
        # Keep newlines, tabs, and standard whitespace
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    if check_injection:
        injection_matches = detect_injection(text)
        if injection_matches:
            raise InputValidationError(f"Potential prompt injection detected: {', '.join(injection_matches)}")

    return text.strip()


def detect_injection(text: str) -> list[str]:
    """Detect potential prompt injection patterns.

    Returns list of matched pattern descriptions. Empty list = clean.
    """
    matches: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            matches.append(pattern.pattern)
    return matches


def validate_json_schema(data: Any, schema: dict[str, Any]) -> list[str]:
    """Lightweight JSON schema validation (type + required fields).

    Does not require jsonschema library. Validates:
    - type checking (object, array, string, number, boolean)
    - required fields
    - nested properties

    Returns list of validation errors. Empty list = valid.
    """
    errors: list[str] = []
    _validate_node(data, schema, "", errors)
    return errors


def _validate_node(data: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    expected_type = schema.get("type")
    if expected_type:
        type_map = {
            "object": dict,
            "array": list,
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
        }
        expected = type_map.get(expected_type)
        if expected and not isinstance(data, expected):
            errors.append(f"{path or 'root'}: expected {expected_type}, got {type(data).__name__}")
            return

    if expected_type == "object" and isinstance(data, dict):
        for req in schema.get("required", []):
            if req not in data:
                errors.append(f"{path}.{req}: required field missing")
        for prop_name, prop_schema in schema.get("properties", {}).items():
            if prop_name in data:
                _validate_node(data[prop_name], prop_schema, f"{path}.{prop_name}", errors)

    if expected_type == "array" and isinstance(data, list):
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(data):
                _validate_node(item, items_schema, f"{path}[{i}]", errors)


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content for integrity verification."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
