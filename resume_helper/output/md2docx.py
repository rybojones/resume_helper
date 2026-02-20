import subprocess
import argparse
import sys
import shutil
from pathlib import Path


def check_pandoc_installed():
    """Check if pandoc is available in the system's PATH. Raises RuntimeError if not."""
    if shutil.which("pandoc") is None:
        raise RuntimeError("Pandoc is not installed or not in your PATH")


def convert_markdown_to_docx(input_file, output_file, template_file=None):
    """Execute the pandoc command to convert a Markdown file to DOCX.

    Raises RuntimeError if the input file is missing or pandoc fails.
    Progress is printed to stderr.
    """
    if not Path(input_file).is_file():
        raise RuntimeError(f"Input file '{input_file}' not found")

    command = ["pandoc", input_file, "-o", output_file]

    if template_file:
        if Path(template_file).is_file():
            print(f"Converting '{input_file}' using template '{template_file}'...", file=sys.stderr)
            command.insert(2, f"--reference-doc={template_file}")
        else:
            print(f"Warning: Template file '{template_file}' not found. Using default styles...", file=sys.stderr)
    else:
        print(f"Converting '{input_file}' with default styles...", file=sys.stderr)

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Success! File saved to '{output_file}'.", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Pandoc conversion failed: {e.stderr}") from e


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Markdown to DOCX using Pandoc.")
    parser.add_argument("input", help="The source Markdown file.")
    parser.add_argument("output", help="The destination DOCX file.")
    parser.add_argument("-t", "--template", help="Optional Word (.docx) template file for styling.", default=None)

    args = parser.parse_args()

    try:
        check_pandoc_installed()
        convert_markdown_to_docx(args.input, args.output, args.template)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
