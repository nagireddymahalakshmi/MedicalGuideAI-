# services/ai.py

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. "
        "Please add your OpenAI API key to the .env file."
    )

if not OPENAI_MODEL:
    raise RuntimeError(
        "OPENAI_MODEL is missing. "
        "Please add a valid API model name to the .env file."
    )

client = OpenAI(
    api_key=OPENAI_API_KEY
)


SYSTEM_PROMPT = """
You are MediGuide AI, a medical-document understanding assistant.

Your job is to help the user understand the medical document they uploaded.

STRICT RULES:

1. Use ONLY information contained in the verified medical document.
2. Do not invent patient information.
3. Do not invent test results.
4. Do not invent diagnoses.
5. Do not prescribe medicines.
6. Do not recommend changing medicine or dosage.
7. Do not say that a laboratory value is normal or abnormal unless
   the document itself explicitly says so.
8. If the requested information is not present in the document,
   clearly say:
   "I could not find this information in your uploaded document."
9. You may explain medical words appearing in the document in simple
   language.
10. You may summarize recommendations, follow-up instructions,
    precautions, medicines, and findings that are explicitly written
    in the document.
11. If the user asks a follow-up question, understand the conversation
    naturally and use the same verified document as context.
12. Answer the user's actual question directly.
13. Do not repeatedly tell the user to ask a specific question.
14. Never pretend to be a doctor.
15. For emergencies or serious symptoms, advise the user to seek
    appropriate professional medical care immediately.

IMPORTANT:
The document is the source of truth.
Do not add medical facts that are not supported by the document.

Give answers in clear, simple, patient-friendly language.
"""


def generate_answer(
    question: str,
    context: str
):

    question = (question or "").strip()
    context = (context or "").strip()

    if not question:
        return "Please enter your question."

    if not context:
        return (
            "I could not find a verified medical document. "
            "Please upload and verify your medical document first."
        )

    try:

        user_prompt = f"""
VERIFIED MEDICAL DOCUMENT
-------------------------
{context}

-------------------------
USER QUESTION
-------------------------
{question}

-------------------------
INSTRUCTIONS
-------------------------
Answer the user's question using only the verified
medical document above.

If the document contains relevant recommendations,
follow-up instructions, precautions, medicines,
findings, or other information requested by the user,
explain exactly what is written in the document.

If the requested information is not present, say:

"I could not find this information in your uploaded document."

Do not invent information.
"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.2
        )

        answer = response.choices[0].message.content

        if not answer:
            return (
                "I could not generate an answer from "
                "your verified medical document."
            )

        return answer.strip()

    except Exception as error:

        print(
            "AI API ERROR:",
            repr(error)
        )

        return (
            "I am unable to generate the AI answer right now. "
            "Please check your API key, model name, internet "
            "connection, and backend terminal for the exact error."
        )