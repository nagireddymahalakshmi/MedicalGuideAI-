# MediGuide AI

MediGuide AI is an AI-powered medical document explanation prototype.

## Features

- Medical document upload
- Medical document text extraction
- RAG-based document retrieval
- AI question answering
- Basic safety checking
- Medication extraction
- Laboratory value extraction
- Medical document summarization
- Reminder generation

## Technology

- Python
- FastAPI
- OpenAI API
- Pydantic
- PyPDF
- RAG
- REST API

## Backend Structure

backend/
│
├── main.py
│
├── routes/
│   ├── upload.py
│   ├── verify.py
│   └── ask.py
│
├── services/
│   ├── ai.py
│   ├── rag.py
│   ├── safety.py
│   ├── medication.py
│   ├── lab_extraction.py
│   ├── summary.py
│   └── reminder.py
│
├── prompts/
│   ├── system_prompt.py
│   └── safety_prompt.py
│
├── models/
│   ├── schemas.py
│   └── response_models.py
│
├── tests/
│   ├── test_ai.py
│   ├── test_safety.py
│   ├── test_medication.py
│   └── test_rag.py
│
├── .env
├── requirements.txt
└── README.md

## Running the Backend

Install dependencies:

pip install -r requirements.txt

Run the server:

uvicorn main:app --reload

Then open:

http://127.0.0.1:8000/docs

## Safety

MediGuide AI is an educational prototype.

It does not diagnose medical conditions or prescribe treatment.
Important medical decisions should be made with a qualified healthcare
professional.