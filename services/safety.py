from typing import List


EMERGENCY_KEYWORDS = [
    "chest pain",
    "difficulty breathing",
    "shortness of breath",
    "severe bleeding",
    "unconscious",
    "fainted",
    "seizure",
    "stroke",
    "suicide",
    "suicidal",
    "cannot breathe",
    "loss of consciousness"
]


HIGH_RISK_KEYWORDS = [
    "overdose",
    "allergic reaction",
    "severe allergy",
    "blood in vomit",
    "blood in stool",
    "severe abdominal pain"
]


def find_risk_keywords(text: str) -> List[str]:
    """
    Find potentially important safety-related terms.
    """

    text_lower = text.lower()

    found = []

    for keyword in EMERGENCY_KEYWORDS + HIGH_RISK_KEYWORDS:
        if keyword in text_lower:
            found.append(keyword)

    return found


def check_safety(text: str) -> dict:
    """
    Perform a basic safety check on user/document text.
    """

    found = find_risk_keywords(text)

    emergency_found = any(
        keyword in EMERGENCY_KEYWORDS
        for keyword in found
    )

    high_risk_found = any(
        keyword in HIGH_RISK_KEYWORDS
        for keyword in found
    )

    if emergency_found:
        return {
            "safe": False,
            "level": "emergency",
            "keywords": found,
            "message": (
                "The information may contain symptoms that could require "
                "urgent medical attention. Seek immediate medical care or "
                "contact local emergency services."
            )
        }

    if high_risk_found:
        return {
            "safe": False,
            "level": "high",
            "keywords": found,
            "message": (
                "The information contains potentially important medical "
                "warning signs. Please contact a qualified healthcare "
                "professional promptly."
            )
        }

    return {
        "safe": True,
        "level": "normal",
        "keywords": [],
        "message": (
            "No basic emergency keywords were detected. "
            "This automated check does not guarantee that the information "
            "is medically safe."
        )
    }


def get_safety_notice(text: str) -> str:
    """
    Return a user-friendly safety notice.
    """

    result = check_safety(text)

    return result["message"]