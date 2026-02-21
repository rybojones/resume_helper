"""Main orchestrator — no CLI concerns."""
import sys
from datetime import datetime
from pathlib import Path

from resume_helper.config import (
    DEFAULT_RESUME_PATH, DEFAULT_PROJECTS_PATH, OUTPUT_DIR,
    OUTPUT_DIR_MD, OUTPUT_DIR_DOCX, DEFAULT_REFERENCE_DOCX,
    UserPaths,
)
from resume_helper.output.md2docx import check_pandoc_installed, convert_markdown_to_docx
from resume_helper.parsers.pdf_parser import parse_pdf
from resume_helper.parsers.job_parser import parse_job_input
from resume_helper.data.projects_db import load_projects, filter_by_role_tag
from resume_helper.builder.prompt_builder import build_prompt
from resume_helper.output.formatter import format_and_write


def build_resume(
    resume_path: str | None,
    job_input: str,
    projects_path: str | None,
    role_tag: str | None,
    provider: str,
    output_path: str | None,
    reference_doc: str | None = None,
    user_paths: UserPaths | None = None,
) -> None:
    # --- Resolve defaults ---
    _p = user_paths
    resolved_resume   = Path(resume_path)   if resume_path   else (_p.resume    if _p else DEFAULT_RESUME_PATH)
    resolved_projects = Path(projects_path) if projects_path else (_p.projects  if _p else DEFAULT_PROJECTS_PATH)
    _out_md           = _p.output_dir_md   if _p else OUTPUT_DIR_MD
    _out_docx         = _p.output_dir_docx if _p else OUTPUT_DIR_DOCX

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

    # --- Pre-flight coverage check (advisory only) ---
    if base_resume_text:
        _preflight_coverage_check(base_resume_text, projects)

    # --- Build prompt ---
    system_prompt, user_prompt = build_prompt(base_resume_text, job_text, projects)

    # --- Select LLM provider ---
    llm = _get_provider(provider)
    print(f"[resume-helper] Calling {llm.get_model_name()}...", file=sys.stderr)

    # --- Call LLM ---
    raw_output = llm.complete(system_prompt, user_prompt)

    # --- Resolve output path ---
    resolved_output = _resolve_output_path(output_path, role_tag, _out_md)

    # --- Format and write ---
    result = format_and_write(raw_output, str(resolved_output))

    # --- Rename to company+role-based filename if auto-named ---
    if not output_path:
        resolved_output = _rename_with_metadata(resolved_output, result.company, result.role)

    # --- Convert to DOCX (soft failure) ---
    ref = Path(reference_doc) if reference_doc else DEFAULT_REFERENCE_DOCX
    _convert_to_docx(resolved_output, ref, _out_docx)


def _preflight_coverage_check(resume_text: str, projects: list) -> None:
    """Warn when none of the project organizations appear in the resume text.

    This is a lightweight heuristic: if projects.json has entries but none of their
    organization names are found in the resume, the DB likely doesn't cover this resume.
    Advisory only — build continues regardless.
    """
    orgs = [p.get("organization", "").strip() for p in projects if p.get("organization")]
    if not orgs:
        # No org data to compare — warn if projects list is also empty
        if not projects:
            print(
                "[resume-helper] WARNING: Some roles in your resume may not be represented in projects.json.\n"
                "[resume-helper] Run `python -m resume_helper.import_projects` to extract and import them.",
                file=sys.stderr,
            )
        return

    resume_lower = resume_text.lower()
    covered = any(org.lower() in resume_lower for org in orgs)
    if not covered:
        print(
            "[resume-helper] WARNING: Some roles in your resume may not be represented in projects.json.\n"
            "[resume-helper] Run `python -m resume_helper.import_projects` to extract and import them.",
            file=sys.stderr,
        )


def _slugify(text: str) -> str:
    """Return a lowercase, underscore-separated filesystem slug, capped at 40 chars."""
    import re as _re
    slug = _re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:40]


def _resolve_output_path(
    output_path: str | None,
    role_tag: str | None,
    output_dir_md: Path = OUTPUT_DIR_MD,
) -> Path:
    if output_path:
        return Path(output_path)
    datestamp = datetime.now().strftime("%Y%m%d")
    suffix = f"_{role_tag}" if role_tag else ""
    filename = f"resume{suffix}_{datestamp}.md"
    output_dir_md.mkdir(parents=True, exist_ok=True)
    return output_dir_md / filename


def _rename_with_metadata(current_path: Path, company: str, role: str) -> Path:
    """Rename the written file to include company and role slugs; return the new path."""
    datestamp = datetime.now().strftime("%Y%m%d")
    parts = [_slugify(company) if company else None, _slugify(role) if role else None]
    meta = "_".join(p for p in parts if p)
    new_name = f"resume_{meta}_{datestamp}.md" if meta else current_path.name
    new_path = current_path.parent / new_name
    if new_path != current_path:
        current_path.rename(new_path)
        print(f"[resume-helper] Resume renamed to: {new_path}", file=sys.stderr)
    return new_path


def _resolve_docx_path(md_path: Path, output_dir_docx: Path = OUTPUT_DIR_DOCX) -> Path:
    output_dir_docx.mkdir(parents=True, exist_ok=True)
    return output_dir_docx / md_path.with_suffix(".docx").name


def _convert_to_docx(md_path: Path, reference_doc: Path, output_dir_docx: Path = OUTPUT_DIR_DOCX) -> None:
    docx_path = _resolve_docx_path(md_path, output_dir_docx)
    ref = reference_doc if reference_doc.exists() else None
    try:
        check_pandoc_installed()
        convert_markdown_to_docx(str(md_path), str(docx_path), str(ref) if ref else None)
        print(f"[resume-helper] DOCX written to: {docx_path}", file=sys.stderr)
    except RuntimeError as exc:
        print(f"[resume-helper] WARNING: {exc} — skipping DOCX conversion.", file=sys.stderr)


def _get_provider(provider: str):
    if provider == "claude":
        from resume_helper.llm.claude_provider import ClaudeProvider
        return ClaudeProvider()
    if provider == "openai":
        from resume_helper.llm.openai_provider import OpenAIProvider
        return OpenAIProvider()
    if provider == "gemini":
        from resume_helper.llm.gemini_provider import GeminiProvider
        return GeminiProvider()
    print(f"[resume-helper] ERROR: Provider '{provider}' is not yet implemented.", file=sys.stderr)
    sys.exit(1)
