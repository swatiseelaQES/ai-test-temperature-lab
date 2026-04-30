import json
import os
import subprocess
import sys
from pathlib import Path

from src.config import GENERATED_TESTS_DIR, REPORTS_DIR
from src.score_tests import score_file


def run_pytest(path: Path) -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(path), "-q"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for test_file in sorted(GENERATED_TESTS_DIR.glob("temp_*/test_generated_run_*.py")):
        print(f"Scoring and running {test_file}")
        score = score_file(test_file)
        pytest_result = run_pytest(test_file) if score["syntax_valid"] else {
            "returncode": None,
            "passed": False,
            "stdout": "",
            "stderr": "Skipped pytest because syntax is invalid.",
        }
        results.append({**score, "pytest": pytest_result})

    output_file = REPORTS_DIR / "execution_results.json"
    output_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {output_file}")


if __name__ == "__main__":
    main()
