# Resume Helper

A CLI tool that tailors a resume to a job posting using an LLM. It selects the most
relevant projects from a master projects database and rewrites them to match the target
role, while leaving all other resume sections untouched.

---

## Setup

1. **Activate the venv**

   ```bash
   source /Users/ryanna/Dev/.envs/resume/bin/activate
   # or: activate resume  (if you have a shell alias)
   ```

2. **Install dependencies**

   ```bash
   pip install -e .
   ```

3. **Configure your API key**

   ```bash
   cp .env.example .env
   # Edit .env and add your key — GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY
   ```

---

## Resume format

The base resume (`resumes/legacy/resume_default.pdf`) uses a two-section format:

- **Work Experience** — static condensed list of roles (title, org, dates, Focus keywords).
  The LLM reproduces this section verbatim.
- **Project Experience** — dynamic. The LLM replaces this entire section with 3–5 projects
  selected from `data/projects.json`, tailored to the job posting.

All other sections (Education, Supporting Experience) are also preserved verbatim.

---

## Usage

### Build a tailored resume

```bash
python -m resume_helper \
  --job "https://jobs.example.com/ds-role" \
  --resume resumes/legacy/resume_default.pdf \   # optional; this is the default
  --projects data/projects.json \                # optional; this is the default
  --role data_scientist \                        # optional; filters projects by role tag
  --provider gemini \                            # optional; defaults to gemini
  --output resumes/enhanced/tailored_resume.md   # optional; auto-named if omitted
```

Output is written to `resumes/enhanced/` as a markdown file.

**`--job` accepts a URL or raw text.** URL scraping works for public job postings
(Ashby, Lever, Greenhouse, etc.). Pages behind a login wall (LinkedIn, Workday SSO)
will return the login screen — in those cases, paste the job description directly:

```bash
python -m resume_helper --job "$(pbpaste)"   # macOS: paste from clipboard
```

**Valid `--role` values:**
`data_scientist`, `machine_learning_engineer`, `analytics_engineer`,
`ai_engineer`, `data_analyst`, `data_engineer`

---

### Import projects from a resume PDF

Extracts projects from a legacy resume PDF using an LLM and merges them into
`data/projects.json`. Runs a semantic coverage check after import to flag any
work experience that may not have been captured.

```bash
python -m resume_helper.import_projects \
  --resume resumes/legacy/resume_default.pdf \   # optional; this is the default
  --projects data/projects.json \                # optional; this is the default
  --provider gemini                              # optional; defaults to gemini
```

Re-running is safe — existing projects are deduplicated by title + organization
(case-insensitive). Only genuinely new entries are added.

---

## Projects database

`data/projects.json` is the master list of projects the LLM selects from.
See `data/example_projects.json` for annotated examples of the schema.

Key fields per project:

| Field | Required | Description |
|---|---|---|
| `id` | yes | Unique identifier (auto-generated on import) |
| `title` | yes | Short project name |
| `summary` | yes | 1–2 sentence summary |
| `skills` | yes | Tech stack and tools |
| `role_tags` | yes | Role categories this project is relevant for |
| `impact` | yes | Measurable outcomes |
| `organization` | no | Employer / client name |
| `dates` | no | `{ "start": "YYYY-MM", "end": "YYYY-MM" }` |
| `description_long` | no | Full context paragraph for richer LLM output |
| `keywords` | no | Domain keywords for matching |

---

## Project structure

```
resume_helper/
├── resumes/
│   ├── legacy/                  # Input resumes (resume_default.pdf lives here)
│   └── enhanced/                # Output tailored resumes written here
├── data/
│   ├── projects.json            # Master projects database (may start empty)
│   └── example_projects.json   # Annotated schema examples for reference
├── resume_helper/               # Main Python package
│   ├── builder/                 # Prompt assembly + orchestration
│   ├── data/                    # projects_db.py: load, validate, merge
│   ├── import_projects/         # Importer subpackage
│   ├── llm/                     # Provider abstraction + Claude/Gemini/OpenAI
│   ├── output/                  # Formatter: strip notes, write .md file
│   └── parsers/                 # PDF parser + job posting scraper
├── smoke_test.py
├── pyproject.toml
└── .env.example
```

---

## Smoke test

Verifies imports, config defaults, file existence, and core logic without making any
LLM calls.

```bash
python smoke_test.py
```
