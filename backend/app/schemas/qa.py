"""QA Judge contract shapes — mirrors lib/types.ts QAReview / QACriterionEvidence."""

from datetime import datetime

from pydantic import BaseModel, Field


class QACriterionEvidenceOut(BaseModel):
    criterion: str
    check_type: str
    passed: bool
    detail: str | None = None


class QAReviewOut(BaseModel):
    id: str
    submission_id: str
    task_id: str
    result: str  # pass | fail
    score: float
    confidence: float
    feedback: str
    evidence: list[QACriterionEvidenceOut] = Field(default_factory=list)
    reviewed_by: str  # "ai" | user id
    created_at: datetime


class QAProposalOut(BaseModel):
    """AI proposal payload (no persistence ids) — Spine decides qa_pass / qa_fail."""

    result: str
    score: float
    confidence: float
    feedback: str
    evidence: list[QACriterionEvidenceOut] = Field(default_factory=list)
    action: str = "approve"  # approve | escalate
    source: str = "fixture"  # gemini | fixture
