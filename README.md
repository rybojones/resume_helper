# Resume Helper

A CLI tool that tailors your resume to a specific job posting using AI. It selects the most
relevant projects from your projects database and rewrites them to match the target role,
while leaving all other resume sections untouched.

---

## Getting started

1. **Install Homebrew dependencies**

   ```bash
   brew install pandoc
   ```

   > Don't have Homebrew? Install it from [brew.sh](https://brew.sh).

2. **Create and activate a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   > The `resume-helper-*` commands are installed into the venv's `bin/`. They won't be
   > found in your terminal unless the venv is active. Add the `source` line to your
   > `~/.zshrc` (or `~/.bashrc`) to activate it automatically for this project.

3. **Install dependencies**

   ```bash
   pip install -e .
   ```

4. **Configure your API key**

   ```bash
   cp .env.example .env
   ```

   Open `.env` and fill in one of: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`.

5. **Create your user profile**

   ```bash
   resume-helper-init
   ```

   Follow the prompt to enter your profile name (e.g. `jane_smith`). This creates
   `users/<your-name>/` with the expected directory structure and an empty `projects.json`.

6. **Drop in your resume PDF**

   Copy your resume to:

   ```
   users/<your-name>/resumes/legacy/resume_default.pdf
   ```

   See `users/jayne_dough/resumes/legacy/resume_template.pdf` for an example of the expected
   layout and sections. The structure consists of separate work experience and project experience
   sections. If your resume doesn't follow this pattern there may be _"quirky"_ output behavior.

7. **Import projects** *(optional — skip if you'll edit `projects.json` manually)*

   ```bash
   resume-helper-import-projects --user <your-name>
   ```

8. **Set your active user** *(recommended — avoids typing `--user` every time)*

   ```bash
   export RESUME_HELPER_USER=<your-name>
   ```

---

## Resume format

Resume Helper expects your base resume as a PDF at
`users/<your-name>/resumes/legacy/resume_default.pdf`.

Your resume should use this two-section structure:

- **Work Experience** — a condensed list of roles (title, org, dates, focus keywords).
  The AI reproduces this section verbatim.
- **Project Experience** — replaced entirely by the AI with 3–5 projects selected from
  your `users/<your-name>/projects.json`, tailored to the job posting.

All other sections (Education, Supporting Experience, etc.) are preserved as-is.

> **Note:** `resume_default.pdf` is excluded from version control — it contains your personal
> information and should not be committed.

---

## Usage

### Build a tailored resume

Run the tool with a job posting URL or copy-pasta'd job description:

```bash
resume-helper --job "https://jobs.example.com/ds-role"
```

Output is saved automatically to `users/<your-name>/resumes/enhanced/` and named by
company, role, and date.

**All options:**

```bash
resume-helper \
  --job "https://jobs.example.com/ds-role" \
  --resume users/<your-name>/resumes/legacy/resume_default.pdf \  # optional; default from profile
  --projects users/<your-name>/projects.json \                    # optional; default from profile
  --role data_scientist \                                         # optional; filters projects by role tag
  --provider gemini \                                             # optional; defaults to gemini
  --output users/<your-name>/resumes/enhanced/tailored.md \       # optional; auto-named if omitted
  --user <your-name>                                              # optional if RESUME_HELPER_USER is set
```

**`--job` accepts a URL or raw text.** URL scraping works for public job postings
(Ashby, Lever, Greenhouse, etc.). Pages behind a login wall (LinkedIn, Workday SSO)
will return the login screen — in those cases, paste the job description directly:

```bash
resume-helper --job "$(pbpaste)"   # macOS: paste from clipboard
```

**Valid `--role` values:**
`data_scientist`, `machine_learning_engineer`, `analytics_engineer`,
`ai_engineer`, `data_analyst`, `data_engineer`

---

### Import projects from a resume PDF

If you have an existing resume PDF, this command extracts the projects from it and merges
them into your `projects.json` automatically.

```bash
resume-helper-import-projects --user <your-name>
```

Re-running is safe — duplicates are detected by title and organization, so only new entries
are added.

**All options:**

```bash
resume-helper-import-projects \
  --resume users/<your-name>/resumes/legacy/resume_default.pdf \  # optional; default from profile
  --projects users/<your-name>/projects.json \                    # optional; default from profile
  --provider gemini \                                             # optional; defaults to gemini
  --user <your-name>                                              # optional if RESUME_HELPER_USER is set
```

---

## Projects database

`users/<your-name>/projects.json` is the master list of projects the AI selects from when
building your resume. See `users/jayne_dough/projects.json` for annotated examples of the
expected format.

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

## Multiple users

Resume Helper supports multiple user profiles in the same repository.

### List profiles

```bash
resume-helper-users
```

### Create a new profile

```bash
resume-helper-init
# → Enter profile name: cole_lagreggor
```

### Switch between profiles

Use the `--user` flag on any command:

```bash
resume-helper --job "..." --user cole_lagreggor
```

Or set the environment variable to avoid repeating `--user`:

```bash
export RESUME_HELPER_USER=cole_lagreggor
resume-helper --job "..."
```

`resume-helper-users` marks the active profile (set via `RESUME_HELPER_USER`) with `*`,
and marks `jayne_dough` as the default when no env var is set.

---

## Project structure

```
resume_helper/
├── users/
│   ├── jayne_dough/                  # Example / default user profile
│   │   ├── projects.json             # Projects database
│   │   └── resumes/
│   │       ├── legacy/               # Input resume lives here
│   │       │   └── resume_default.pdf
│   │       └── enhanced/             # Tailored resumes are written here
│   │           ├── md/
│   │           └── docx/
│   └── <your-name>/                  # Your profile (created by resume-helper-init)
│       └── ...
├── shared/
│   ├── projects_empty.json           # Template copied to new user profiles
│   └── pandoc_template.docx          # .docx reference template
├── resume_helper/                    # Main Python package
│   ├── builder/                      # Prompt assembly + orchestration
│   ├── data/                         # projects_db.py: load, validate, merge
│   ├── import_projects/              # Importer subpackage
│   ├── llm/                          # Provider abstraction + Claude/Gemini/OpenAI
│   ├── output/                       # Formatter: strip notes, write .md file
│   └── parsers/                      # PDF parser + job posting scraper
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
