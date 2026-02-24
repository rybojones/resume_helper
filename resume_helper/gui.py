"""Gradio web UI for Resume Helper.

Run with:  resume-helper-app
       or: python -m resume_helper.gui
"""
import contextlib
import io
import os
import shutil
import sys
from pathlib import Path

import gradio as gr

from resume_helper.config import PROJECT_ROOT, resolve_user_paths, ensure_user_dirs
from resume_helper.models import ROLE_TAGS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _list_users() -> list[str]:
    """Return sorted list of profile subdirectories under users/."""
    users_dir = PROJECT_ROOT / "users"
    if not users_dir.exists():
        return []
    return sorted(p.name for p in users_dir.iterdir() if p.is_dir())


def _inject_api_key(provider: str, api_key: str) -> None:
    """Write API key into os.environ for the chosen provider (never persisted to disk)."""
    if not api_key.strip():
        return
    key_map = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
    }
    env_var = key_map.get(provider)
    if env_var:
        os.environ[env_var] = api_key.strip()


def _save_uploaded_resume(file_obj, user: str) -> str:
    """Copy an uploaded Gradio file to users/{user}/resumes/legacy/ and return the path."""
    user_paths = resolve_user_paths(user)
    ensure_user_dirs(user_paths)
    # Gradio 4.x passes a filepath string; older versions pass an object with .name
    src = file_obj if isinstance(file_obj, str) else file_obj.name
    dest = user_paths.resume.parent / Path(src).name
    shutil.copy(src, dest)
    return str(dest)


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
    raise ValueError(f"Provider '{provider}' is not yet implemented.")


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def _build_resume_handler(
    user: str,
    resume_file,
    job_text: str,
    job_url: str,
    role_tag: str,
    provider: str,
    api_key: str,
) -> tuple[str, str, str | None, str | None]:
    """Build Resume button handler.

    Returns (log, preview_markdown, md_filepath, docx_filepath).
    """
    log_buf = io.StringIO()
    try:
        _inject_api_key(provider, api_key)

        job_input = job_url.strip() or job_text.strip()
        if not job_input:
            return "ERROR: Provide a job description — paste text or enter a URL.", "", None, None

        resume_path = _save_uploaded_resume(resume_file, user) if resume_file else None
        user_paths = resolve_user_paths(user)
        ensure_user_dirs(user_paths)

        from resume_helper.builder.resume_builder import build_resume

        with contextlib.redirect_stderr(log_buf):
            md_path, docx_path = build_resume(
                resume_path=resume_path,
                job_input=job_input,
                projects_path=None,
                role_tag=role_tag or None,
                provider=provider,
                output_path=None,
                reference_doc=None,
                user_paths=user_paths,
            )

        log = log_buf.getvalue()
        preview = md_path.read_text()
        docx_str = str(docx_path) if docx_path.exists() else None
        return log, preview, str(md_path), docx_str

    except (FileNotFoundError, ValueError) as exc:
        return f"{log_buf.getvalue()}\nERROR: {exc}", "", None, None
    except Exception as exc:
        return f"{log_buf.getvalue()}\nUnexpected error: {exc}", "", None, None


def _import_projects_handler(
    user: str,
    resume_file,
    provider: str,
    api_key: str,
) -> str:
    """Import Projects button handler. Returns log text."""
    log_buf = io.StringIO()
    try:
        _inject_api_key(provider, api_key)

        if resume_file is None:
            return "ERROR: Please upload a resume PDF."

        user_paths = resolve_user_paths(user)
        ensure_user_dirs(user_paths)
        resume_path = _save_uploaded_resume(resume_file, user)
        effective_projects = str(user_paths.projects)

        from resume_helper.parsers.pdf_parser import parse_pdf
        from resume_helper.data.projects_db import load_projects, merge_projects
        from resume_helper.import_projects.extractor import extract_projects
        from resume_helper.import_projects.deduplicator import resolve_duplicates
        from resume_helper.import_projects.coverage_check import check_coverage

        with contextlib.redirect_stderr(log_buf):
            print(f"[import-projects] Parsing resume: {resume_path}", file=sys.stderr)
            resume_text = parse_pdf(resume_path)

            llm = _get_provider(provider)
            print(f"[import-projects] Extracting projects via {llm.get_model_name()}...", file=sys.stderr)
            new_projects = extract_projects(resume_text, llm)
            print(f"[import-projects] Extracted {len(new_projects)} project(s).", file=sys.stderr)

            try:
                existing = load_projects(effective_projects)
            except FileNotFoundError:
                existing = []

            if existing:
                print(
                    f"[import-projects] Deduplicating against {len(existing)} existing...",
                    file=sys.stderr,
                )
                truly_new, updated_existing = resolve_duplicates(existing, new_projects, llm)
                n_merged = len(new_projects) - len(truly_new)
                if n_merged:
                    print(f"[import-projects] Merged {n_merged} duplicate(s).", file=sys.stderr)
            else:
                truly_new, updated_existing = list(new_projects), []

            added, merged = merge_projects(updated_existing, truly_new, effective_projects)
            print(f"[import-projects] Added {added} new project(s). Total: {len(merged)}.", file=sys.stderr)
            print(f"[import-projects] projects.json updated: {effective_projects}", file=sys.stderr)

            print("[import-projects] Checking coverage...", file=sys.stderr)
            gaps = check_coverage(resume_text, merged, llm)
            if gaps:
                print("[import-projects] WARNING: Possible gaps:", file=sys.stderr)
                for gap in gaps:
                    print(f"  - {gap}", file=sys.stderr)
            else:
                print("[import-projects] Coverage check passed.", file=sys.stderr)

        return log_buf.getvalue()

    except Exception as exc:
        return f"{log_buf.getvalue()}\nERROR: {exc}"


def _create_user_handler(new_user: str, br_user_comp, ip_user_comp):
    """Create Profile handler. Also refreshes the user dropdowns in other tabs."""
    name = new_user.strip()
    if not name:
        return "ERROR: Profile name cannot be empty.", gr.update(), gr.update()
    user_paths = resolve_user_paths(name)
    ensure_user_dirs(user_paths)
    updated = _list_users()
    return (
        f"Profile '{name}' created at users/{name}/",
        gr.update(choices=updated, value=name),
        gr.update(choices=updated, value=name),
    )


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def main() -> None:
    providers = ["gemini", "openai", "claude"]
    role_choices = [""] + ROLE_TAGS
    users = _list_users()
    default_user = users[0] if users else None

    with gr.Blocks(title="Resume Helper") as demo:
        selected_user = gr.State(value=default_user)

        gr.Markdown("# Resume Helper")

        with gr.Tabs():

            # ── Build Resume ──────────────────────────────────────────────
            with gr.Tab("Build Resume"):
                with gr.Row():
                    br_user = gr.Dropdown(
                        choices=users, label="User Profile", value=default_user
                    )
                    br_role = gr.Dropdown(
                        choices=role_choices, label="Role Tag (optional)", value=""
                    )
                br_resume = gr.File(
                    label="Resume PDF (optional — uses profile default if omitted)",
                    file_types=[".pdf"],
                )
                with gr.Tabs():
                    with gr.Tab("Paste Text"):
                        br_job_text = gr.Textbox(
                            label="Job Description",
                            lines=10,
                            placeholder="Paste the job posting here…",
                        )
                    with gr.Tab("URL"):
                        br_job_url = gr.Textbox(
                            label="Job Posting URL",
                            placeholder="https://…",
                        )
                with gr.Row():
                    br_provider = gr.Dropdown(
                        choices=providers, label="LLM Provider", value="gemini"
                    )
                    br_api_key = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="Paste key here (never stored to disk)",
                    )
                br_button = gr.Button("Build Resume", variant="primary")
                br_log = gr.Textbox(label="Progress Log", lines=8, interactive=False)
                br_preview = gr.Markdown()
                with gr.Row():
                    br_dl_md = gr.File(label="Download .md", interactive=False)
                    br_dl_docx = gr.File(label="Download .docx", interactive=False)

                br_user.change(fn=lambda u: u, inputs=[br_user], outputs=[selected_user])
                br_button.click(
                    fn=_build_resume_handler,
                    inputs=[
                        br_user, br_resume, br_job_text, br_job_url,
                        br_role, br_provider, br_api_key,
                    ],
                    outputs=[br_log, br_preview, br_dl_md, br_dl_docx],
                )

            # ── Import Projects ───────────────────────────────────────────
            with gr.Tab("Import Projects"):
                ip_user = gr.Dropdown(
                    choices=users, label="User Profile", value=default_user
                )
                ip_resume = gr.File(label="Resume PDF", file_types=[".pdf"])
                with gr.Row():
                    ip_provider = gr.Dropdown(
                        choices=providers, label="LLM Provider", value="gemini"
                    )
                    ip_api_key = gr.Textbox(
                        label="API Key",
                        type="password",
                        placeholder="Paste key here (never stored to disk)",
                    )
                ip_button = gr.Button("Import Projects", variant="primary")
                ip_log = gr.Textbox(label="Progress Log", lines=12, interactive=False)

                ip_user.change(fn=lambda u: u, inputs=[ip_user], outputs=[selected_user])
                ip_button.click(
                    fn=_import_projects_handler,
                    inputs=[ip_user, ip_resume, ip_provider, ip_api_key],
                    outputs=[ip_log],
                )

            # ── Manage Users ──────────────────────────────────────────────
            with gr.Tab("Manage Users"):
                mu_name = gr.Textbox(
                    label="New Profile Name", placeholder="e.g. jane_smith"
                )
                mu_button = gr.Button("Create Profile", variant="primary")
                mu_output = gr.Textbox(label="Result", interactive=False)

                mu_button.click(
                    fn=_create_user_handler,
                    inputs=[mu_name, br_user, ip_user],
                    outputs=[mu_output, br_user, ip_user],
                )

        demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
