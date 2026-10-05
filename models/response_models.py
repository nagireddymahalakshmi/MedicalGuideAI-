from typing import List

from pydantic import BaseModel


class AskResponse(BaseModel):
    answer: str
    safety_level: str
    safety_notice: str
    sources: List[str] = []


class VerifyResponse(BaseModel):
    safe: bool
    level: str
    keywords: List[str]
    message: str


class UploadResponse(BaseModel):
    filename: str
    text: str
    character_count: int


class SummaryResponse(BaseModel):
    summary: str
    disclaimer: str


class ReminderResponse(BaseModel):
    medication: str
    dose: str
    reminder: str