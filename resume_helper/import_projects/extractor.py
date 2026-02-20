"""Extract structured project records from resume text using an LLM."""
from resume_helper.models import ROLE_TAGS, ProjectRecord

_SYSTEM_PROMPT = """\
You are a resume parser. Your job is to extract every distinct work experience and project \
from the resume text provided.

Each record must include:
  Required:
    - "title": string — short descriptive name for the project or role (e.g. "Churn Prediction Model")
    - "summary": string — 1-2 sentence summary of the work
    - "skills": array of strings — tech stack and tools used
    - "role_tags": array of strings — one or more tags from this exact list:
        {role_tags}
      Assign all tags that apply. Every record must have at least one.
    - "impact": array of strings — measurable outcomes or achievements (use exact numbers from the resume)

  Optional (include if inferable from the resume):
    - "organization": string — employer or client name
    - "role": string — the candidate's job title for this work
    - "dates": object with "start" and "end" string fields (YYYY-MM format, e.g. "2022-06")
    - "description_long": string — full context paragraph for the LLM to draw tailored bullets from
    - "keywords": array of strings — domain keywords useful for resume matching
    - "notes": string — any other context worth preserving

Rules:
- Never invent facts. Only use information present in the resume.
- One record per distinct project or job. If a job had multiple projects, create one record per project.
- "impact" bullets must be concrete — skip vague statements like "improved performance".
""".format(role_tags=", ".join(ROLE_TAGS))


def extract_projects(resume_text: str, llm) -> list[ProjectRecord]:
    """Prompt the LLM to parse resume_text and return a validated list of ProjectRecords."""
    return llm.complete_structured(_SYSTEM_PROMPT, resume_text, ProjectRecord)
