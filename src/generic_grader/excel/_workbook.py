"""Shared workbook helpers for excel checks."""

import glob
from pathlib import Path

from generic_grader.utils.options import Options

from openpyxl import load_workbook


def resolve_single_file(file_patterns: tuple[str, ...], label: str) -> str:
    """Resolve exactly one file from a tuple of file patterns."""

    if not file_patterns:
        raise ValueError(f"No {label} file pattern provided.")

    pattern = file_patterns[0]
    matches = glob.glob(pattern)

    if len(matches) == 0:
        raise FileNotFoundError(
            f'Could not find a {label} file matching pattern "{pattern}".'
        )

    if len(matches) > 1:
        raise ValueError(
            f'Found multiple {label} files matching pattern "{pattern}".'
        )

    return matches[0]


def resolve_sheet_and_range(options):
    """Read sheet and cell-range settings from Options."""

    if len(options.entries) != 2:
        raise ValueError(
            "Excel checks require `entries=(start_cell, end_cell)`,"
            " e.g. ('A1', 'C4')."
        )

    sheet = options.kwargs.get("sheet", "Sheet")
    start_cell, end_cell = options.entries
    return sheet, start_cell, end_cell


def load_sheet(path: str, sheet: str, data_only: bool):
    """Load a workbook and return the requested sheet."""

    workbook = load_workbook(filename=path, data_only=data_only)
    return workbook[sheet]


def _resolve_from_patterns(patterns: tuple[str, ...], label: str) -> str:
    """Resolve exactly one file from multiple candidate patterns."""

    if not patterns:
        raise ValueError(f"No {label} file pattern provided.")

    matches = []
    for pattern in patterns:
        matches.extend(glob.glob(pattern))

    matches = list(dict.fromkeys(matches))

    if len(matches) == 0:
        pattern_str = '", "'.join(patterns)
        raise FileNotFoundError(
            f'Could not find a {label} file matching any pattern in ("{pattern_str}").'
        )

    if len(matches) > 1:
        pattern_str = '", "'.join(patterns)
        raise ValueError(
            f'Found multiple {label} files matching patterns in ("{pattern_str}").'
        )

    return matches[0]


def resolve_submission_file(options: Options) -> str:
    """Resolve submission workbook from sub_module or required_files."""

    if options.sub_module:
        return resolve_module_workbook(options.sub_module, "submission")

    if options.required_files:
        return resolve_single_file(options.required_files, "submission")

    raise ValueError("No submission file pattern provided.")


def resolve_reference_file(options: Options) -> str:
    """Resolve reference workbook from ref_module or kwargs['reference_file']."""

    default_ref_module = Options().ref_module
    if options.ref_module and options.ref_module != default_ref_module:
        return resolve_module_workbook(options.ref_module, "reference")

    explicit_reference = options.kwargs.get("reference_file")
    if explicit_reference:
        return resolve_single_file((explicit_reference,), "reference")

    raise ValueError(
        "No reference file provided. Set `ref_module`"
        " or `kwargs['reference_file']`.")


def resolve_module_workbook(module: str, label: str) -> str:
    """Resolve an exact workbook path from module-like syntax."""

    if not module:
        raise ValueError(f"No {label} module provided.")

    if any(char in module for char in "*?[]"):
        return _resolve_from_patterns((module,), label)

    candidate_paths = [
        module,
        f"{module}.xlsx",
        f"{module.replace('.', '/')}.xlsx",
        f"{module.replace('.', str(Path('/')))}.xlsx",
    ]

    existing_paths = {}
    for candidate in candidate_paths:
        candidate_path = Path(candidate)
        if candidate_path.is_file():
            normalized = str(candidate_path.resolve())
            existing_paths[normalized] = str(candidate_path)

    existing_paths = list(existing_paths.values())

    if len(existing_paths) == 0:
        candidate_str = '", "'.join(candidate_paths)
        raise FileNotFoundError(
            f'Could not find a {label} file from module "{module}".'
            f' Tried ("{candidate_str}").'
        )

    if len(existing_paths) > 1:
        candidate_str = '", "'.join(existing_paths)
        raise ValueError(
            f'Found multiple {label} files for module "{module}"'
            f' in ("{candidate_str}").'
        )

    return existing_paths[0]
