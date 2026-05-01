import ast
import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from src.config import REPORTS_DIR


PROMPT_MODES = ["temp_only", "temp_plus_prompt"]

SCENARIO_KEYWORDS = {
    "happy_path": ["happy", "valid", "successful", "success", "standard"],
    "missing_required": ["missing", "required"],
    "boundary_price": ["boundary", "totalprice", "price", "large number", "zero"],
    "depositpaid_variation": ["depositpaid", "true", "false"],
    "additionalneeds_optional": ["additionalneeds", "optional", "empty string", "omitted"],
    "name_variation": ["firstname", "lastname", "unicode", "hyphen", "apostrophe", "spaces"],
    "date_behavior": ["date", "checkin", "checkout", "same-day", "before checkin"],
    "extra_fields": ["extra field", "unexpected", "additional field"],
    "response_schema": ["schema", "response", "bookingid", "nested", "structure"],
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def html_escape(value):
    return html.escape(str(value), quote=True)


def prompt_mode_from_path(file_path: str) -> str:
    normalized = file_path.replace("\\", "/")
    for mode in PROMPT_MODES:
        if f"/{mode}/" in normalized or normalized.startswith(f"{mode}/"):
            return mode
    return "unknown"


def temp_from_path(file_path: str) -> str:
    normalized = file_path.replace("\\", "/")
    match = re.search(r"/temp_(\d+)_(\d+)(/|$)", normalized)
    if not match:
        match = re.search(r"^temp_(\d+)_(\d+)(/|$)", normalized)
    return f"{match.group(1)}.{match.group(2)}" if match else "unknown"


def run_from_path(file_path: str) -> str:
    match = re.search(r"run_(\d+)", Path(file_path).name)
    return match.group(1) if match else "unknown"


def sort_temp(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 99.0


def classify_assertion(assert_text: str) -> str:
    text = assert_text.lower()

    if "status_code" in text:
        return "Status code"
    if "bookingid" in text or "booking_id" in text:
        return "Identifier"
    if "bookingdates" in text or "checkin" in text or "checkout" in text:
        return "Date/Nested field"
    if any(field in text for field in ["firstname", "lastname", "totalprice", "depositpaid", "additionalneeds"]):
        return "Field value"
    if " in " in text:
        return "Schema/existence"
    if "==" in text:
        return "Equality"
    if "is not none" in text or "!= none" in text:
        return "Non-null"

    return "Other"


def extract_tests_and_assertions(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    tests = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            doc = ast.get_docstring(node) or ""
            assertions = []

            for sub in ast.walk(node):
                if isinstance(sub, ast.Assert):
                    try:
                        text = ast.unparse(sub)
                    except Exception:
                        text = "assert (...)"

                    assertions.append(
                        {
                            "text": text,
                            "type": classify_assertion(text),
                        }
                    )

            tests.append(
                {
                    "name": node.name,
                    "scenario": doc.splitlines()[0] if doc else "",
                    "assertions": assertions,
                }
            )

    return tests


def analyze_structure(code: str) -> dict:
    return {
        "uses_parametrize": "@pytest.mark.parametrize" in code,
        "uses_fixture": "@pytest.fixture" in code,
        "uses_helpers": bool(re.search(r"def\s+(?!test_)\w+\(", code)),
    }


def structure_label(structure: dict) -> str:
    labels = []
    if structure["uses_parametrize"]:
        labels.append("Parametrize")
    if structure["uses_fixture"]:
        labels.append("Fixtures")
    if structure["uses_helpers"]:
        labels.append("Helpers")
    return ", ".join(labels) if labels else "Inline/simple"


def detect_scenario_themes(test_name: str, scenario: str, assertions: list[dict]) -> set[str]:
    combined = test_name + " " + scenario + " " + " ".join(a["text"] for a in assertions)
    combined = combined.lower()

    themes = set()
    for theme, keywords in SCENARIO_KEYWORDS.items():
        if any(keyword in combined for keyword in keywords):
            themes.add(theme)

    return themes


def avg(values: list[int]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def value_range(values: list[int]) -> str:
    if not values:
        return "0"
    if min(values) == max(values):
        return str(min(values))
    return f"{min(values)}–{max(values)}"


def format_counter(counter: Counter) -> str:
    if not counter:
        return "None"
    return ", ".join(f"{key}: {value}" for key, value in counter.most_common())


def format_list(values) -> str:
    if not values:
        return "None"
    return ", ".join(sorted(values))


def summarize(execution: list[dict]) -> dict:
    summary = defaultdict(
        lambda: {
            "files": 0,
            "syntax_valid": 0,
            "pytest_passed": 0,
            "pytest_failed": 0,
            "tests_per_file": [],
            "assertions_per_file": [],
            "structures": Counter(),
            "scenario_themes": Counter(),
            "assertion_types": Counter(),
            "test_names": [],
        }
    )

    for item in execution:
        mode = prompt_mode_from_path(item["file"])
        temp = temp_from_path(item["file"])
        key = (mode, temp)

        file_path = Path(item["file"])
        if not file_path.exists():
            continue

        code = file_path.read_text(encoding="utf-8")
        tests = extract_tests_and_assertions(code)
        structure = analyze_structure(code)
        structure_text = structure_label(structure)

        total_assertions = sum(len(t["assertions"]) for t in tests)

        summary[key]["files"] += 1
        summary[key]["syntax_valid"] += int(item.get("syntax_valid", False))
        summary[key]["pytest_passed"] += int(item.get("pytest", {}).get("passed", False))
        summary[key]["pytest_failed"] += int(not item.get("pytest", {}).get("passed", False))
        summary[key]["tests_per_file"].append(len(tests))
        summary[key]["assertions_per_file"].append(total_assertions)
        summary[key]["structures"][structure_text] += 1

        for test in tests:
            summary[key]["test_names"].append(test["name"])

            for assertion in test["assertions"]:
                summary[key]["assertion_types"][assertion["type"]] += 1

            for theme in detect_scenario_themes(test["name"], test["scenario"], test["assertions"]):
                summary[key]["scenario_themes"][theme] += 1

    return summary


def comparison_sentence(temp: str, temp_only: dict | None, temp_plus_prompt: dict | None) -> str:
    if not temp_only or not temp_plus_prompt:
        return "Both prompt modes were not available for this temperature."

    def avg_val(values):
        return sum(values) / len(values) if values else 0

    # Compute averages
    only_tests = avg_val(temp_only["tests_per_file"])
    prompt_tests = avg_val(temp_plus_prompt["tests_per_file"])

    only_asserts = avg_val(temp_only["assertions_per_file"])
    prompt_asserts = avg_val(temp_plus_prompt["assertions_per_file"])

    # Deltas
    test_delta = round(prompt_tests - only_tests, 2)
    assert_delta = round(prompt_asserts - only_asserts, 2)

    # Themes difference
    only_themes = set(temp_only["scenario_themes"].keys())
    prompt_themes = set(temp_plus_prompt["scenario_themes"].keys())

    added_themes = prompt_themes - only_themes
    removed_themes = only_themes - prompt_themes

    parts = []

    # Test count change
    if test_delta != 0:
        direction = "increased" if test_delta > 0 else "decreased"
        parts.append(f"tests {direction} by {abs(test_delta)}")

    # Assertion change
    if assert_delta != 0:
        direction = "increased" if assert_delta > 0 else "decreased"
        parts.append(f"assertions {direction} by {abs(assert_delta)}")

    # Theme changes
    if added_themes:
        parts.append(f"added themes: {', '.join(sorted(added_themes))}")

    if removed_themes:
        parts.append(f"removed themes: {', '.join(sorted(removed_themes))}")

    if not parts:
        return "No measurable difference."

    return "; ".join(parts) + "."

def build_temperature_variation_rows(summary: dict) -> str:
    rows = []

    for (mode, temp), data in sorted(summary.items(), key=lambda kv: (kv[0][0], sort_temp(kv[0][1]))):
        rows.append(
            f"""
            <tr>
                <td>{html_escape(mode)}</td>
                <td>{html_escape(temp)}</td>
                <td>{data['files']}</td>
                <td>{value_range(data['tests_per_file'])}</td>
                <td>{value_range(data['assertions_per_file'])}</td>
                <td>{html_escape(format_counter(data['structures']))}</td>
                <td>{html_escape(format_counter(data['scenario_themes']))}</td>
                <td>{html_escape(format_counter(data['assertion_types']))}</td>
            </tr>
            """
        )

    return "".join(rows)


def build_execution_rows(summary: dict) -> str:
    rows = []

    for (mode, temp), data in sorted(summary.items(), key=lambda kv: (kv[0][0], sort_temp(kv[0][1]))):
        rows.append(
            f"""
            <tr>
                <td>{html_escape(mode)}</td>
                <td>{html_escape(temp)}</td>
                <td>{data['files']}</td>
                <td>{data['syntax_valid']}</td>
                <td>{data['pytest_passed']}</td>
                <td>{data['pytest_failed']}</td>
            </tr>
            """
        )

    return "".join(rows)


def build_mode_comparison_rows(summary: dict) -> str:
    temps = sorted({temp for _, temp in summary.keys()}, key=sort_temp)
    rows = []

    for temp in temps:
        only = summary.get(("temp_only", temp))
        prompt = summary.get(("temp_plus_prompt", temp))

        rows.append(
            f"""
            <tr>
                <td>{html_escape(temp)}</td>
                <td>{html_escape(mode_summary_text(only))}</td>
                <td>{html_escape(mode_summary_text(prompt))}</td>
                <td>{html_escape(comparison_sentence(temp, only, prompt))}</td>
            </tr>
            """
        )

    return "".join(rows)


def mode_summary_text(data: dict | None) -> str:
    if not data:
        return "No data"

    return (
        f"Tests/file: {value_range(data['tests_per_file'])}; "
        f"Assertions/file: {value_range(data['assertions_per_file'])}; "
        f"Structure: {format_counter(data['structures'])}; "
        f"Themes: {format_counter(data['scenario_themes'])}"
    )


def build_sample_rows(execution: list[dict]) -> str:
    rows = []

    sorted_items = sorted(
        execution,
        key=lambda item: (
            prompt_mode_from_path(item["file"]),
            sort_temp(temp_from_path(item["file"])),
            int(run_from_path(item["file"])) if run_from_path(item["file"]).isdigit() else 99,
        ),
    )

    for item in sorted_items:
        file_path = Path(item["file"])
        if not file_path.exists():
            continue

        code = file_path.read_text(encoding="utf-8")
        tests = extract_tests_and_assertions(code)
        structure = structure_label(analyze_structure(code))

        for test in tests:
            themes = detect_scenario_themes(test["name"], test["scenario"], test["assertions"])
            assertion_types = Counter(a["type"] for a in test["assertions"])

            rows.append(
                f"""
                <tr>
                    <td>{html_escape(prompt_mode_from_path(item['file']))}</td>
                    <td>{html_escape(temp_from_path(item['file']))}</td>
                    <td>{html_escape(run_from_path(item['file']))}</td>
                    <td>{html_escape(structure)}</td>
                    <td>{html_escape(test['name'])}</td>
                    <td>{html_escape(test['scenario'])}</td>
                    <td>{html_escape(format_list(themes))}</td>
                    <td>{len(test['assertions'])}</td>
                    <td>{html_escape(format_counter(assertion_types))}</td>
                </tr>
                """
            )

    return "".join(rows)


def executive_summary(summary: dict) -> str:
    modes = sorted({mode for mode, _ in summary.keys()})
    temps = sorted({temp for _, temp in summary.keys()}, key=sort_temp)

    return (
        f"Compared {len(modes)} prompt mode(s) across {len(temps)} temperature setting(s). "
        "The report checks whether different temperatures created different tests, "
        "whether the generated tests executed successfully, and how temp-only differs from temp-plus-prompt."
    )


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    execution_file = REPORTS_DIR / "execution_results.json"
    execution = load_json(execution_file, [])
    summary = summarize(execution)

    html_report = f"""
    <html>
    <head>
        <title>AI Test Temperature Lab Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 30px;
                line-height: 1.4;
                color: #111;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 34px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 9px;
                vertical-align: top;
                text-align: left;
                font-size: 13px;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .summary {{
                background-color: #f7f7f7;
                border-left: 4px solid #999;
                padding: 12px;
                font-size: 16px;
                max-width: 1100px;
            }}
            .note {{
                color: #555;
                max-width: 1100px;
            }}
        </style>
    </head>
    <body>
        <h1>AI Test Temperature Lab Report</h1>

        <h2>Executive Summary</h2>
        <p class="summary">{html_escape(executive_summary(summary))}</p>

        <p class="note">
            Source data: {html_escape(execution_file)}.
            This report only reads execution_results.json and writes HTML.
        </p>

        <h2>1. Did Different Temperatures Create Different Tests?</h2>
        <table>
            <tr>
                <th>Prompt Mode</th>
                <th>Temperature</th>
                <th>Runs / Files</th>
                <th>Test Count Range</th>
                <th>Assertion Count Range</th>
                <th>Structure</th>
                <th>Scenario Themes</th>
                <th>Assertion Types</th>
            </tr>
            {build_temperature_variation_rows(summary)}
        </table>

        <h2>2. Did Generated Tests Execute?</h2>
        <table>
            <tr>
                <th>Prompt Mode</th>
                <th>Temperature</th>
                <th>Files</th>
                <th>Syntax Valid</th>
                <th>Pytest Passed</th>
                <th>Pytest Failed</th>
            </tr>
            {build_execution_rows(summary)}
        </table>

        <h2>3. Temp Only vs Temp + Prompt</h2>
        <table>
            <tr>
                <th>Temperature</th>
                <th>Temp Only Summary</th>
                <th>Temp + Prompt Summary</th>
                <th>Quick Difference</th>
            </tr>
            {build_mode_comparison_rows(summary)}
        </table>

        <h2>4. Generated Test Detail</h2>
        <table>
            <tr>
                <th>Mode</th>
                <th>Temp</th>
                <th>Run</th>
                <th>Structure</th>
                <th>Test Name</th>
                <th>Scenario</th>
                <th>Themes</th>
                <th>Assertion Count</th>
                <th>Assertion Types</th>
            </tr>
            {build_sample_rows(execution)}
        </table>
    </body>
    </html>
    """

    output = REPORTS_DIR / "temperature_experiment_report.html"
    output.write_text(html_report, encoding="utf-8")

    print(f"Wrote {output}")


if __name__ == "__main__":
    main()