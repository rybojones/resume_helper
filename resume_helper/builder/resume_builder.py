"""Main orchestrator — no CLI concerns."""
import sys
from pathlib import Path

from resume_helper.config import DEFAULT_RESUME_PATH, DEFAULT_PROJECTS_PATH
from resume_helper.parsers.pdf_parser import parse_pdf
from resume_helper.parsers.job_parser import parse_job_input
from resume_helper.data.projects_db import load_projects, filter_by_role_tag
from resume_helper.builder.prompt_builder import build_prompt


def build_resume(
    resume_path: str | None,
    job_input: str,
    projects_path: str | None,
    role_tag: str | None,
    provider: str,
    output_path: str | None,
) -> None:
    # --- Resolve defaults ---
    resolved_resume = Path(resume_path) if resume_path else DEFAULT_RESUME_PATH
    resolved_projects = Path(projects_path) if projects_path else DEFAULT_PROJECTS_PATH

    # --- Parse base resume (optional) ---
    if resolved_resume.exists():
        print(f"[resume-helper] Parsing resume: {resolved_resume}", file=sys.stderr)
        base_resume_text = parse_pdf(str(resolved_resume))
    else:
        if resume_path:
            # Explicit path was given but not found — hard error
            print(f"[resume-helper] ERROR: Resume not found: {resolved_resume}", file=sys.stderr)
            sys.exit(1)
        # Default path missing — soft fallback, LLM builds from projects
        print(
            f"[resume-helper] No resume found at default path ({resolved_resume}), "
            "building from projects only.",
            file=sys.stderr,
        )
        base_resume_text = None

    # --- Parse job posting ---
    print("[resume-helper] Fetching job posting...", file=sys.stderr)
    job_text = parse_job_input(job_input)

    # --- Load and filter projects ---
    print(f"[resume-helper] Loading projects: {resolved_projects}", file=sys.stderr)
    projects = load_projects(str(resolved_projects))
    if role_tag:
        projects = filter_by_role_tag(projects, role_tag)
        print(f"[resume-helper] Filtered to {len(projects)} project(s) for role: {role_tag}", file=sys.stderr)

    # --- Build prompt ---
    system_prompt, user_prompt = build_prompt(base_resume_text, job_text, projects)

    # --- Select LLM provider ---
    llm = _get_provider(provider)
    print(f"[resume-helper] Calling {llm.get_model_name()}...", file=sys.stderr)

    # --- Call LLM ---
    raw_output = llm.complete(system_prompt, user_prompt)

    # Print raw output to stdout for inspection (formatter strips and writes file in step 8)
    print(raw_output)


def _get_provider(provider: str):
    if provider == "claude":
        from resume_helper.llm.claude_provider import ClaudeProvider
        return ClaudeProvider()
    print(f"[resume-helper] ERROR: Provider '{provider}' is not yet implemented.", file=sys.stderr)
    sys.exit(1)
