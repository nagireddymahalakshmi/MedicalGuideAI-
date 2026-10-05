import re
from typing import List, Dict


MEDICATION_PATTERN = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z0-9\- ]{2,40})"
    r"\s+"
    r"(?P<dose>\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|mL|units?))",
    re.IGNORECASE
)


COMMON_MEDICATION_WORDS = [
    "tablet",
    "capsule",
    "syrup",
    "injection",
    "medicine",
    "medication"
]


def extract_medications(text: str) -> List[Dict]:
    """
    Extract possible medication names and doses from text.

    This is a prototype extraction method and should be verified
    against the original medical document.
    """

    if not text:
        return []

    results = []

    for match in MEDICATION_PATTERN.finditer(text):
        name = match.group("name").strip()
        dose = match.group("dose").strip()

        results.append({
            "name": name,
            "dose": dose,
            "raw_text": match.group(0)
        })

    # Remove duplicates
    unique = []
    seen = set()

    for item in results:
        key = (
            item["name"].lower(),
            item["dose"].lower()
        )

        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


def extract_medication_lines(text: str) -> List[str]:
    """
    Find lines that appear to contain medication information.
    """

    lines = text.splitlines()

    return [
        line.strip()
        for line in lines
        if any(
            word in line.lower()
            for word in COMMON_MEDICATION_WORDS
        )
    ]