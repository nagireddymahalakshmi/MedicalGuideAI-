from typing import List, Optional
from pydantic import BaseModel, Field


class AskMessage(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str
    document_text: str = ""
    history: List[AskMessage] = Field(default_factory=list)


class VerifyRequest(BaseModel):
    text: str


class TextRequest(BaseModel):
    text: str