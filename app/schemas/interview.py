from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.simplify import UserProfile


class InterviewQuestionItem(BaseModel):
    question_ro: str
    why_asked_ro: str
    suggested_approach_ro: str


class InterviewAdjustmentItem(BaseModel):
    id: str
    title: str
    talking_point_ro: str


class InterviewPrepData(BaseModel):
    overview_ro: str
    common_questions: list[InterviewQuestionItem] = Field(default_factory=list)
    suggested_adjustments: list[InterviewAdjustmentItem] = Field(default_factory=list)
    questions_to_ask_employer: list[str] = Field(default_factory=list)


class InterviewPrepRequest(BaseModel):
    job_title: str = Field(default="")
    job_description: str = Field(default="")
    profile: Optional[UserProfile] = Field(default_factory=UserProfile)
