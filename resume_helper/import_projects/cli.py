"""CLI for `python -m resume_helper.import_projects`."""
import argparse
import sys

from resume_helper.config import DEFAULT_PROVIDER, resolve_user_paths, ensure_user_dirs
from resume_helper.parsers.pdf_parser import parse_pdf
from resume_helper.data.projects_db import load_projects, merge_projects
from resume_helper.import_projects.extractor import extract_projects
from resume_helper.import_projects.deduplicator import resolve_duplicates
from resume_helper.import_projects.coverage_check import check_coverage


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="resume-helper-import-projects",
        description="Extract projects from a resume PDF and merge them into projects.json.",
    )
    parser.add_argument(
        "--resume",
        default=None,
        help="Path to resume PDF (default: user profile resume)",
    )
    parser.add_argument(
        "--projects",
        default=None,
        help="Path to projects.json (default: user profile projects)",
    )
    parser.add_argument(
        "--provider",
        default=DEFAULT_PROVIDER,
        help=f"LLM provider (default: {DEFAULT_PROVIDER})",
    )
    parser.add_argument("--user", help="Your user profile name (or set RESUME_HELPER_USER env var)")
    args = parser.parse_args()

    user_paths = resolve_user_paths(args.user)
    ensure_user_dirs(user_paths)
    effective_resume   = args.resume   or str(user_paths.resume)
    effective_projects = args.projects or str(user_paths.projects)

    # --- Parse resume ---
    print(f"[import-projects] Parsing resume: {effective_resume}", file=sys.stderr)
    try:
        resume_text = parse_pdf(effective_resume)
    except FileNotFoundError as exc:
        print(f"[import-projects] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    # --- Get LLM provider ---
    llm = _get_provider(args.provider)
    print(f"[import-projects] Extracting projects via {llm.get_model_name()}...", file=sys.stderr)

    # --- Extract ---
    try:
        new_projects = extract_projects(resume_text, llm)
    except ValueError as exc:
        print(f"[import-projects] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[import-projects] Extracted {len(new_projects)} project(s) from resume.", file=sys.stderr)

    # --- Load existing ---
    try:
        existing = load_projects(effective_projects)
    except FileNotFoundError:
        existing = []

    # --- Deduplicate against existing ---
    if existing:
        print(f"[import-projects] Checking {len(new_projects)} new project(s) for duplicates against {len(existing)} existing...", file=sys.stderr)
        truly_new, updated_existing = resolve_duplicates(existing, new_projects, llm)
        n_merged = len(new_projects) - len(truly_new)
        if n_merged:
            print(f"[import-projects] Merged {n_merged} duplicate(s) into existing records.", file=sys.stderr)
    else:
        truly_new, updated_existing = list(new_projects), []

    # --- Merge new into database ---
    added, merged = merge_projects(updated_existing, truly_new, effective_projects)

    print(f"[import-projects] Added {added} new project(s). Total: {len(merged)}.", file=sys.stderr)
    print(f"[import-projects] projects.json updated: {effective_projects}", file=sys.stderr)

    # --- LLM coverage check ---
    print("[import-projects] Checking coverage...", file=sys.stderr)
    gaps = check_coverage(resume_text, merged, llm)
    if gaps:
        print(
            "[import-projects] WARNING: The following resume experiences may not be fully captured:",
            file=sys.stderr,
        )
        for gap in gaps:
            print(f"  - {gap}", file=sys.stderr)
        print(
            "[import-projects] Review projects.json and add them manually if needed.",
            file=sys.stderr,
        )
    else:
        print("[import-projects] Coverage check passed — all experience appears represented.", file=sys.stderr)


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
    print(f"[import-projects] ERROR: Provider '{provider}' is not yet implemented.", file=sys.stderr)
    sys.exit(1)
