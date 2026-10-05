from typing import Dict, List

from services.ai import generate_answer


def create_summary(document_text: str) -> str:
    """
    Generate a simple patient-friendly summary of a document.
    """

    if not document_text:
        return "No medical document text was provided."

    prompt = """
Create a simple medical-document summary.

Include:
1. Main information
2. Important laboratory values if present
3. Medicines mentioned if present
4. Important observations
5. Questions the patient may discuss with their doctor

Do not diagnose the patient.
Do not recommend changing medication.
Use simple language.
"""

    return generate_answer(
        question=prompt,
        context=document_text
    )


def create_structured_summary(document_text: str) -> Dict:
    """
    Return a structured summary for the frontend.
    """

    summary = create_summary(document_text)

    return {
        "summary": summary,
        "disclaimer": (
            "This summary is generated from the provided document and "
            "is not a medical diagnosis."
        )
    }