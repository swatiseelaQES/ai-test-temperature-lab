from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT_DIR / "prompts"
REQUIREMENT_FILE = ROOT_DIR / "requirements" / "create_booking.md"
API_CONTRACT_FILE = ROOT_DIR / "api_contracts" / "restful_booker_contract.json"
GENERATED_TESTS_DIR = ROOT_DIR / "generated_tests"
REPORTS_DIR = ROOT_DIR / "reports"

PROMPT_MODE = "temp_plus_prompt" #"temp_only"


PROMPT_FILES = {
    "temp_only": "api_test_prompt_temp_only.txt",
    "temp_plus_prompt": "api_test_prompt_temp_plus_prompt.txt",
}

TEMPERATURES = [0.0, 0.25, 0.75, 1.0, 1.5]
RUNS_PER_TEMPERATURE = 1

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


