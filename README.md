# Resume Helper

A CLI tool that tailors your resume to a specific job posting using AI. It selects the most
relevant projects from your projects database and rewrites them to match the target role,
while leaving all other resume sections untouched.

---

## Setup

1. **Install dependencies**

   ```bash
   pip install -e .
   ```

2. **Configure your API key**

   Copy the example environment file and add your key:

   ```bash
   cp .env.example .env
   ```

   Open `.env` and fill in one of: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`.

3. **Create your projects database**

   ```bash
   cp data/projects_empty.json data/projects.json
   ```

   Then add your projects to `data/projects.json`. You can do this manually or use the importer (see below).

---

## Resume format

Resume Helper expects your base resume as a PDF at `resumes/legacy/resume_default.pdf`.
See `resumes/legacy/resume_template.pdf` for an example of the expected layout and sections.

Your resume should use this two-section structure:

- **Work Experience** — a condensed list of roles (title, org, dates, focus keywords).
  The AI reproduces this section verbatim.
- **Project Experience** — replaced entirely by the AI with 3–5 projects selected from
  your `data/projects.json`, tailored to the job posting.

All other sections (Education, Supporting Experience, etc.) are preserved as-is.

> **Note:** `resume_default.pdf` is excluded from version control — it contains your personal
> information and should not be committed.

---

## Usage

### Build a tailored resume

Run the tool with a job posting URL or pasted job description:

```bash
python -m resume_helper --job "https://jobs.example.com/ds-role"
```

Output is saved automatically to `resumes/enhanced/` and named by company, role, and date.

**All options:**

```bash
python -m resume_helper \
  --job "https://jobs.example.com/ds-role" \
  --resume resumes/legacy/resume_default.pdf \   # optional; this is the default
  --projects data/projects.json \                # optional; this is the default
  --role data_scientist \                        # optional; filters projects by role tag
  --provider gemini \                            # optional; defaults to gemini
  --output resumes/enhanced/tailored_resume.md   # optional; auto-named if omitted
```

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

If you have an existing resume PDF, this command extracts the projects from it and merges
them into your `data/projects.json` automatically.

```bash
python -m resume_helper.import_projects --resume resumes/legacy/resume_default.pdf
```

Re-running is safe — duplicates are detected by title and organization, so only new entries are added.

**All options:**

```bash
python -m resume_helper.import_projects \
  --resume resumes/legacy/resume_default.pdf \   # optional; this is the default
  --projects data/projects.json \                # optional; this is the default
  --provider gemini                              # optional; defaults to gemini
```

---

## Projects database

`data/projects.json` is the master list of projects the AI selects from when building your resume.
See `data/example_projects.json` for annotated examples of the expected format.

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
| `description_long` | no | Full context paragraph for richer AI output |
| `keywords` | no | Domain keywords for matching |

---

## Project structure

```
resume_helper/
├── resumes/
│   ├── legacy/                  # Your input resume lives here
│   │   ├── resume_template.pdf  # Blank template showing expected format and sections
│   │   └── resume_default.pdf   # Your resume (not committed — add your own)
│   └── enhanced/                # Tailored resumes are written here
├── data/
│   ├── projects.json            # Your projects database (not committed)
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
AI calls.

```bash
python smoke_test.py
```
