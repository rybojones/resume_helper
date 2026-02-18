# Resume Helper

A CLI tool that tailors a resume to a job posting using an LLM.

---

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your API key**

   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

---

## Usage

```bash
python -m resume_helper \
  --job "https://jobs.example.com/ds-role" \
  --resume resumes/legacy/data_scientist.pdf \   # optional; defaults to resumes/legacy/resume_default.pdf
  --projects data/projects.json \                # optional; defaults to data/projects.json
  --role data_scientist \                        # optional; filters projects by role tag
  --provider claude \                            # optional; defaults to claude
  --output resumes/enhanced/tailored_resume.md   # optional; auto-named if omitted
```

### Job posting input

`--job` accepts either a URL or raw pasted text.

URL scraping works for **public** job postings (Ashby, Lever, Greenhouse public pages, etc.).
Pages behind a login wall (e.g. LinkedIn, Built In matches, Workday SSO) will return the login
screen instead of the job content — in those cases, copy-paste the job description as raw text:

```bash
python -m resume_helper --job "$(pbpaste)"   # macOS: paste from clipboard
```

---

## Project Structure

```
resume_helper/
├── resumes/
│   ├── legacy/          # Input resumes (resume_default.pdf lives here)
│   └── enhanced/        # Output tailored resumes written here
├── data/
│   └── projects.json    # Master projects database
├── resume_helper/       # Main Python package
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Smoke Test

```bash
python smoke_test.py
```
