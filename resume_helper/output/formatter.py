"""Post-process LLM output: strip SELECTION NOTES, normalize whitespace, write file."""
import re
import sys
from pathlib import Path

from pydantic import ValidationError

from resume_helper.models import ResumeOutput

_NOTES_PATTERN = re.compile(
    r"##?\s*SELECTION NOTES.*$",
    re.IGNORECASE | re.DOTALL,
)


def format_and_write(raw_output: str, output_path: str) -> str:
    """Strip SELECTION NOTES, clean whitespace, write plain text to output_path.

    Prints the SELECTION NOTES block to stderr for debugging.
    Returns the cleaned resume text.
    """
    match = _NOTES_PATTERN.search(raw_output)
    if match:
        resume_text = raw_output[: match.start()]
        notes_text = raw_output[match.start() :]
        print("\n" + notes_text.strip(), file=sys.stderr)
    else:
        resume_text = raw_output
        notes_text = ""

    try:
        ResumeOutput(resume_markdown=resume_text, selection_notes=notes_text)
    except ValidationError as exc:
        print(f"[resume-helper] WARNING: LLM output validation failed — {exc}", file=sys.stderr)

    cleaned = _normalize_whitespace(resume_text)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(cleaned, encoding="utf-8")
    print(f"[resume-helper] Resume written to: {out}", file=sys.stderr)

    return cleaned


def _normalize_whitespace(text: str) -> str:
    """Strip trailing whitespace from each line; collapse 3+ blank lines to 2."""
    lines = [line.rstrip() for line in text.splitlines()]
    result = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run <= 2:
                result.append("")
        else:
            blank_run = 0
            result.append(line)
    return "\n".join(result).strip() + "\n"
