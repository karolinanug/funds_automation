#!/usr/bin/env python3
"""
Daily pipeline orchestrator - auto-discovers and runs all scrapers.
"""
from datetime import datetime
from pathlib import Path
import subprocess
import sys

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PYTHON = BASE_DIR / ".venv" / "bin" / "python3"
LOG_DIR = BASE_DIR / "logs"
SOURCES_DIR = BASE_DIR / "sources"


def get_python_executable():
    if DEFAULT_PYTHON.exists():
        return DEFAULT_PYTHON
    return Path(sys.executable)


def discover_scrapers():
    """
    Auto-discover all scraper scripts in the sources/ directory.
    Excludes files starting with underscore or 'template'.
    
    Returns:
        List of scraper script paths in sources/ folder
    """
    scrapers = []
    
    if not SOURCES_DIR.exists():
        print(f"Warning: sources/ directory not found at {SOURCES_DIR}")
        return scrapers
    
    for script_file in sorted(SOURCES_DIR.glob("*.py")):
        # Skip private files, templates, and __init__.py
        if script_file.name.startswith("_") or "template" in script_file.name:
            continue
        
        scrapers.append(script_file)
    
    return scrapers


def run_step(script_path):
    """
    Run a single script/scraper with a timeout.
    
    Args:
        script_path: Full path to the script to run
    """
    command = [str(get_python_executable()), str(script_path)]
    print(f"\n=== Running {script_path.name} ===")
    try:
        result = subprocess.run(command, cwd=BASE_DIR, check=False, timeout=180)
        if result.returncode != 0:
            raise RuntimeError(f"{script_path.name} failed with exit code {result.returncode}")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{script_path.name} timed out after 180 seconds")


def main():
    python_executable = get_python_executable()
    if not python_executable.exists():
        print(f"Missing Python interpreter: {python_executable}")
        sys.exit(1)

    LOG_DIR.mkdir(exist_ok=True)
    print(f"Starting daily workflow at {datetime.now().isoformat(timespec='seconds')}")

    # Step 1: Discover and run all scrapers
    scrapers = discover_scrapers()
    
    if not scrapers:
        print("Warning: No scrapers found in sources/ directory")
    else:
        print(f"Found {len(scrapers)} scraper(s): {', '.join(s.name for s in scrapers)}")
        
        for scraper_path in scrapers:
            run_step(scraper_path)

    # Step 2: Merge data from all sources
    print("\n=== Running merge_data.py ===")
    merge_script = BASE_DIR / "merge_data.py"
    if merge_script.exists():
        run_step(merge_script)
    else:
        print(f"Warning: {merge_script} not found")

    # Step 3: Send email
    print("\n=== Running send_email.py ===")
    email_script = BASE_DIR / "send_email.py"
    if email_script.exists():
        run_step(email_script)
    else:
        print(f"Warning: {email_script} not found")

    print(f"Workflow completed at {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Workflow failed: {exc}")
        sys.exit(1)
