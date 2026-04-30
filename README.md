# AI Test Temperature Lab

A practical experiment repo for studying how LLM temperature affects AI-generated API tests.

The goal is simple:

```text
Same requirement
Same API contract
Same prompt
Different temperature settings
Repeated generations
Compare the generated tests
```

This repo is designed to help answer questions like:

- Does `temperature=0` produce repeatable test code?
- Does a higher temperature produce more scenario variety?
- Does variety improve coverage or introduce more noise?
- How often do generated tests have syntax, framework, or assertion problems?
- What changes between generation runs when only temperature changes?

## Experiment Flow

```text
Requirement + API contract + prompt template
        ↓
Generate pytest tests at multiple temperatures
        ↓
Save generated tests as artifacts
        ↓
Run syntax checks and pytest
        ↓
Compare generated tests for similarity and variation
        ↓
Generate a report
```

## Project Structure

```text
ai-test-temperature-lab/
  requirements/
    create_booking.md
  api_contracts/
    restful_booker_contract.json
  prompts/
    api_test_prompt.txt
  generated_tests/
    .gitkeep
  reports/
    .gitkeep
  src/
    config.py
    generate_tests.py
    run_tests.py
    compare_tests.py
    score_tests.py
    make_report.py
  tests/
    test_scoring.py
  .env.example
  .gitignore
  requirements.txt
  README.md
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Add your OpenAI API key to `.env`:

```bash
OPENAI_API_KEY=your_key_here
```

## Run the Experiment

Generate tests across temperatures:

```bash
python -m src.generate_tests
```

Run syntax checks and pytest against generated files:

```bash
python -m src.run_tests
```

Compare generated tests:

```bash
python -m src.compare_tests
```

Generate HTML report:

```bash
python -m src.make_report
```

Open:

```text
reports/temperature_experiment_report.html
```

## Default Temperatures

The default experiment runs these temperatures:

```python
[0.0, 0.2, 0.5, 0.8, 1.0]
```

Each temperature runs multiple generations so you can compare variation across runs.

You can edit these in `src/config.py`.

## What This Repo Measures

For each generated test file, the repo captures:

- syntax validity
- pytest collection/execution result
- number of test functions
- number of assertions
- generated code size
- similarity between generated files
- simple keyword-based coverage indicators

This is intentionally lightweight. The purpose is not to perfectly grade test quality. The purpose is to make variation observable.

## Important Notes

This project does not claim that temperature is the only source of variation. Even with low temperature, LLM output may still vary depending on model behavior, prompt structure, input formatting, and backend changes.

The working thesis:

```text
Low temperature improves repeatability.
Higher temperature may increase scenario diversity.
Neither eliminates the need for evaluation.
```

## Suggested Article / Talk Angle

**Temperature ≠ Determinism: What Happens When AI Generates Tests at Different Settings**

Core message:

> Turning temperature down may make AI-generated tests more stable, but stability is not the same as trust. Turning it up may create more interesting scenarios, but variety is not the same as coverage.
