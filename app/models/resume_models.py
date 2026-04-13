from pydantic import BaseModel
from typing import Optional, List


class ResumeContact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None


class ResumeSection(BaseModel):
    heading: str
    content: str


class ParsedResume(BaseModel):
    raw_text: str
    file_type: str = "unknown"
    contact: ResumeContact = ResumeContact()
    summary: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[str] = None
    education: Optional[str] = None
    certifications: Optional[str] = None
    languages: Optional[str] = None
    sections: List[ResumeSection] = []
