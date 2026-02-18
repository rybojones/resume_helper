"""Parse job posting from URL or raw text."""
import re

import requests
from bs4 import BeautifulSoup

# Tags whose content is never useful (scripts, styles, nav, etc.)
_STRIP_TAGS = {"script", "style", "noscript", "header", "footer", "nav", "aside"}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def parse_job_input(job_input: str) -> str:
    """Return plain text for a job posting.

    If job_input looks like a URL, fetches and parses the page.
    Otherwise treats job_input as raw text and returns it as-is.
    """
    if _is_url(job_input):
        return _scrape_url(job_input)
    return job_input.strip()


def _is_url(text: str) -> bool:
    return bool(re.match(r"^https?://", text.strip(), re.IGNORECASE))


def _scrape_url(url: str) -> str:
    response = requests.get(url, headers=_HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    for tag in soup(list(_STRIP_TAGS)):
        tag.decompose()

    # Prefer a focused content container if one exists
    body = (
        soup.find("main")
        or soup.find(id=re.compile(r"job|content|description", re.I))
        or soup.find(class_=re.compile(r"job|content|description", re.I))
        or soup.body
    )

    if body is None:
        return _meta_description_fallback(soup)

    text = _collapse_whitespace(body.get_text(separator="\n"))

    # JS-rendered SPAs (e.g. Ashby) produce an empty body — fall back to meta
    if not text:
        return _meta_description_fallback(soup)

    return text


def _collapse_whitespace(raw: str) -> str:
    """Collapse runs of blank lines; strip each line."""
    lines = (line.strip() for line in raw.splitlines())
    chunks = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                chunks.append("")
            prev_blank = True
        else:
            chunks.append(line)
            prev_blank = False
    return "\n".join(chunks).strip()


def _meta_description_fallback(soup: BeautifulSoup) -> str:
    """Extract content from <meta name="description"> for JS-rendered pages."""
    tag = soup.find("meta", attrs={"name": "description"})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""
