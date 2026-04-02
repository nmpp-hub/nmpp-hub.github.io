#!/usr/bin/env python3
"""Master script to generate all pages from YAML data.

This script orchestrates all generation tasks in the correct order:
1. Fetch/cache publications metadata
2. Generate dissertations page
3. Generate code pages with publications and dissertations
4. Generate member pages

Run this once to regenerate all content:
    python3 generate_website.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_script(script_path: Path, script_name: str) -> bool:
    """Run a Python script and return True if successful."""
    print(f"\n{'=' * 70}")
    print(f"Running: {script_name}")
    print(f"{'=' * 70}")

    try:
        result = subprocess.run(
            ["python3", str(script_path)],
            cwd=ROOT,
            check=False,
        )
        if result.returncode != 0:
            print(f"❌ {script_name} failed with exit code {result.returncode}")
            return False
        print(f"✅ {script_name} completed successfully")
        return True
    except Exception as exc:
        print(f"❌ {script_name} raised an exception: {exc}")
        return False


def main() -> int:
    """Run all generation scripts in order."""
    scripts_dir = ROOT / "scripts"
    scripts = [
        (scripts_dir / "populate_publications.py", "Populate Publications"),
        (scripts_dir / "generate_dissertations_page.py", "Generate Dissertations Page"),
        (scripts_dir / "generate_code_pages.py", "Generate Code Pages"),
        (scripts_dir / "generate_members_page.py", "Generate Members Page"),
        (scripts_dir / "generate_member_pages.py", "Generate Individual Member Pages"),
    ]

    results = []
    for script_path, script_name in scripts:
        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            results.append(False)
        else:
            results.append(run_script(script_path, script_name))

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")

    for (_, script_name), success in zip(scripts, results):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {script_name}")

    all_success = all(results)
    print(f"\nOverall: {'✅ All scripts completed successfully!' if all_success else '❌ Some scripts failed'}")
    print(f"{'=' * 70}\n")

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
