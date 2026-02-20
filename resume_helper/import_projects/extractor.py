"""Extract structured project records from resume text using an LLM."""
import json

from resume_helper.data.projects_db import ROLE_TAGS

_SYSTEM_PROMPT = """\
You are a resume parser. Your job is to extract every distinct work experience and project \
from the resume text provided and return them as a JSON array.

Output ONLY a raw JSON array — no prose, no markdown, no code fences. \
If you cannot extract any projects, output an empty array: []

Each element of the array must be a JSON object with these fields:
  Required:
    - "title": string — short descriptive name for the project or role (e.g. "Churn Prediction Model")
    - "summary": string — 1-2 sentence summary of the work
    - "skills": array of strings — tech stack and tools used
    - "role_tags": array of strings — one or more tags from this exact list:
        {role_tags}
      Assign all tags that apply. Every object must have at least one.
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
- One object per distinct project or job. If a job had multiple projects, create one object per project.
- "impact" bullets must be concrete — skip vague statements like "improved performance".
""".format(role_tags=", ".join(ROLE_TAGS))


def extract_projects(resume_text: str, llm) -> list[dict]:
    """Prompt the LLM to parse resume_text and return a list of project dicts.

    Raises ValueError if the LLM response cannot be parsed as a JSON array.
    """
    raw = llm.complete(_SYSTEM_PROMPT, resume_text)
    cleaned = _strip_code_fences(raw.strip())

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM response was not valid JSON.\n"
            f"Response (first 500 chars): {raw[:500]}\n"
            f"Parse error: {exc}"
        ) from exc

    if not isinstance(result, list):
        raise ValueError(
            f"Expected a JSON array from the LLM but got {type(result).__name__}."
        )

    return result


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences if the LLM added them despite instructions."""
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first line (```json or ```) and last line (```)
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        return "\n".join(inner)
    return text
