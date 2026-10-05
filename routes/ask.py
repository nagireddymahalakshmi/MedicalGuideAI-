from fastapi import APIRouter
from pydantic import BaseModel
import sqlite3
import re
import os

router = APIRouter()

DB_PATH = "mediguide.db"


class AskRequest(BaseModel):
    question: str
    report_id: int | None = None
    context: str = ""


# =========================================================
# GET REPORT FROM DATABASE
# =========================================================

def get_report_text(report_id=None):

    if not os.path.exists(DB_PATH):
        return ""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:

        if report_id:
            cursor.execute(
                """
                SELECT extracted_text
                FROM medical_reports
                WHERE id = ?
                """,
                (report_id,)
            )
        else:
            cursor.execute(
                """
                SELECT extracted_text
                FROM medical_reports
                ORDER BY id DESC
                LIMIT 1
                """
            )

        row = cursor.fetchone()

        if row:
            return row[0] or ""

        return ""

    finally:
        conn.close()


# =========================================================
# FIND LAB VALUE
# =========================================================

def find_lab_value(text, test_names):

    for name in test_names:

        pattern = (
            rf"{re.escape(name)}"
            r"\s*[:\-]?\s*"
            r"(\d+(?:\.\d+)?)"
            r"\s*"
            r"(mg/dL|g/dL|mmol/L|U/L|%|10\^9/L)?"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = match.group(1)
            unit = match.group(2) or ""

            return f"{value} {unit}".strip()

    return None


# =========================================================
# LOCAL CHATBOT
# =========================================================

def local_chatbot(question, report_text):

    q = question.lower().strip()

    # -----------------------------------------------------
    # NO REPORT
    # -----------------------------------------------------

    if not report_text.strip():

        return (
            "I could not find a medical report yet. 📄\n\n"
            "Please upload your medical report first."
        )

    # -----------------------------------------------------
    # GREETING
    # -----------------------------------------------------

    if q in [
        "hi",
        "hello",
        "hey",
        "hi there",
        "hello there"
    ]:

        return (
            "Hello! 👋\n\n"
            "I am MediGuide AI. I can help you understand "
            "information found in your uploaded medical report.\n\n"
            "You can ask me things like:\n"
            "• What is my hemoglobin?\n"
            "• What is my glucose level?\n"
            "• What medicines are mentioned?\n"
            "• Explain my report in simple language.\n"
            "• What recommendations are written in my report?"
        )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "summary",
            "summarize",
            "summarise",
            "what is in my report",
            "tell me about my report",
            "report summary"
        ]
    ):

        cleaned = " ".join(
            report_text.split()
        )

        if len(cleaned) > 1500:
            cleaned = cleaned[:1500] + "..."

        return (
            "📄 Here is a simple summary based only "
            "on your uploaded report:\n\n"
            + cleaned
        )

    # -----------------------------------------------------
    # HEMOGLOBIN
    # -----------------------------------------------------

    if any(
        word in q
        for word in [
            "hemoglobin",
            "haemoglobin",
            "hb"
        ]
    ):

        value = find_lab_value(
            report_text,
            [
                "hemoglobin",
                "haemoglobin",
                "hb"
            ]
        )

        if value:

            return (
                f"🩸 Hemoglobin found in your report: "
                f"{value}\n\n"
                "Hemoglobin is a protein in red blood cells "
                "that carries oxygen. The meaning of the result "
                "depends on the person's clinical context."
            )

        return (
            "I could not find a hemoglobin value "
            "in your uploaded report."
        )

    # -----------------------------------------------------
    # GLUCOSE
    # -----------------------------------------------------

    if any(
        word in q
        for word in [
            "glucose",
            "blood sugar",
            "sugar level",
            "fasting sugar"
        ]
    ):

        value = find_lab_value(
            report_text,
            [
                "glucose",
                "blood sugar",
                "fasting glucose",
                "fasting blood sugar"
            ]
        )

        if value:

            return (
                f"🧪 Glucose value found in your report: "
                f"{value}\n\n"
                "Glucose is the amount of sugar measured "
                "in the blood at the time of testing."
            )

        return (
            "I could not find a glucose value "
            "in the uploaded report."
        )

    # -----------------------------------------------------
    # CHOLESTEROL
    # -----------------------------------------------------

    if "cholesterol" in q:

        value = find_lab_value(
            report_text,
            [
                "total cholesterol",
                "cholesterol"
            ]
        )

        if value:

            return (
                f"🧪 Cholesterol value found in your report: "
                f"{value}\n\n"
                "Cholesterol is a type of fat measured in blood."
            )

        return (
            "I could not find a cholesterol value "
            "in your report."
        )

    # -----------------------------------------------------
    # MEDICATIONS
    # -----------------------------------------------------

    if any(
        word in q
        for word in [
            "medicine",
            "medicines",
            "medication",
            "medications",
            "tablet",
            "tablets",
            "capsule",
            "capsules",
            "drug"
        ]
    ):

        medicine_lines = []

        for line in report_text.splitlines():

            lower_line = line.lower()

            if any(
                keyword in lower_line
                for keyword in [
                    "tablet",
                    "tab ",
                    "capsule",
                    "cap ",
                    "syrup",
                    "injection",
                    "medicine",
                    "medication",
                    " mg",
                    "mg "
                ]
            ):

                if line.strip():
                    medicine_lines.append(
                        line.strip()
                    )

        if medicine_lines:

            unique = list(
                dict.fromkeys(
                    medicine_lines
                )
            )

            return (
                "💊 Medication information found "
                "in your report:\n\n"
                + "\n".join(
                    "• " + item
                    for item in unique[:15]
                )
                + "\n\n"
                "Do not start, stop, or change medication "
                "based only on this chatbot. Confirm medication "
                "decisions with your doctor or pharmacist."
            )

        return (
            "I could not find clear medication information "
            "in your uploaded report."
        )

    # -----------------------------------------------------
    # RECOMMENDATIONS
    # -----------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "recommendation",
            "recommendations",
            "what should i do",
            "what can i do",
            "advice",
            "suggestion",
            "suggestions"
        ]
    ):

        # Look for recommendation section in report

        lines = report_text.splitlines()

        found = []

        for index, line in enumerate(lines):

            lower_line = line.lower()

            if any(
                keyword in lower_line
                for keyword in [
                    "recommendation",
                    "recommendations",
                    "treatment plan",
                    "plan",
                    "advice"
                ]
            ):

                for item in lines[
                    index:index + 8
                ]:

                    if item.strip():
                        found.append(
                            item.strip()
                        )

                break

        if found:

            unique = list(
                dict.fromkeys(found)
            )

            return (
                "📋 Recommendations written "
                "in your report:\n\n"
                + "\n".join(
                    "• " + item
                    for item in unique
                )
            )

        return (
            "I could not find a specific recommendation "
            "section in your uploaded report.\n\n"
            "For personal medical advice, please discuss "
            "your report with your doctor."
        )

    # -----------------------------------------------------
    # EXPLAIN
    # -----------------------------------------------------

    if any(
        phrase in q
        for phrase in [
            "explain",
            "simple language",
            "simple",
            "meaning",
            "what does this mean"
        ]
    ):

        cleaned = " ".join(
            report_text.split()
        )

        if len(cleaned) > 1500:
            cleaned = cleaned[:1500] + "..."

        return (
            "🩺 In simple language:\n\n"
            "Your report contains the following "
            "information:\n\n"
            + cleaned
            + "\n\n"
            "This chatbot only explains information "
            "found in the uploaded document. For medical "
            "interpretation, please consult your doctor."
        )

    # -----------------------------------------------------
    # SEARCH REPORT
    # -----------------------------------------------------

    words = [
        word
        for word in re.findall(
            r"[a-zA-Z]+",
            q
        )
        if len(word) > 3
    ]

    matches = []

    report_lower = report_text.lower()

    for word in words:

        if word in report_lower:

            matches.append(word)

    if matches:

        return (
            "🔎 I found related information in your "
            "uploaded report.\n\n"
            "Related terms:\n"
            + ", ".join(matches[:10])
            + "\n\n"
            "Try asking a more specific question."
        )

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    return (
        "I can answer questions about information "
        "found in your uploaded medical report.\n\n"
        "Try asking:\n"
        "• What is my hemoglobin?\n"
        "• What is my glucose level?\n"
        "• What is my cholesterol?\n"
        "• Explain my report in simple language.\n"
        "• What medicines are mentioned?\n"
        "• What recommendations are written in my report?"
    )


# =========================================================
# ASK ENDPOINT
# =========================================================

@router.post("/ask/")
def ask_question(request: AskRequest):

    # First use context sent by frontend, if available
    report_text = request.context.strip()

    # Otherwise get report from SQLite
    if not report_text:

        report_text = get_report_text(
            request.report_id
        )

    answer = local_chatbot(
        request.question,
        report_text
    )

    return {
        "status": "success",
        "success": True,
        "answer": answer
    }