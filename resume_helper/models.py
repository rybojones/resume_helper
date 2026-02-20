"""Pydantic models — single source of truth for project and resume output schemas."""
from pydantic import BaseModel, field_validator

ROLE_TAGS = [
    "data_scientist",
    "machine_learning_engineer",
    "analytics_engineer",
    "ai_engineer",
    "data_analyst",
    "data_engineer",
]


class ProjectRecord(BaseModel):
    # Required fields
    id: str = ""
    title: str
    summary: str
    skills: list[str]
    role_tags: list[str]
    impact: list[str]
    # Optional with defaults
    organization: str = ""
    role: str = ""
    dates: dict = {}
    description_long: str = ""
    keywords: list[str] = []
    include_by_default: bool = False
    notes: str = ""

    @field_validator("role_tags")
    @classmethod
    def role_tags_must_be_valid(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("role_tags must be non-empty")
        invalid = set(v) - set(ROLE_TAGS)
        if invalid:
            raise ValueError(
                f"Invalid role_tags: {sorted(invalid)}. Must be a subset of: {ROLE_TAGS}"
            )
        return v


class ProjectsFile(BaseModel):
    projects: list[ProjectRecord]


class ResumeOutput(BaseModel):
    resume_markdown: str
    selection_notes: str = ""

    @field_validator("resume_markdown")
    @classmethod
    def must_contain_required_sections(cls, v: str) -> str:
        missing = []
        if "Work Experience" not in v:
            missing.append("Work Experience")
        if "Project Experience" not in v:
            missing.append("Project Experience")
        if missing:
            raise ValueError(
                f"resume_markdown is missing required sections: {missing}"
            )
        return v
