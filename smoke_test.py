"""
Lightweight smoke test — no pytest, no LLM calls.
Run with: /Users/ryanna/Dev/.envs/resume/bin/python smoke_test.py
"""
import json
import sys
import tempfile
from pathlib import Path

_PASS = []
_FAIL = []


def check(name: str, fn):
    try:
        fn()
        _PASS.append(name)
        print(f"  PASS  {name}")
    except Exception as exc:
        _FAIL.append(name)
        print(f"  FAIL  {name}")
        print(f"        {exc}")


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
print("\n-- imports --")

check("models imports", lambda: __import__("resume_helper.models", fromlist=["ProjectRecord", "ProjectsFile", "ResumeOutput", "DuplicateMatch", "MergedProjectText"]))
check("deduplicator imports", lambda: __import__("resume_helper.import_projects.deduplicator", fromlist=["resolve_duplicates"]))
check("config imports", lambda: __import__("resume_helper.config", fromlist=["PROJECT_ROOT"]))
check("projects_db imports", lambda: __import__("resume_helper.data.projects_db", fromlist=["load_projects"]))
check("pdf_parser imports", lambda: __import__("resume_helper.parsers.pdf_parser", fromlist=["parse_pdf"]))
check("job_parser imports", lambda: __import__("resume_helper.parsers.job_parser", fromlist=["parse_job_input"]))
check("llm.base imports", lambda: __import__("resume_helper.llm.base", fromlist=["LLMProvider"]))
check("claude_provider imports", lambda: __import__("resume_helper.llm.claude_provider", fromlist=["ClaudeProvider"]))
check("gemini_provider imports", lambda: __import__("resume_helper.llm.gemini_provider", fromlist=["GeminiProvider"]))
check("prompt_builder imports", lambda: __import__("resume_helper.builder.prompt_builder", fromlist=["build_prompt"]))
check("resume_builder imports", lambda: __import__("resume_helper.builder.resume_builder", fromlist=["build_resume"]))
check("formatter imports", lambda: __import__("resume_helper.output.formatter", fromlist=["format_and_write"]))
check("import_projects.extractor imports", lambda: __import__("resume_helper.import_projects.extractor", fromlist=["extract_projects"]))
check("import_projects.coverage_check imports", lambda: __import__("resume_helper.import_projects.coverage_check", fromlist=["check_coverage"]))
check("import_projects.cli imports", lambda: __import__("resume_helper.import_projects.cli", fromlist=["main"]))

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
print("\n-- models --")

from pydantic import ValidationError
from resume_helper.models import ProjectRecord, ResumeOutput, DuplicateMatch, MergedProjectText

_WELL_FORMED_RESUME = (
    "# Jane Smith\n\n"
    "## Work Experience\nSome Corp 2020–2022\n\n"
    "## Project Experience\n### Cool Project\nDid cool things.\n"
)

check("ResumeOutput validates well-formed resume",
      lambda: ResumeOutput(resume_markdown=_WELL_FORMED_RESUME))

def _resume_output_missing_sections():
    try:
        ResumeOutput(resume_markdown="# Jane Smith\n\nNo sections here.")
        raise AssertionError("should have raised ValidationError")
    except ValidationError:
        pass

check("ResumeOutput raises ValidationError when sections missing", _resume_output_missing_sections)

def _project_record_bad_role_tags():
    try:
        ProjectRecord(title="Test", summary="s", skills=[], role_tags=["not_a_real_tag"], impact=[])
        raise AssertionError("should have raised ValidationError")
    except ValidationError:
        pass

check("ProjectRecord rejects invalid role_tags", _project_record_bad_role_tags)

def _project_record_empty_role_tags():
    try:
        ProjectRecord(title="Test", summary="s", skills=[], role_tags=[], impact=[])
        raise AssertionError("should have raised ValidationError")
    except ValidationError:
        pass

check("ProjectRecord rejects empty role_tags", _project_record_empty_role_tags)

# ---------------------------------------------------------------------------
# Deduplicator
# ---------------------------------------------------------------------------
print("\n-- deduplicator --")

from resume_helper.import_projects.deduplicator import resolve_duplicates

check("DuplicateMatch accepts empty matched_id",
      lambda: DuplicateMatch(matched_id="", reason="no match found"))

check("DuplicateMatch accepts a real matched_id",
      lambda: DuplicateMatch(matched_id="proj_001", reason="same project"))

check("MergedProjectText validates",
      lambda: MergedProjectText(summary="A summary.", description_long="A longer description."))


def _resolve_duplicates_no_existing():
    existing = []
    new = [ProjectRecord(title="T", summary="s", skills=[], role_tags=["data_scientist"], impact=[])]
    truly_new, updated = resolve_duplicates(existing, new, llm=None)
    assert len(truly_new) == 1
    assert updated == []


check("resolve_duplicates with no existing returns all as new", _resolve_duplicates_no_existing)


def _resolve_duplicates_stub_no_match():
    """Stub LLM always returns no match — all new projects should pass through."""
    class _StubLLM:
        def complete_structured_one(self, _sys, _usr, response_model):
            return DuplicateMatch(matched_id="", reason="no match")

    existing = [
        {"id": "proj_001", "title": "Old Project", "summary": "old summary",
         "skills": ["Python"], "role_tags": ["data_scientist"], "impact": [],
         "organization": "", "role": "", "dates": {}, "description_long": "",
         "keywords": [], "include_by_default": False, "notes": ""}
    ]
    new = [ProjectRecord(title="New Project", summary="new summary", skills=["SQL"],
                         role_tags=["data_analyst"], impact=[])]
    truly_new, updated = resolve_duplicates(existing, new, _StubLLM())
    assert len(truly_new) == 1, f"expected 1 truly new, got {len(truly_new)}"
    assert truly_new[0].title == "New Project"


check("resolve_duplicates stub no-match passes project through", _resolve_duplicates_stub_no_match)


def _resolve_duplicates_stub_match():
    """Stub LLM always returns a match — project should be merged into existing."""
    class _StubLLM:
        def complete_structured_one(self, _sys, _usr, response_model):
            if response_model is DuplicateMatch:
                return DuplicateMatch(matched_id="proj_001", reason="same project")
            return MergedProjectText(summary="merged summary", description_long="merged desc")

    existing = [
        {"id": "proj_001", "title": "Old Project", "summary": "old summary",
         "skills": ["Python"], "role_tags": ["data_scientist"], "impact": ["10% improvement"],
         "organization": "Acme", "role": "", "dates": {}, "description_long": "old desc",
         "keywords": [], "include_by_default": False, "notes": ""}
    ]
    new = [ProjectRecord(title="Old Project v2", summary="new summary", skills=["Python", "SQL"],
                         role_tags=["data_scientist", "data_analyst"], impact=["10% improvement", "saved $1M"],
                         description_long="new desc")]
    truly_new, updated = resolve_duplicates(existing, new, _StubLLM())
    assert len(truly_new) == 0, f"expected 0 truly new, got {len(truly_new)}"
    proj = updated[0]
    assert proj["summary"] == "merged summary"
    assert "SQL" in proj["skills"]
    assert "data_analyst" in proj["role_tags"]
    assert "saved $1M" in proj["impact"]


check("resolve_duplicates stub match merges fields correctly", _resolve_duplicates_stub_match)

# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------
print("\n-- config --")

from resume_helper.config import DEFAULT_RESUME_PATH, DEFAULT_PROJECTS_PATH, OUTPUT_DIR, DEFAULT_PROVIDER

check("DEFAULT_RESUME_PATH points to resume_default.pdf",
      lambda: None if "resume_default.pdf" in str(DEFAULT_RESUME_PATH) else (_ for _ in ()).throw(AssertionError(DEFAULT_RESUME_PATH)))
check("DEFAULT_PROJECTS_PATH points to projects.json",
      lambda: None if "projects.json" in str(DEFAULT_PROJECTS_PATH) else (_ for _ in ()).throw(AssertionError(DEFAULT_PROJECTS_PATH)))
check("OUTPUT_DIR contains 'enhanced'",
      lambda: None if "enhanced" in str(OUTPUT_DIR) else (_ for _ in ()).throw(AssertionError(OUTPUT_DIR)))
check("DEFAULT_PROVIDER is set", lambda: None if DEFAULT_PROVIDER else (_ for _ in ()).throw(AssertionError("empty")))

# ---------------------------------------------------------------------------
# Default resume and projects files exist
# ---------------------------------------------------------------------------
print("\n-- file existence --")

check("resumes/legacy/resume_default.pdf exists", lambda: None if DEFAULT_RESUME_PATH.exists() else (_ for _ in ()).throw(FileNotFoundError(DEFAULT_RESUME_PATH)))
check("data/projects.json exists", lambda: None if DEFAULT_PROJECTS_PATH.exists() else (_ for _ in ()).throw(FileNotFoundError(DEFAULT_PROJECTS_PATH)))

# ---------------------------------------------------------------------------
# projects_db: load + filter
# ---------------------------------------------------------------------------
print("\n-- projects_db --")

from resume_helper.data.projects_db import load_projects, filter_by_role_tag, ROLE_TAGS

def _load_check():
    projects = load_projects(str(DEFAULT_PROJECTS_PATH))
    assert isinstance(projects, list), f"expected list, got {type(projects)}"

check("load_projects returns a list (may be empty before import)", _load_check)

def _filter_check():
    projects = load_projects(str(DEFAULT_PROJECTS_PATH))
    tag = ROLE_TAGS[0]
    filtered = filter_by_role_tag(projects, tag)
    assert isinstance(filtered, list)

check("filter_by_role_tag returns list", _filter_check)

def _bad_tag_check():
    projects = load_projects(str(DEFAULT_PROJECTS_PATH))
    try:
        filter_by_role_tag(projects, "not_a_real_tag")
        raise AssertionError("should have raised ValueError")
    except ValueError:
        pass

check("filter_by_role_tag rejects unknown tag", _bad_tag_check)

# ---------------------------------------------------------------------------
# merge_projects: deduplication
# ---------------------------------------------------------------------------
print("\n-- merge_projects --")

from resume_helper.data.projects_db import merge_projects

def _merge_check():
    existing = [
        {"id": "proj_001", "title": "Alpha Project", "organization": "Acme",
         "summary": "", "skills": [], "role_tags": ["data_scientist"], "impact": []}
    ]
    new = [
        # duplicate (case-insensitive) — must be skipped
        {"title": "alpha project", "organization": "acme",
         "summary": "dup", "skills": [], "role_tags": ["data_scientist"], "impact": []},
        # genuinely new
        {"title": "Beta Project", "organization": "FinCo",
         "summary": "new", "skills": ["Python"], "role_tags": ["machine_learning_engineer"], "impact": ["saved $1M"]},
    ]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({"projects": existing}, f)
        tmp = f.name
    added, merged = merge_projects(existing, new, tmp)
    Path(tmp).unlink(missing_ok=True)
    assert added == 1, f"expected 1 added, got {added}"
    assert len(merged) == 2, f"expected 2 total, got {len(merged)}"
    ids = [p["id"] for p in merged]
    assert "proj_001" in ids, "existing ID should be preserved"

check("merge_projects deduplicates and adds new", _merge_check)

# ---------------------------------------------------------------------------
# prompt_builder: section names present
# ---------------------------------------------------------------------------
print("\n-- prompt_builder --")

from resume_helper.builder.prompt_builder import build_prompt, SYSTEM_PROMPT

check("SYSTEM_PROMPT mentions 'Work Experience'",
      lambda: None if "Work Experience" in SYSTEM_PROMPT else (_ for _ in ()).throw(AssertionError("missing")))
check("SYSTEM_PROMPT mentions 'Project Experience'",
      lambda: None if "Project Experience" in SYSTEM_PROMPT else (_ for _ in ()).throw(AssertionError("missing")))

def _prompt_instructions_check():
    _, user_prompt = build_prompt("RESUME TEXT", "JOB TEXT", [])
    assert "Work Experience" in user_prompt
    assert "Project Experience" in user_prompt

check("build_prompt instructions reference both section names", _prompt_instructions_check)

# ---------------------------------------------------------------------------
# formatter: SELECTION NOTES stripped
# ---------------------------------------------------------------------------
print("\n-- formatter --")

from resume_helper.output.formatter import format_and_write

def _formatter_check():
    raw = (
        "# Jane Smith\n\n"
        "## Work Experience\nSome Corp 2020–2022\n\n"
        "## Project Experience\n### Cool Project\nDid cool things.\n\n"
        "## SELECTION NOTES\nChose Cool Project because it matched.\n"
    )
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
        tmp = f.name
    cleaned = format_and_write(raw, tmp)
    content = Path(tmp).read_text()
    Path(tmp).unlink(missing_ok=True)
    assert "SELECTION NOTES" not in content, "SELECTION NOTES should be stripped from file"
    assert "Jane Smith" in content, "resume content should be present"

check("formatter strips SELECTION NOTES from written file", _formatter_check)

# ---------------------------------------------------------------------------
# Output path uses .md extension
# ---------------------------------------------------------------------------
print("\n-- output path --")

from resume_helper.builder.resume_builder import _resolve_output_path

check("auto-named output path uses .md extension",
      lambda: None if _resolve_output_path(None, None).suffix == ".md"
      else (_ for _ in ()).throw(AssertionError(_resolve_output_path(None, None).suffix)))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total = len(_PASS) + len(_FAIL)
print(f"\n{len(_PASS)}/{total} checks passed", end="")
if _FAIL:
    print(f"  ({len(_FAIL)} failed: {', '.join(_FAIL)})")
    sys.exit(1)
else:
    print(" — all good.")
