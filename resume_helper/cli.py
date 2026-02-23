"""Thin CLI entrypoint. Parses args and delegates to build_resume()."""
import argparse
import sys

from resume_helper.config import DEFAULT_PROVIDER, resolve_user_paths, ensure_user_dirs
from resume_helper.models import ROLE_TAGS


def _read_job_input(job_arg: str | None) -> str:
    """Return job posting text from the argument, or stdin if arg is '-' or omitted."""
    if job_arg is not None and job_arg != "-":
        return job_arg

    if sys.stdin.isatty():
        print("Paste job description below, then press Ctrl+D when done:", file=sys.stderr)

    text = sys.stdin.read()

    if not text.strip():
        print("[resume-helper] ERROR: No job description provided.", file=sys.stderr)
        sys.exit(1)

    return text


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="resume-helper",
        description="Tailor a resume to a job posting using an LLM.",
        epilog="See also: resume-helper-init  resume-helper-users  resume-helper-import-projects",
    )
    parser.add_argument("--resume", help="Path to base resume PDF (default: resumes/legacy/default_resume.pdf)")
    parser.add_argument(
        "--job",
        default=None,
        help=(
            "Job posting URL, raw text, or '-' to read from stdin. "
            "Omit entirely to be prompted for interactive paste (Ctrl+D to finish)."
        ),
    )
    parser.add_argument("--projects", help="Path to projects.json (default: data/projects.json)")
    parser.add_argument("--role", choices=ROLE_TAGS, metavar="ROLE",
                        help=f"Filter projects by role tag. Valid values: {', '.join(ROLE_TAGS)}")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, help=f"LLM provider (default: {DEFAULT_PROVIDER})")
    parser.add_argument("--output", help="Output file path (auto-named if omitted)")
    parser.add_argument(
        "--reference-doc",
        help="Path to .docx reference template (default: resumes/legacy/resume_template.docx)",
    )
    parser.add_argument("--user", help="Your user profile name (or set RESUME_HELPER_USER env var)")

    args = parser.parse_args()

    job_input = _read_job_input(args.job)

    user_paths = resolve_user_paths(args.user)
    ensure_user_dirs(user_paths)

    # Import here to keep startup fast and allow stubs during scaffold
    from resume_helper.builder.resume_builder import build_resume  # noqa: F401
    build_resume(
        resume_path=args.resume,
        job_input=job_input,
        projects_path=args.projects,
        role_tag=args.role,
        provider=args.provider,
        output_path=args.output,
        reference_doc=args.reference_doc,
        user_paths=user_paths,
    )


if __name__ == "__main__":
    main()
