"""Assemble LLM prompts from all inputs."""

SYSTEM_PROMPT = """\
You are an expert resume writer with deep experience tailoring resumes to specific job postings.

Rules you must follow without exception:
- Output well-structured markdown. Use # for the candidate name, ## for section headers,
  ### for job/project titles, **bold** for company names and dates, and - for bullet points.
- Never invent facts, credentials, or experiences not present in the inputs.
- Select the 3 to 5 most relevant projects from the candidate projects provided.
- Preserve every non-project section from the base resume exactly (contact info, education,
  skills, certifications, etc.) — only the experience/projects section should be tailored.
- End your response with a SELECTION NOTES section explaining which projects you chose,
  which you excluded, and why.

Output format:
[Full markdown resume]

## SELECTION NOTES
[Your explanation of project selection and tailoring decisions]
"""


def build_prompt(base_resume_text: str | None, job_text: str, projects: list) -> tuple[str, str]:
    """Assemble (system_prompt, user_prompt) from all inputs.

    Returns a 2-tuple of strings ready to pass to an LLMProvider.
    """
    sections = []

    # --- Base resume ---
    if base_resume_text:
        sections.append(_section("BASE RESUME", base_resume_text))
    else:
        sections.append(
            "BASE RESUME\n"
            "-----------\n"
            "No base resume provided. Build the full resume from the candidate projects below,\n"
            "following a standard chronological format."
        )

    # --- Job posting ---
    sections.append(_section("JOB POSTING", job_text))

    # --- Candidate projects ---
    project_blocks = "\n\n".join(_format_project(p) for p in projects)
    sections.append(_section("CANDIDATE PROJECTS", project_blocks))

    # --- Tailoring instructions ---
    sections.append(
        "INSTRUCTIONS\n"
        "------------\n"
        "1. Keep all non-project sections from the base resume unchanged.\n"
        "2. Select the 3 to 5 projects that best match the job posting.\n"
        "3. Rewrite the project bullets to emphasize skills and impact relevant to this role.\n"
        "4. Do not add any experience, skills, or credentials not present in the inputs.\n"
        "5. After the resume, append a SELECTION NOTES section explaining your choices."
    )

    user_prompt = "\n\n" + "\n\n".join(sections) + "\n"
    return SYSTEM_PROMPT, user_prompt


def _section(title: str, content: str) -> str:
    divider = "-" * len(title)
    return f"{title}\n{divider}\n{content.strip()}"


def _format_project(p: dict) -> str:
    """Format a single project dict as labeled plain-text fields for the LLM."""
    lines = []
    lines.append(f"Project: {p.get('title', 'Untitled')}")

    if org := p.get("organization"):
        lines.append(f"Organization: {org}")

    if dates := p.get("dates"):
        start = dates.get("start", "")
        end = dates.get("end", "present")
        if start:
            lines.append(f"Dates: {start} to {end}")

    if role := p.get("role"):
        lines.append(f"Role: {role}")

    if summary := p.get("summary"):
        lines.append(f"Summary: {summary}")

    if desc := p.get("description_long"):
        lines.append(f"Details: {desc}")

    if skills := p.get("skills"):
        lines.append(f"Skills: {', '.join(skills)}")

    if impact := p.get("impact"):
        lines.append("Impact:")
        for item in impact:
            lines.append(f"  - {item}")

    if keywords := p.get("keywords"):
        lines.append(f"Keywords: {', '.join(keywords)}")

    if notes := p.get("notes"):
        lines.append(f"Notes: {notes}")

    return "\n".join(lines)
