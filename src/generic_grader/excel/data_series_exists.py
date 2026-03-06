"""Test that a reference data series exists in a submission workbook."""

import unittest

from openpyxl.utils.cell import range_boundaries
from parameterized import parameterized

from generic_grader.excel._series import extract_series_from_range, find_best_series_window
from generic_grader.excel._workbook import (
    load_sheet,
    resolve_reference_file,
    resolve_sheet_and_range,
    resolve_submission_file,
)
from generic_grader.utils.decorators import merge_subtests, weighted
from generic_grader.utils.docs import get_wrapper
from generic_grader.utils.options import options_to_params


def doc_func(func, num, param):
    """Return parameterized docstring for data series existence checks."""

    o = param.args[0]
    sheet = o.kwargs.get("sheet", o.sheet)
    start_cell, end_cell = o.entries
    require_formulas = o.kwargs.get(
        "series_require_formulas",
        o.kwargs.get("require_formulas", False),
    )
    formula_suffix = " and uses formulas" if require_formulas else ""
    return (
        f"Check that the data series in range {start_cell}:{end_cell}"
        f" on sheet `{sheet}` exists somewhere in the submission workbook"
        f"{formula_suffix}."
    )


def _iter_series_coordinates(match: dict):
    min_col, min_row, max_col, max_row = range_boundaries(
        f"{match['start_cell']}:{match['end_cell']}"
    )

    if match["orientation"] == "row":
        for col in range(min_col, max_col + 1):
            yield min_row, col
        return

    for row in range(min_row, max_row + 1):
        yield row, min_col


def build(the_options):
    """Create a class for data series existence checks."""

    the_params = options_to_params(the_options)

    class TestDataSeriesExists(unittest.TestCase):
        """A class for data series existence tests."""

        wrapper = get_wrapper()

        @parameterized.expand(the_params, doc_func=doc_func)
        @merge_subtests()
        @weighted
        def test_data_series_exists(self, options):
            """Check that reference data series exists in submission sheet."""

            o = options
            sheet, start_cell, end_cell = resolve_sheet_and_range(o)

            sub_file = resolve_submission_file(o)
            reference_file = resolve_reference_file(o)

            ref_sheet = load_sheet(reference_file, sheet, data_only=True)
            sub_sheet = load_sheet(sub_file, sheet, data_only=True)

            require_formulas = o.kwargs.get(
                "series_require_formulas",
                o.kwargs.get("require_formulas", False),
            )
            if not isinstance(require_formulas, bool):
                raise ValueError(
                    "`kwargs['series_require_formulas']` must be a boolean."
                )

            series = extract_series_from_range(ref_sheet, start_cell, end_cell)
            search_orientation = o.kwargs.get("search_orientation", "either")

            if require_formulas and all(value is None for value in series["values"]):
                ref_sheet_formulas = load_sheet(reference_file, sheet, data_only=False)
                sub_sheet = load_sheet(sub_file, sheet, data_only=False)
                series = extract_series_from_range(ref_sheet_formulas, start_cell, end_cell)

            best_match = find_best_series_window(
                sub_sheet,
                series["values"],
                search_orientation,
                o.relative_tolerance,
                o.absolute_tolerance,
            )

            self.assertIsNotNone(
                best_match,
                msg=(
                    "\n\nHint:\n"
                    + self.wrapper.fill(
                        "Could not find any candidate location for the"
                        f" series from `{series['start_cell']}:{series['end_cell']}`"
                        f" on sheet `{sheet}`."
                        + (o.hint and f"  {o.hint}" or "")
                    )
                ),
            )

            self.assertGreaterEqual(
                best_match["ratio"],
                o.ratio,
                msg=(
                    "\n\nHint:\n"
                    + self.wrapper.fill(
                        f"Could not find data series from `{series['start_cell']}:{series['end_cell']}`"
                        f" on sheet `{sheet}` with at least {o.ratio:.2f} match ratio."
                        " Best match was"
                        f" `{best_match['start_cell']}:{best_match['end_cell']}`"
                        f" ({best_match['orientation']}) with"
                        f" ratio {best_match['ratio']:.2f}."
                        + (o.hint and f"  {o.hint}" or "")
                    )
                ),
            )

            if require_formulas:
                sub_sheet_formulas = load_sheet(sub_file, sheet, data_only=False)
                for row, col in _iter_series_coordinates(best_match):
                    with self.subTest(row=row, column=col):
                        cell = sub_sheet_formulas.cell(row, col)
                        is_formula = isinstance(cell.value, str) and cell.value.startswith("=")
                        self.assertTrue(
                            is_formula,
                            msg=(
                                "\n\nHint:\n"
                                + self.wrapper.fill(
                                    f"Matched series cell `{cell.coordinate}` on sheet `{sheet}`"
                                    " is not a formula cell."
                                    + (o.hint and f"  {o.hint}" or "")
                                )
                            ),
                        )

            self.set_score(self, o.weight)

    return TestDataSeriesExists
