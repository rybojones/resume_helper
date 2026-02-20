"""LLM-based coverage check: identify resume work experience not captured in projects.json."""

_SYSTEM_PROMPT = """\
You are a resume coverage auditor.

You will be given:
1. A resume (full text)
2. A list of projects already captured in a database (title and organization)

Your task: identify any distinct work experience or project in the resume that does NOT \
appear to be represented in the database list. Consider semantic similarity — the same \
work may be described with slightly different wording or project names.

Output rules:
- If all experience is represented, output exactly: NONE
- Otherwise, output a plain-text bullet list of gaps, one per line, starting with "- ".
  Each bullet should name the role/project and employer as they appear in the resume.
- No prose introduction or conclusion. Bullets or NONE only.
"""


def check_coverage(resume_text: str, merged_projects: list, llm) -> list[str]:
    """Return a list of gap descriptions, or an empty list if fully covered.

    Each string in the returned list is a plain-text description of a resume
    experience not found in merged_projects.
    """
    db_summary = _format_db_summary(merged_projects)
    user_prompt = (
        f"RESUME\n------\n{resume_text.strip()}\n\n"
        f"DATABASE PROJECTS\n-----------------\n{db_summary}"
    )

    raw = llm.complete(_SYSTEM_PROMPT, user_prompt).strip()

    if raw.upper() == "NONE" or not raw:
        return []

    gaps = [
        line.lstrip("- ").strip()
        for line in raw.splitlines()
        if line.strip().startswith("-")
    ]
    return gaps


def _format_db_summary(projects: list) -> str:
    lines = []
    for p in projects:
        title = p.get("title", "Untitled")
        org = p.get("organization", "")
        lines.append(f"- {title}" + (f" ({org})" if org else ""))
    return "\n".join(lines) if lines else "(empty)"
