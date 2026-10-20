import re
from typing import Any

BANNED_IMPERATIVE_TERMS = [
    r"\bbuy\b",
    r"\bsell\b",
    r"\bhold\b",
    r"\byou should\b",
    r"\bguaranteed\b",
    r"\bwill definitely\b",
    r"\bpromised returns\b",
]


def validate_language_compliance(text: str) -> list[str]:
    """Detects imperative or regulatory non-compliant phrases."""
    violations = []
    text_lower = text.lower()
    for pattern in BANNED_IMPERATIVE_TERMS:
        if re.search(pattern, text_lower):
            clean_term = pattern.replace(r"\b", "")
            violations.append(f"Forbidden imperative/promissory language detected: '{clean_term}'")
    return violations


def extract_numbers(text: str) -> set[float]:
    """Extracts scalar numbers and percentages from narrative text."""
    matches = re.findall(r"[-+]?\d*\.?\d+(?:%)?", text)
    numbers = set()
    for m in matches:
        clean = m.replace("%", "").strip()
        try:
            val = float(clean)
            numbers.add(round(val, 2))
        except ValueError:
            continue
    return numbers


def validate_number_grounding(narrative: str, allowed_numbers: set[float], tolerance: float = 0.5) -> list[str]:
    """
    Extracts every number from narrative prose and validates that it exists
    in the whitelist of computed quant metrics or parameters.
    """
    narrative_numbers = extract_numbers(narrative)
    unauthorized = []

    for num in narrative_numbers:
        matched = any(abs(num - allowed) <= tolerance for allowed in allowed_numbers)
        if not matched:
            unauthorized.append(f"Ungrounded number in narrative: {num}")

    return unauthorized