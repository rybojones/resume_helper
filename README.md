# Resume Helper

A CLI tool that tailors a resume to a job posting using an LLM.

---

## Setup

1. **Create and activate the virtual environment**

   ```bash
   python -m venv ~/Dev/.envs/resume
   activate resume
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API key**

   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

---

## Usage

```bash
python -m resume_helper \
  --job "https://jobs.example.com/ds-role" \
  --resume resumes/legacy/data_scientist.pdf \   # optional; defaults to resumes/legacy/default.pdf
  --projects data/projects.json \                # optional; defaults to data/projects.json
  --role data_scientist \                        # optional; filters projects by role tag
  --provider claude \                            # optional; defaults to claude
  --output resumes/enhanced/tailored_resume.txt  # optional; auto-named if omitted
```

---

## Project Structure

```
resume_helper/
├── resumes/
│   ├── legacy/          # Input resumes (default.pdf lives here)
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
