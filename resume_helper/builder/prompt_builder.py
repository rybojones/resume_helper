"""Assemble LLM prompts from all inputs."""

SYSTEM_PROMPT = """\
You are an expert resume writer with deep experience tailoring resumes to specific job postings.

Rules you must follow without exception:
- Output well-structured markdown. Use # for the candidate name, #### for contact info, ## for section headers,
  ### for project titles, **bold** for company/school names and dates, and - for bullet points.
- Never invent facts, credentials, or experiences not present in the inputs.
- The resume contains two experience sections:
    - "Work Experience" — static. Reproduce it exactly, word for word. Do not add, remove,
      or rephrase any role, date, organisation, or Focus line.
    - "Project Experience" — dynamic. Replace the entire contents of this section with your
      4 to 7 project selections, tailored to the job posting. Don't include company name where work was done.
      Order projects from most relevant to least (using your discretion).
- For the Project Experience section, select ONLY from the CANDIDATE PROJECTS list provided.
  Do not source any project content from the BASE RESUME section.
- Keep all other sections (contact info, Education, Supporting Experience, etc.) verbatim.
- Format each selected project as:
    ### <Project Title>
    <One tailored paragraph drawing on the project details and impact, emphasising relevance
    to the job posting.>- Single paragraph per project and no impact bullet-points.
- End your response with a SELECTION NOTES section explaining which projects you chose,
  which you excluded, and why.

Stylistic rules:
- Don't use em-dashes, '-', when creating project text.
- Use horizontal rules, '---', before any H2 ('##') sections.
- Use a horizontal rule at the very end of the resume, if not already present.
- bold text for role and company, but not duration and location.

Output format:
COMPANY: <exact company name from the job posting>
ROLE: <exact job title from the job posting>
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
            "No base resume provided. Build the full resume from the candidate projects below.\n"
            "Use a ## Work Experience section (leave empty or omit) and a ## Project Experience\n"
            "section containing the selected projects in the format described."
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
        "1. Reproduce the Work Experience section exactly as it appears — every role, date, "
        "organisation, and Focus line verbatim.\n"
        "2. Replace the Project Experience section with 3 to 5 projects from CANDIDATE PROJECTS "
        "that best match the job posting. Select ONLY from CANDIDATE PROJECTS — never from BASE RESUME.\n"
        "3. Rewrite each selected project as: ### title, one tailored paragraph, \n"
        "4. Keep Education and Supporting Experience verbatim.\n"
        "5. Do not add any experience, skills, or credentials not present in the inputs.\n"
        "6. After the resume, append a SELECTION NOTES section explaining your choices."
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
