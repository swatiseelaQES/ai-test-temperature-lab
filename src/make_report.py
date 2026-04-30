import json
from collections import defaultdict
from pathlib import Path

from src.config import REPORTS_DIR


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def temp_from_path(file_path: str) -> str:
    parts = Path(file_path).parts
    for part in parts:
        if part.startswith("temp_"):
            return part.replace("temp_", "").replace("_", ".")
    return "unknown"


def summarize_execution(results: list[dict]) -> dict[str, dict]:
    summary = defaultdict(lambda: {
        "files": 0,
        "syntax_valid": 0,
        "pytest_passed": 0,
        "test_functions": 0,
        "assertions": 0,
        "coverage_keywords": 0,
    })
    for item in results:
        temp = temp_from_path(item["file"])
        summary[temp]["files"] += 1
        summary[temp]["syntax_valid"] += int(item["syntax_valid"])
        summary[temp]["pytest_passed"] += int(item["pytest"]["passed"])
        summary[temp]["test_functions"] += item["test_function_count"]
        summary[temp]["assertions"] += item["assertion_count"]
        summary[temp]["coverage_keywords"] += item["coverage_keyword_count"]
    return dict(summary)


def average_similarity(comparisons: list[dict]) -> float:
    if not comparisons:
        return 0.0
    return round(sum(c["similarity"] for c in comparisons) / len(comparisons), 4)


def html_escape(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    execution = load_json(REPORTS_DIR / "execution_results.json", [])
    similarity = load_json(REPORTS_DIR / "similarity_results.json", [])
    summary = summarize_execution(execution)

    rows = []
    for temp, data in sorted(summary.items(), key=lambda kv: float(kv[0]) if kv[0] != "unknown" else 99):
        rows.append(
            f"""
            <tr>
              <td>{html_escape(temp)}</td>
              <td>{data['files']}</td>
              <td>{data['syntax_valid']}</td>
              <td>{data['pytest_passed']}</td>
              <td>{data['test_functions']}</td>
              <td>{data['assertions']}</td>
              <td>{data['coverage_keywords']}</td>
            </tr>
            """
        )

    detail_rows = []
    for item in execution:
        detail_rows.append(
            f"""
            <tr>
              <td>{html_escape(Path(item['file']).name)}</td>
              <td>{html_escape(temp_from_path(item['file']))}</td>
              <td>{item['syntax_valid']}</td>
              <td>{item['pytest']['passed']}</td>
              <td>{item['test_function_count']}</td>
              <td>{item['assertion_count']}</td>
              <td>{item['coverage_keyword_count']}</td>
            </tr>
            """
        )

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>AI Test Temperature Lab Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; line-height: 1.45; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 32px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f5f5f5; }}
    code {{ background: #f5f5f5; padding: 2px 4px; }}
    .note {{ background: #fff8dc; padding: 12px; border-left: 4px solid #e1b100; }}
  </style>
</head>
<body>
  <h1>AI Test Temperature Lab Report</h1>
  <p>This report compares generated pytest files across temperature settings.</p>

  <div class="note">
    <strong>Interpretation note:</strong> These are lightweight indicators, not a definitive quality score.
    Use them to spot variation, drift, and candidates for human review.
  </div>

  <h2>Summary by Temperature</h2>
  <table>
    <tr>
      <th>Temperature</th>
      <th>Files</th>
      <th>Syntax Valid</th>
      <th>Pytest Passed</th>
      <th>Test Functions</th>
      <th>Assertions</th>
      <th>Coverage Keyword Hits</th>
    </tr>
    {''.join(rows)}
  </table>

  <h2>Overall Similarity</h2>
  <p>Average pairwise similarity across generated files: <code>{average_similarity(similarity)}</code></p>

  <h2>Generated File Details</h2>
  <table>
    <tr>
      <th>File</th>
      <th>Temperature</th>
      <th>Syntax Valid</th>
      <th>Pytest Passed</th>
      <th>Test Functions</th>
      <th>Assertions</th>
      <th>Coverage Keyword Hits</th>
    </tr>
    {''.join(detail_rows)}
  </table>
</body>
</html>
"""

    output_file = REPORTS_DIR / "temperature_experiment_report.html"
    output_file.write_text(html, encoding="utf-8")
    print(f"Wrote {output_file}")


if __name__ == "__main__":
    main()
