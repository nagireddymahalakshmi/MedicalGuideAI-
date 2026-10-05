import re
from typing import List, Dict


LAB_NAMES = [
    "hemoglobin",
    "haemoglobin",
    "glucose",
    "blood sugar",
    "cholesterol",
    "triglycerides",
    "creatinine",
    "urea",
    "sodium",
    "potassium",
    "calcium",
    "bilirubin",
    "platelet",
    "white blood cell",
    "wbc",
    "red blood cell",
    "rbc",
    "tsh",
    "vitamin d",
    "vitamin b12"
]


def extract_lab_values(text: str) -> List[Dict]:
    """
    Extract possible laboratory test values from medical text.

    This is basic prototype extraction. Values should be verified
    against the original laboratory report.
    """

    if not text:
        return []

    results = []

    for lab_name in LAB_NAMES:

        pattern = re.compile(
            rf"{re.escape(lab_name)}"
            r"\s*(?:[:=\-])?\s*"
            r"(\d+(?:\.\d+)?)"
            r"\s*([a-zA-Z/%µμ]*)",
            re.IGNORECASE
        )

        matches = pattern.finditer(text)

        for match in matches:

            value = match.group(1)
            unit = match.group(2).strip()

            results.append({
                "test": lab_name,
                "value": value,
                "unit": unit
            })

    return results


def format_lab_values(values: List[Dict]) -> str:
    """
    Convert extracted laboratory values into readable text.
    """

    if not values:
        return "No laboratory values were detected."

    lines = []

    for item in values:
        lines.append(
            f"{item['test']}: {item['value']} {item['unit']}".strip()
        )

    return "\n".join(lines)