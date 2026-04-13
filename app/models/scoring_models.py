from pydantic import BaseModel
from typing import List, Optional


class CategoryScore(BaseModel):
    name: str
    score: float
    weight: float
    strengths: List[str] = []
    issues: List[str] = []


class ScoringResult(BaseModel):
    total_score: float
    categories: List[CategoryScore] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[str] = []


class KeywordMatchResult(BaseModel):
    matched_keywords: List[str] = []
    missing_keywords: List[str] = []
    critical_missing: List[str] = []
    score: float = 0.0


class FormattingResult(BaseModel):
    score: float = 0.0
    warnings: List[str] = []
    recommendations: List[str] = []
