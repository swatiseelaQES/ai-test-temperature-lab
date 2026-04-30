from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
REQUIREMENT_FILE = ROOT_DIR / "requirements" / "create_booking.md"
API_CONTRACT_FILE = ROOT_DIR / "api_contracts" / "restful_booker_contract.json"
PROMPT_TEMPLATE_FILE = ROOT_DIR / "prompts" / "api_test_prompt.txt"
GENERATED_TESTS_DIR = ROOT_DIR / "generated_tests"
REPORTS_DIR = ROOT_DIR / "reports"

TEMPERATURES = [0.0, 0.2, 0.5, 0.8, 1.0]
RUNS_PER_TEMPERATURE = 3

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
