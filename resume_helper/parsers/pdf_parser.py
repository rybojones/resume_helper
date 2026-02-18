"""Extract text from PDF resume files."""
from pathlib import Path

import pdfplumber


def parse_pdf(path: str) -> str:
    """Extract plain text from a PDF resume.

    Joins pages with a blank line separator so section breaks are preserved.
    Raises FileNotFoundError if the path does not exist.
    """
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Resume PDF not found: {resolved}")

    pages = []
    with pdfplumber.open(resolved) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if text:
                pages.append(text.strip())

    return "\n\n".join(pages)
