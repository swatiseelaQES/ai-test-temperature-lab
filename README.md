# AI Test Temperature Lab

## Overview

This project explores how **LLM temperature** and **prompt design** influence automated test generation.

The goal is to answer three practical questions:

1. Do different temperatures generate different tests?
2. Do the generated tests actually run?
3. How does **temperature-only prompting** compare with **structured prompting**?

This is a **test generation experiment**, not a test accuracy benchmark.

---
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
## Edit you configuration file 

PROMPT_MODE = "temp_only"
# or
PROMPT_MODE = "temp_plus_prompt"

## Run the Experiment

Generate tests across temperatures:

```bash
python -m src.generate_tests
```

Run syntax checks and pytest against generated files:

```bash
python -m src.run_tests
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
[0.0, 0.25, 0.5, 0.75, 1.0, 1.5]
```

Each temperature runs multiple generations so you can compare variation across runs.

You can edit these in `src/config.py`.

