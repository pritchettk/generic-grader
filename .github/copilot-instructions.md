# Copilot instructions for `generic-grader`

## Purpose and architecture
- This package provides **parameterizable autograder test generators**. Each module exposes a `build(...)` function that returns a `unittest.TestCase` subclass configured with `parameterized.expand` cases.
- Main code lives in `src/generic_grader/` and is grouped by domain: `class_`, `excel`, `file`, `function`, `image`, `output`, `style`, plus shared helpers in `utils`.
- Core execution model compares a submission module to a reference module using simulated I/O users (`RefUser` and `SubUser`) and structured options.
- The center of configuration is `Options` in `src/generic_grader/utils/options.py` (attrs-based, frozen, kw-only, strict runtime type checks in `__attrs_post_init__`).

## Key patterns to follow when editing/adding checks
- Implement new checks as `build(the_options)` returning a nested `Test...` class (see `src/generic_grader/output/output_values_match_reference.py`).
- Convert incoming options with `options_to_params(...)` so both single `Options` and iterables are supported.
- Decorator stack should match existing order for the check type:
  - `@parameterized.expand(...)`
  - `@merge_subtests()` when assertions are per-cell/per-item (see excel checks)
  - `@weighted`
- Use `@reference_test` only for checks that execute callable code and compare reference/submission runs.
- Build failure messages as student-facing hints with `get_wrapper()`, `make_call_str(...)`, and `ordinalize(...)` from `utils/docs.py`.
- Set full credit only on success via `self.set_score(self, o.weight)` (injected by `@weighted`).

## Reference/submission flow (important)
- `@reference_test` in `src/generic_grader/utils/reference_test.py` performs orchestration:
  - optional `o.init(self, o)`
  - run reference object, compute log limit, rename produced files to `ref_<name>`
  - run submission object with evolved options, rename files to `sub_<name>`
  - then run the decorated assertion body
- `src/generic_grader/utils/user.py` captures stdout/input, enforces entry exhaustion rules, and formats rich log output for assertion failures.
- If your check depends on generated files, rely on `o.filenames` and this rename contract.

## Excel check conventions
- Excel checks live in `src/generic_grader/excel/` and use shared path/range helpers in `src/generic_grader/excel/_workbook.py`.
- For module-style configs, resolve workbooks from exact names (Python-test style):
  - submission: `sub_module` -> `<sub_module>.xlsx` (fallback `required_files`)
  - reference: `ref_module` -> module-path `.xlsx` (fallback `kwargs['reference_file']`)
- Use `entries=(start_cell, end_cell)` and `kwargs['sheet']` (default `"Sheet"`) for target ranges.
- For formula checks, load with `data_only=False`; for value checks, load with `data_only=True`.
- Keep assertions inside `self.subTest(...)` loops so per-cell failures are grouped under one parameterized test.

## Test and development workflow
- Install dev environment: `pip install -e .[dev]` (or `uv sync --extra dev`).
- Run full tests with coverage: `pytest` (configured in `pyproject.toml` with `--cov=generic_grader --cov=tests`).
- Run targeted tests while iterating, e.g.:
  - `pytest tests/output/test_output_values_match_reference.py`
  - `pytest tests/utils/test_reference_test.py`
  - `pytest tests/excel/test_data_match_reference.py tests/excel/test_formulas_exist.py tests/excel/test_formulas_match_reference.py`
- Build package via `make` (uses `./.env3.11/bin/python` if present) or `python -m build`.

## Project-specific conventions
- Keep tests predominantly in `pytest` style, but generated classes must subclass `unittest.TestCase` to integrate with `gradescope-utils` weighting metadata.
- Prefer `attrs.evolve(...)` for modifying immutable `Options` in flow code.
- Preserve actionable, specific failure hints; include function call shape and, when relevant, simulated I/O logs.
- Do not bypass `Options` validation with ad-hoc dicts; extend `Options` fields when introducing new knobs.

## Integration dependencies to remember
- Runtime integrations include: `gradescope-utils`, `parameterized`, `attrs`, `openpyxl`, `numpy/scipy`, `matplotlib`, `Pillow`, `pytesseract`.
- OCR/image tests require system tools documented in `README.md` (`tesseract-ocr`, `ghostscript`) during local development.