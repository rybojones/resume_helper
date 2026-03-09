"""Assemble LLM prompts from all inputs."""


def build_prompt(
    base_resume_text: str | None,
    job_text: str,
    projects: list,
    system_prompt: str,
) -> tuple[str, str]:
    """Assemble (system_prompt, user_prompt) from all inputs.

    system_prompt is loaded from the active template's system_prompt.md.
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
            "No base resume provided. Build the full resume from the candidate projects below.\n"
            "Use a ## Work Experience section (leave empty or omit) and a ## Project Experience\n"
            "section containing the selected projects in the format described."
        )

    # --- Job posting ---
    sections.append(_section("JOB POSTING", job_text))

    # --- Candidate projects ---
    project_blocks = "\n\n".join(_format_project(p) for p in projects)
    sections.append(_section("CANDIDATE PROJECTS", project_blocks))

    user_prompt = "\n\n" + "\n\n".join(sections) + "\n"
    return system_prompt, user_prompt


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
