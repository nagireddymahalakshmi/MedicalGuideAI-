from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from routes import upload
from routes import ask

from pypdf import PdfReader
from io import BytesIO
import re
import os

import pytesseract
from PIL import Image
import pymupdf

from database import save_report, get_latest_report


# =========================================================
# TESSERACT CONFIGURATION
# =========================================================

import shutil

tesseract_path = shutil.which("tesseract")

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="MediGuide AI",
    description="Medical document understanding system",
    version="1.2.0"
)


# =========================================================
# ROUTERS
# =========================================================

app.include_router(upload.router)
app.include_router(ask.router)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# BASIC ROUTES
# =========================================================

@app.get("/")
def root():
    return {
        "message": "MediGuide AI backend is running",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================================================
# MEDICAL DOCUMENT VALIDATION
# =========================================================

DOCUMENT_KEYWORDS = {

    "prescription": [
        "prescription",
        "rx",
        "medicine",
        "medication",
        "tablet",
        "capsule",
        "syrup",
        "injection",
        "dosage",
        "dose",
        "frequency",
        "refill",
        "pharmacy",
        "prescribed",
        "doctor",
        "physician",
        "mg",
        "mcg",
        "ml"
    ],

    "lab_report": [
        "lab report",
        "laboratory",
        "laboratory report",
        "blood test",
        "urine test",
        "test result",
        "reference range",
        "reference interval",
        "hemoglobin",
        "haemoglobin",
        "glucose",
        "creatinine",
        "cholesterol",
        "platelet",
        "wbc",
        "rbc",
        "patient",
        "result"
    ],

    "discharge_summary": [
        "discharge summary",
        "discharge",
        "admission",
        "hospital",
        "hospitalization",
        "clinical",
        "medical history",
        "treatment",
        "diagnosis",
        "consultation",
        "patient information",
        "follow up",
        "follow-up",
        "discharge date"
    ]
}


def classify_medical_document(text: str):

    clean_text = re.sub(
        r"\s+",
        " ",
        text.lower()
    ).strip()

    if len(clean_text) < 15:

        return {
            "is_medical": False,
            "document_type": "unknown",
            "confidence": 0,
            "matched_keywords": [],
            "message": (
                "❌ Wrong document. "
                "No sufficient readable medical text was detected. "
                "Please upload a clear Prescription, Lab Report, "
                "or Discharge Summary."
            )
        }

    scores = {}

    for document_type, keywords in DOCUMENT_KEYWORDS.items():

        matched = []

        for keyword in keywords:

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(keyword.lower())
                + r"(?![a-z0-9])"
            )

            if re.search(
                pattern,
                clean_text
            ):
                matched.append(keyword)

        scores[document_type] = matched

    best_type = max(
        scores,
        key=lambda item: len(scores[item])
    )

    matched = scores[best_type]

    MIN_MEDICAL_KEYWORDS = 3

    if len(matched) < MIN_MEDICAL_KEYWORDS:

        return {
            "is_medical": False,
            "document_type": "unknown",
            "confidence": len(matched),
            "matched_keywords": matched,
            "message": (
                "❌ WRONG DOCUMENT\n\n"
                "This image does not appear to be "
                "a supported medical document.\n\n"
                "Please upload one of these:\n"
                "• Prescription\n"
                "• Lab Report\n"
                "• Discharge Summary"
            )
        }

    return {
        "is_medical": True,
        "document_type": best_type,
        "confidence": len(matched),
        "matched_keywords": matched,
        "message": (
            "Medical document detected: "
            + best_type.replace("_", " ").title()
        )
    }


# =========================================================
# MEDICAL KEYWORDS
# =========================================================

MEDICAL_KEYWORDS = sorted({
    keyword
    for keywords in DOCUMENT_KEYWORDS.values()
    for keyword in keywords
})


def get_medical_keywords(text):

    text_lower = text.lower()

    return [
        keyword
        for keyword in MEDICAL_KEYWORDS
        if keyword.lower() in text_lower
    ]


# =========================================================
# PATIENT INFORMATION
# =========================================================

def extract_patient_information(text):

    information = {
        "name": "Not available",
        "age": "Not available",
        "gender": "Not available",
        "date": "Not available"
    }

    patterns = {

        "name": [
            r"patient\s*name\s*[:\-]\s*([^\n]+)",
            r"name\s*[:\-]\s*([^\n]+)",
            r"patient\s*[:\-]\s*([^\n]+)"
        ],

        "age": [
            r"age\s*[:\-]\s*(\d{1,3})",
            r"(\d{1,3})\s*(?:years|yrs|year)\s*old"
        ],

        "gender": [
            r"gender\s*[:\-]\s*([^\n]+)",
            r"sex\s*[:\-]\s*([^\n]+)"
        ],

        "date": [
            r"date\s*[:\-]\s*([^\n]+)",
            r"report\s*date\s*[:\-]\s*([^\n]+)",
            r"date\s+of\s+report\s*[:\-]\s*([^\n]+)"
        ]
    }

    for key, pattern_list in patterns.items():

        for pattern in pattern_list:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE
            )

            if match:

                value = match.group(1).strip()

                if value:
                    information[key] = value
                    break

    return information


# =========================================================
# LAB TESTS
# =========================================================

LAB_TESTS = [
    "hemoglobin",
    "haemoglobin",
    "hb",
    "wbc",
    "white blood cell",
    "rbc",
    "red blood cell",
    "platelet",
    "platelets",
    "glucose",
    "blood sugar",
    "fasting blood sugar",
    "postprandial blood sugar",
    "hba1c",
    "cholesterol",
    "total cholesterol",
    "hdl",
    "ldl",
    "triglycerides",
    "creatinine",
    "urea",
    "uric acid",
    "bilirubin",
    "albumin",
    "protein",
    "sodium",
    "potassium",
    "calcium",
    "vitamin d",
    "vitamin b12",
    "tsh",
    "t3",
    "t4",
    "esr",
    "crp",
    "sgot",
    "ast",
    "sgpt",
    "alt",
    "blood pressure",
    "temperature",
    "oxygen saturation",
    "spo2"
]


def extract_lab_values(text):

    results = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        lower_line = line.lower()

        matched_test = None

        for test in LAB_TESTS:

            if test in lower_line:

                matched_test = test
                break

        if not matched_test:
            continue

        number_match = re.search(
            r"\b\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?\b",
            line
        )

        if number_match:

            value = number_match.group(0)

            results.append({
                "test": line,
                "value": value
            })

    return results


# =========================================================
# MEDICATION EXTRACTION
# =========================================================

def extract_medications(text):

    medicines = []

    medicine_keywords = [
        "tablet",
        "tab ",
        "capsule",
        "cap ",
        "syrup",
        "injection",
        "medicine",
        "medication",
        " mg",
        "mg ",
        " mcg",
        "mcg ",
        " ml",
        "ml "
    ]

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        lower_line = line.lower()

        if any(
            keyword in lower_line
            for keyword in medicine_keywords
        ):

            if len(line) < 250:
                medicines.append(line)

    unique_medicines = []

    for medicine in medicines:

        if medicine not in unique_medicines:
            unique_medicines.append(medicine)

    return unique_medicines[:20]


# =========================================================
# SECTION EXTRACTION
# =========================================================

def extract_section(text, keywords):

    lines = text.splitlines()

    for index, line in enumerate(lines):

        lower_line = line.lower().strip()

        for keyword in keywords:

            if keyword in lower_line:

                section = lines[
                    index:index + 8
                ]

                cleaned = []

                for item in section:

                    item = item.strip()

                    if item:
                        cleaned.append(item)

                return "\n".join(cleaned)

    return "Not available"


# =========================================================
# DIAGNOSIS / IMPRESSION
# =========================================================

def extract_diagnosis_or_impression(text):

    lines = text.splitlines()

    headings = [
        "diagnosis",
        "diagnoses",
        "diagnostic impression",
        "impression",
        "final impression",
        "clinical impression",
        "assessment"
    ]

    for index, line in enumerate(lines):

        clean_line = line.strip()
        lower_line = clean_line.lower()

        for heading in headings:

            if heading in lower_line:

                same_line = re.split(
                    r"[:\-]",
                    clean_line,
                    maxsplit=1
                )

                if len(same_line) == 2:

                    value = same_line[1].strip()

                    if value:
                        return value

                following_lines = []

                for next_line in lines[
                    index + 1:index + 5
                ]:

                    next_line = next_line.strip()

                    if next_line:
                        following_lines.append(
                            next_line
                        )

                if following_lines:

                    return "\n".join(
                        following_lines
                    )

    return "Not available"


# =========================================================
# STRUCTURED REPORT
# =========================================================

def create_structured_report(text):

    patient = extract_patient_information(text)

    labs = extract_lab_values(text)

    medicines = extract_medications(text)

    findings = extract_section(
        text,
        [
            "findings",
            "clinical findings"
        ]
    )

    diagnosis = extract_diagnosis_or_impression(
        text
    )

    recommendations = extract_section(
        text,
        [
            "recommendation",
            "recommendations",
            "treatment plan",
            "plan"
        ]
    )

    return {
        "patient_information": patient,
        "lab_values": labs,
        "medications": medicines,
        "important_findings": findings,
        "diagnosis_or_impression": diagnosis,
        "recommendations": recommendations
    }


# =========================================================
# IMAGE OCR
# =========================================================

def extract_image_text(content):

    image = Image.open(
        BytesIO(content)
    )

    image = image.convert(
        "RGB"
    )

    width, height = image.size

    if width < 1200:

        scale = 1200 / width

        image = image.resize(
            (
                int(width * scale),
                int(height * scale)
            )
        )

    extracted_text = pytesseract.image_to_string(
        image,
        config="--psm 6"
    )

    return extracted_text.strip()


# =========================================================
# PDF TEXT EXTRACTION + OCR
# =========================================================

def extract_pdf_text(content):

    extracted_text = ""

    try:

        reader = PdfReader(
            BytesIO(content)
        )

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                extracted_text += (
                    page_text + "\n"
                )

    except Exception as error:

        print(
            "PDF TEXT EXTRACTION ERROR:",
            repr(error)
        )

        extracted_text = ""

    # -----------------------------------------------------
    # OCR PDF IF NORMAL TEXT EXTRACTION FAILED
    # -----------------------------------------------------

    if not extracted_text.strip():

        pdf = pymupdf.open(
            stream=content,
            filetype="pdf"
        )

        try:

            for page in pdf:

                pix = page.get_pixmap(
                    matrix=pymupdf.Matrix(
                        2,
                        2
                    )
                )

                image_bytes = pix.tobytes(
                    "png"
                )

                image = Image.open(
                    BytesIO(image_bytes)
                )

                image = image.convert(
                    "RGB"
                )

                page_text = pytesseract.image_to_string(
                    image,
                    config="--psm 6"
                )

                extracted_text += (
                    page_text + "\n"
                )

        finally:

            pdf.close()

    return extracted_text.strip()


# =========================================================
# DOCUMENT OCR
# =========================================================

def extract_text_from_document(
    content,
    content_type,
    filename
):

    extension = os.path.splitext(
        filename.lower()
    )[1]

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    if (
        content_type in [
            "image/jpeg",
            "image/jpg",
            "image/png"
        ]
        or extension in [
            ".jpg",
            ".jpeg",
            ".png"
        ]
    ):

        return extract_image_text(
            content
        )

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    if (
        content_type == "application/pdf"
        or extension == ".pdf"
    ):

        return extract_pdf_text(
            content
        )

    raise HTTPException(
        status_code=400,
        detail=(
            "Unsupported file type. "
            "Please upload JPG, JPEG, PNG, or PDF."
        )
    )


# =========================================================
# UPLOAD REPORT
# =========================================================

@app.post("/upload-report")
async def upload_report(
    file: UploadFile = File(...)
):

    print(
        f"UPLOAD REQUEST: "
        f"name={file.filename}, "
        f"type={file.content_type}"
    )

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename received."
        )

    filename = file.filename.lower()

    allowed_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".pdf"
    ]

    extension = os.path.splitext(
        filename
    )[1]

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                "Please upload a JPG, JPEG, PNG, "
                "or PDF medical document."
            )
        )

    content = await file.read()

    print(
        f"FILE RECEIVED: "
        f"{len(content)} bytes"
    )

    if len(content) == 0:

        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty."
        )

    try:

        print("OCR STARTED...")

        extracted_text = extract_text_from_document(
            content,
            file.content_type or "",
            file.filename
        )

        print(
            f"OCR COMPLETE: "
            f"{len(extracted_text)} characters"
        )

        # -------------------------------------------------
        # NO TEXT DETECTED
        # -------------------------------------------------

        if not extracted_text.strip():

            print("DOCUMENT REJECTED: NO TEXT")

            return {
                "status": "rejected",
                "valid_document": False,
                "verified": False,
                "ocr_verified": False,
                "filename": file.filename,
                "document_type": "unknown",
                "message": (
                    "❌ WRONG DOCUMENT\n\n"
                    "No readable text was detected.\n\n"
                    "Please upload a clear:\n"
                    "• Prescription\n"
                    "• Lab Report\n"
                    "• Discharge Summary"
                ),
                "matched_keywords": [],
                "extracted_text": ""
            }

        # -------------------------------------------------
        # MEDICAL DOCUMENT VALIDATION
        # -------------------------------------------------

        validation = classify_medical_document(
            extracted_text
        )

        # -------------------------------------------------
        # WRONG DOCUMENT
        # -------------------------------------------------

        if not validation["is_medical"]:

            print(
                "DOCUMENT REJECTED:",
                validation["message"]
            )

            return {
                "status": "rejected",
                "valid_document": False,
                "verified": False,
                "ocr_verified": False,
                "filename": file.filename,
                "document_type": "unknown",
                "confidence": validation[
                    "confidence"
                ],
                "message": validation[
                    "message"
                ],
                "matched_keywords": validation[
                    "matched_keywords"
                ],
                "extracted_text": extracted_text
            }

        # -------------------------------------------------
        # VALID MEDICAL DOCUMENT
        # -------------------------------------------------

        matched_keywords = get_medical_keywords(
            extracted_text
        )

        structured_report = (
            create_structured_report(
                extracted_text
            )
        )

        print(
            "MEDICAL DOCUMENT ACCEPTED:",
            validation["document_type"]
        )

        return {
            "status": "success",
            "valid_document": True,
            "filename": file.filename,
            "message": (
                "Medical document uploaded successfully. "
                "Please verify the extracted text."
            ),
            "verified": False,
            "ocr_verified": False,
            "document_type": validation[
                "document_type"
            ],
            "confidence": validation[
                "confidence"
            ],
            "matched_keywords": matched_keywords,
            "extracted_text": extracted_text,
            "structured_report": structured_report
        }

    except HTTPException:
        raise

    except Exception as error:

        print(
            "UPLOAD ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Error processing the uploaded file: "
                + str(error)
            )
        )


# =========================================================
# VERIFY REQUEST
# =========================================================

class VerifyRequest(BaseModel):

    extracted_text: str

    filename: str = "verified_medical_report"


# =========================================================
# VERIFY + SAVE
# =========================================================

@app.post("/verify/")
def verify_report(
    request: VerifyRequest
):

    text = request.extracted_text.strip()

    if not text:

        raise HTTPException(
            status_code=400,
            detail="No text was provided."
        )

    validation = classify_medical_document(
        text
    )

    if not validation["is_medical"]:

        return {
            "status": "rejected",
            "verified": False,
            "ocr_verified": False,
            "message": (
                "❌ The corrected text still does not "
                "appear to be a supported medical document. "
                "Please verify the original document."
            ),
            "document_type": "unknown",
            "matched_keywords": validation[
                "matched_keywords"
            ],
            "extracted_text": text
        }

    matched_keywords = get_medical_keywords(
        text
    )

    structured_report = create_structured_report(
        text
    )

    # -----------------------------------------------------
    # SAVE TO SQLITE DATABASE
    # -----------------------------------------------------

    save_report(
        request.filename,
        text
    )

    return {
        "status": "success",
        "verified": True,
        "ocr_verified": True,
        "message": (
            "Verified medical document "
            "saved successfully."
        ),
        "filename": request.filename,
        "document_type": validation[
            "document_type"
        ],
        "matched_keywords": matched_keywords,
        "extracted_text": text,
        "structured_report": structured_report
    }


# =========================================================
# GET CURRENT VERIFIED REPORT
# =========================================================

def get_current_report():

    latest_report = get_latest_report()

    if not latest_report:

        raise HTTPException(
            status_code=400,
            detail=(
                "Please upload and verify "
                "a medical report first."
            )
        )

    try:

        filename = latest_report[0]

        extracted_text = latest_report[1]

    except Exception:

        raise HTTPException(
            status_code=500,
            detail=(
                "Invalid database record format."
            )
        )

    return (
        filename,
        extracted_text
    )


# =========================================================
# EXPLAIN DOCUMENT
# =========================================================

class ExplainRequest(BaseModel):

    context: str = ""


@app.post("/explain/")
def explain_report(
    request: ExplainRequest
):

    try:

        filename, verified_text = (
            get_current_report()
        )

        # -------------------------------------------------
        # CURRENTLY USES AI SERVICE
        # -------------------------------------------------

        from services.ai import generate_answer

        question = """

Explain the uploaded medical document
in very simple patient-friendly language.

IMPORTANT SAFETY RULES:

1. Use ONLY information present in the
   uploaded verified document.

2. Do NOT create a new diagnosis.

3. If the document contains a diagnosis
   or impression, report it only as information
   written in the document.

4. Do NOT invent medical information.

5. Do NOT recommend medicines.

6. Do NOT recommend changing medicine doses.

7. Do NOT declare that a laboratory result
   is normal or abnormal.

8. Explain medical terms in simple language
   only when the terms appear in the document.

9. If information is not present in the
   document, say:

"I could not find this information in
your uploaded document."

Organize the answer into:

1. What this report is about
2. Important findings
3. Test results
4. Diagnosis / Impression written in the document
5. Medical terms explained simply
6. Recommendations written in the document

"""

        answer = generate_answer(
            question=question,
            context=verified_text
        )

        return {
            "status": "success",
            "filename": filename,
            "explanation": answer
        }

    except HTTPException:
        raise

    except Exception as error:

        print(
            "EXPLAIN ERROR:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Error explaining document: "
                + str(error)
            )
        )


# =========================================================
# LAB VALUES
# =========================================================

@app.post("/lab-values/")
def lab_values(
    request: ExplainRequest
):

    try:

        filename, verified_text = (
            get_current_report()
        )

        values = extract_lab_values(
            verified_text
        )

        return {
            "status": "success",
            "filename": filename,
            "lab_values": values
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error extracting lab values: "
                + str(error)
            )
        )


# =========================================================
# MEDICATIONS
# =========================================================

@app.post("/medications/")
def medications(
    request: ExplainRequest
):

    try:

        filename, verified_text = (
            get_current_report()
        )

        medicines = extract_medications(
            verified_text
        )

        return {
            "status": "success",
            "filename": filename,
            "medications": medicines
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error extracting medications: "
                + str(error)
            )
        )


# =========================================================
# CURRENT REPORT
# =========================================================

@app.get("/current-report/")
def current_report():

    try:

        filename, verified_text = (
            get_current_report()
        )

        structured_report = (
            create_structured_report(
                verified_text
            )
        )

        return {
            "status": "success",
            "filename": filename,
            "verified": True,
            "extracted_text": verified_text,
            "structured_report": structured_report
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Error loading current report: "
                + str(error)
            )
        )


# =========================================================
# STARTUP MESSAGE
# =========================================================

@app.on_event("startup")
def startup_message():

    print("=" * 60)
    print("MediGuide AI Backend Started")
    print("Local chatbot router enabled")
    print("OpenAPI docs: http://127.0.0.1:8000/docs")
    print("=" * 60)
