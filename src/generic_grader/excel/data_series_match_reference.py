"""Test that a reference data series matches somewhere in a submission workbook."""

import unittest

from openpyxl.utils.cell import range_boundaries
from parameterized import parameterized

from generic_grader.excel._series import (
    extract_series_from_range,
    find_best_series_window,
    find_exact_series_window,
)
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
    """Return parameterized docstring for data series match checks."""

    o = param.args[0]
    sheet = o.kwargs.get("sheet", o.sheet)
    start_cell, end_cell = o.entries
    require_formulas = o.series_require_formulas
    formula_suffix = " and uses formulas" if require_formulas else ""
    return (
        f"Check that the data series in range {start_cell}:{end_cell}"
        f" on sheet `{sheet}` exactly matches somewhere in the submission workbook"
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
    """Create a class for data series matching checks."""

    the_params = options_to_params(the_options)

    class TestDataSeriesMatchReference(unittest.TestCase):
        """A class for data series matching tests."""

        wrapper = get_wrapper()

        @parameterized.expand(the_params, doc_func=doc_func)
        @merge_subtests()
        @weighted
        def test_data_series_match_reference(self, options):
            """Check that reference data series exactly matches submission."""

            o = options
            sheet, start_cell, end_cell = resolve_sheet_and_range(o)

            sub_file = resolve_submission_file(o)
            reference_file = resolve_reference_file(o)

            ref_sheet = load_sheet(reference_file, sheet, data_only=True)
            sub_sheet = load_sheet(sub_file, sheet, data_only=True)

            series = extract_series_from_range(ref_sheet, start_cell, end_cell)
            search_orientation = o.kwargs.get("search_orientation", "either")
            require_formulas = o.series_require_formulas

            if require_formulas and all(value is None for value in series["values"]):
                ref_sheet_formulas = load_sheet(reference_file, sheet, data_only=False)
                sub_sheet = load_sheet(sub_file, sheet, data_only=False)
                series = extract_series_from_range(ref_sheet_formulas, start_cell, end_cell)

            exact_match = find_exact_series_window(
                sub_sheet,
                series["values"],
                search_orientation,
                o.relative_tolerance,
                o.absolute_tolerance,
            )

            if exact_match is None:
                best_match = find_best_series_window(
                    sub_sheet,
                    series["values"],
                    search_orientation,
                    o.relative_tolerance,
                    o.absolute_tolerance,
                )

                if best_match is None:
                    self.fail(
                        "\n\nHint:\n"
                        + self.wrapper.fill(
                            "Could not find any candidate location for the"
                            f" series from `{series['start_cell']}:{series['end_cell']}`"
                            f" on sheet `{sheet}`."
                            + (o.hint and f"  {o.hint}" or "")
                        )
                    )

                self.fail(
                    "\n\nHint:\n"
                    + self.wrapper.fill(
                        f"No exact data series match was found for"
                        f" `{series['start_cell']}:{series['end_cell']}` on sheet `{sheet}`."
                        " Best candidate was"
                        f" `{best_match['start_cell']}:{best_match['end_cell']}`"
                        f" ({best_match['orientation']}) with"
                        f" ratio {best_match['ratio']:.2f}."
                        + (o.hint and f"  {o.hint}" or "")
                    )
                )

            if require_formulas:
                sub_sheet_formulas = load_sheet(sub_file, sheet, data_only=False)
                for row, col in _iter_series_coordinates(exact_match):
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

    return TestDataSeriesMatchReference
