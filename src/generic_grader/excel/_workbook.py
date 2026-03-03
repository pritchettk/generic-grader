"""Shared workbook helpers for excel checks."""

import glob

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
