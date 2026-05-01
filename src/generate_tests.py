import hashlib
import json
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from src.config import (
    API_CONTRACT_FILE,
    GENERATED_TESTS_DIR,
    OPENAI_MODEL,
    PROMPT_MODE,
    PROMPT_FILES,
    PROMPTS_DIR,
    REQUIREMENT_FILE,
    RUNS_PER_TEMPERATURE,
    TEMPERATURES,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def get_prompt_template_file() -> Path:
    if PROMPT_MODE not in PROMPT_FILES:
        valid_modes = ", ".join(PROMPT_FILES.keys())
        raise ValueError(
            f"Invalid PROMPT_MODE '{PROMPT_MODE}'. Valid options are: {valid_modes}"
        )

    return PROMPTS_DIR / PROMPT_FILES[PROMPT_MODE]


def build_prompt() -> str:
    requirement = read_text(REQUIREMENT_FILE)
    api_contract = read_text(API_CONTRACT_FILE)
    template = read_text(get_prompt_template_file())
    return template.format(requirement=requirement, api_contract=api_contract)


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def generate_test(client: OpenAI, prompt: str, temperature: float) -> str:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": "You generate clean, executable pytest code."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def clean_code(code: str) -> str:
    code = code.strip()

    if code.startswith("```python"):
        code = code.removeprefix("```python").strip()

    if code.startswith("```"):
        code = code.removeprefix("```").strip()

    if code.endswith("```"):
        code = code.removesuffix("```").strip()

    return code


def main() -> None:
    http_client = httpx.Client(
        verify=False,
        timeout=httpx.Timeout(20.0, connect=10.0),
    )

    load_dotenv()
    client = OpenAI(http_client=http_client)

    prompt_template_file = get_prompt_template_file()
    prompt = build_prompt()
    prompt_hash = stable_hash(prompt)

    mode_output_dir = GENERATED_TESTS_DIR / PROMPT_MODE
    mode_output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "model": OPENAI_MODEL,
        "prompt_mode": PROMPT_MODE,
        "prompt_template_file": str(prompt_template_file),
        "prompt_hash": prompt_hash,
        "temperatures": TEMPERATURES,
        "runs_per_temperature": RUNS_PER_TEMPERATURE,
        "generated_files": [],
    }

    for temperature in TEMPERATURES:
        temp_label = str(temperature).replace(".", "_")
        temp_dir = mode_output_dir / f"temp_{temp_label}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        for run_id in range(1, RUNS_PER_TEMPERATURE + 1):
            print(
                f"Generating test: prompt_mode={PROMPT_MODE}, "
                f"temperature={temperature}, run={run_id}"
            )

            code = clean_code(generate_test(client, prompt, temperature))

            output_file = temp_dir / f"test_generated_run_{run_id}.py"
            output_file.write_text(code + "\n", encoding="utf-8")

            manifest["generated_files"].append(
                {
                    "prompt_mode": PROMPT_MODE,
                    "temperature": temperature,
                    "run_id": run_id,
                    "file": str(output_file.relative_to(GENERATED_TESTS_DIR.parent)),
                }
            )

    manifest_file = mode_output_dir / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote manifest: {manifest_file}")


if __name__ == "__main__":
    main()