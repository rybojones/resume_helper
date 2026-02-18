"""Thin CLI entrypoint. Parses args and delegates to build_resume()."""
import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="resume-helper",
        description="Tailor a resume to a job posting using an LLM.",
    )
    parser.add_argument("--resume", help="Path to base resume PDF (default: resumes/legacy/default_resume.pdf)")
    parser.add_argument("--job", required=True, help="Job posting URL or raw text")
    parser.add_argument("--projects", help="Path to projects.json (default: data/projects.json)")
    parser.add_argument("--role", help="Role tag to filter projects (e.g. data_scientist)")
    parser.add_argument("--provider", default="claude", help="LLM provider (default: claude)")
    parser.add_argument("--output", help="Output file path (auto-named if omitted)")

    args = parser.parse_args()

    # Import here to keep startup fast and allow stubs during scaffold
    from resume_helper.builder.resume_builder import build_resume  # noqa: F401
    build_resume(
        resume_path=args.resume,
        job_input=args.job,
        projects_path=args.projects,
        role_tag=args.role,
        provider=args.provider,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
