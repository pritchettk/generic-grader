"""Shared workbook helpers for excel checks."""

import glob

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
    """Resolve submission workbook from required_files or sub_module."""

    if options.required_files:
        return resolve_single_file(options.required_files, "submission")

    if options.sub_module:
        return resolve_single_file((f"{options.sub_module}*.xlsx",), "submission")

    raise ValueError("No submission file pattern provided.")


def resolve_reference_file(options: Options) -> str:
    """Resolve reference workbook from kwargs['reference_file'] or ref_module."""

    explicit_reference = options.kwargs.get("reference_file")
    if explicit_reference:
        return resolve_single_file((explicit_reference,), "reference")

    ref_module = options.ref_module
    if not ref_module:
        raise ValueError(
            "No reference file provided. Set `kwargs['reference_file']`"
            " or `ref_module`.")

    if any(char in ref_module for char in "*?[]"):
        return _resolve_from_patterns((ref_module,), "reference")

    candidate_patterns = (
        ref_module,
        f"{ref_module}.xlsx",
        f"{ref_module.replace('.', '/')}.xlsx",
    )
    return _resolve_from_patterns(candidate_patterns, "reference")
