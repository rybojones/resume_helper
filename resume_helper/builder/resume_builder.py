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
    if not job_text.strip():
        print(
            "[resume-helper] ERROR: Could not extract job posting content from the provided URL.\n"
            "[resume-helper] Try pasting the job description as raw text instead.",
            file=sys.stderr,
        )
        sys.exit(1)

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

    # --- Validate job content sentinel ---
    if raw_output.strip().startswith("JOB_CONTENT_ERROR:"):
        reason = raw_output.strip().removeprefix("JOB_CONTENT_ERROR:").strip()
        print(f"[resume-helper] ERROR: Job posting content is insufficient — {reason}", file=sys.stderr)
        print("[resume-helper] Try pasting the job description as raw text instead.", file=sys.stderr)
        sys.exit(1)

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


def _extract_project_titles(resume_text: str) -> list[str]:
    """Return candidate project titles from the 'Project Experience' section of a resume.

    Finds the section, cuts off at the next major heading, then returns short standalone
    lines (< 70 chars, 2+ words, not ending in punctuation) as candidate titles.
    """
    import re
    # Find the start of 'Project Experience'
    section_match = re.search(r"(?im)^project experience\s*$", resume_text)
    if not section_match:
        return []

    section_text = resume_text[section_match.end():]

    # Cut off at the next major section heading (Education, Supporting Experience, Work Experience, etc.)
    next_section = re.search(
        r"(?im)^(education|supporting experience|work experience|skills|certifications|awards|publications)\s*$",
        section_text,
    )
    if next_section:
        section_text = section_text[: next_section.start()]

    titles = []
    for line in section_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip lines that are too long, single words, or look like body text (end in . , :)
        if len(line) >= 70:
            continue
        if line[-1] in ".,:":
            continue
        words = line.split()
        if len(words) < 2:
            continue
        titles.append(line)
    return titles


def _preflight_coverage_check(resume_text: str, projects: list) -> None:
    """Warn when resume projects are absent from projects.json.

    Extracts project titles from the resume's 'Project Experience' section and
    checks each against the titles in projects.json (case-insensitive substring
    match). Prints an itemised warning for any uncovered titles.
    Advisory only — build continues regardless.
    """
    if not projects:
        print(
            "[resume-helper] WARNING: projects.json is empty — no projects will be selected.\n"
            "[resume-helper] Run `resume-helper-import-projects` to add projects.",
            file=sys.stderr,
        )
        return

    resume_titles = _extract_project_titles(resume_text)
    if not resume_titles:
        # Can't parse section — skip silently
        return

    db_titles = [p.get("title", "").lower() for p in projects]

    uncovered = []
    for title in resume_titles:
        title_lower = title.lower()
        if not any(title_lower in db_t or db_t in title_lower for db_t in db_titles):
            uncovered.append(title)

    if uncovered:
        print(
            f"[resume-helper] WARNING: {len(uncovered)} project(s) in your resume are not in "
            "projects.json and will not be used:",
            file=sys.stderr,
        )
        for t in uncovered:
            print(f'[resume-helper]   - "{t}"', file=sys.stderr)
        print(
            "[resume-helper] Run `resume-helper-import-projects` to add them.",
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
