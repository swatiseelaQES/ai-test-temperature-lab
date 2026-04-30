import ast
import re
from pathlib import Path
from typing import Any


def is_syntax_valid(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def count_test_functions(code: str) -> int:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    )


def count_assertions(code: str) -> int:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.Assert))


def keyword_coverage(code: str) -> dict[str, bool]:
    lowered = code.lower()
    return {
        "valid_booking": "booking" in lowered and "post" in lowered,
        "status_code": "status_code" in lowered,
        "bookingid": "bookingid" in lowered,
        "nested_booking": "['booking']" in code or '["booking"]' in code,
        "missing_required": "missing" in lowered or "required" in lowered,
        "invalid_date": "checkout" in lowered and "checkin" in lowered and "invalid" in lowered,
    }


def score_file(path: Path) -> dict[str, Any]:
    code = path.read_text(encoding="utf-8")
    coverage = keyword_coverage(code)
    return {
        "file": str(path),
        "syntax_valid": is_syntax_valid(code),
        "test_function_count": count_test_functions(code),
        "assertion_count": count_assertions(code),
        "line_count": len(code.splitlines()),
        "coverage_keywords": coverage,
        "coverage_keyword_count": sum(coverage.values()),
    }
