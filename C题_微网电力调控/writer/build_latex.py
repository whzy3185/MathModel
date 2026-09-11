#!/usr/bin/env python3
"""Compile the ReasLab-aligned Chinese CUMCM manuscript.

This script is intentionally small: the manuscript is already split into
problem-by-problem LaTeX files. It performs reproducible XeLaTeX passes,
checks the return code, and promotes the accepted PDF to the project root.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
ENTRY = HERE / "main.tex"
WORKING_PDF = HERE / "main.pdf"
PROMOTED = PROJECT / "微网与外部电网日前日内协同调度.pdf"


def run_xelatex() -> None:
    if shutil.which("xelatex") is None:
        raise RuntimeError("xelatex is not available")
    cmd = ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    result = subprocess.run(cmd, cwd=HERE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"XeLaTeX failed with code {result.returncode}")


def main() -> None:
    if not ENTRY.exists():
        raise FileNotFoundError(ENTRY)
    for _ in range(3):
        run_xelatex()
    if not WORKING_PDF.exists():
        raise RuntimeError("main.pdf was not generated")
    shutil.copy2(WORKING_PDF, HERE / "Paper_Final.pdf")
    shutil.copy2(WORKING_PDF, PROMOTED)
    print(f"compiled: {WORKING_PDF}")
    print(f"promoted: {PROMOTED}")


if __name__ == "__main__":
    main()
