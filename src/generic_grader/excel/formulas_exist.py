"""Test that target spreadsheet cells contain formulas."""

import unittest

from parameterized import parameterized

from generic_grader.excel._workbook import (
    iter_rect_windows,
    load_sheet,
    range_shape,
    read_rect_values,
    resolve_sheet_and_range,
    resolve_submission_file,
)
from generic_grader.utils.decorators import merge_subtests, weighted
from generic_grader.utils.docs import get_wrapper
from generic_grader.utils.options import options_to_params


def doc_func(func, num, param):
    """Return parameterized docstring for formula-existence checks."""

    o = param.args[0]
    sheet = o.kwargs.get("sheet") or o.sheet or "<first worksheet>"
    start_cell, end_cell = o.entries
    location_clause = (
        "use formulas"
        if o.range_matches_reference
        else "have a same-sized formula-only region somewhere in the submission workbook"
    )
    return (
        f"Check that cells in range {start_cell}:{end_cell}"
        f" on sheet `{sheet}` {location_clause}."
    )


def build(the_options):
    """Create a class for excel formula-existence checks."""

    the_params = options_to_params(the_options)

    class TestFormulasExist(unittest.TestCase):
        """A class for formula-existence tests."""

        wrapper = get_wrapper()

        @parameterized.expand(the_params, doc_func=doc_func)
        @merge_subtests()
        @weighted
        def test_formulas_exist(self, options):
            """Check that cells are formula-based."""

            o = options
            sheet, start_cell, end_cell = resolve_sheet_and_range(o)

            sub_file = resolve_submission_file(o)
            sub_sheet = load_sheet(sub_file, sheet, data_only=False)

            if o.range_matches_reference:
                for row in sub_sheet[start_cell:end_cell]:
                    for cell in row:
                        with self.subTest(cell=cell):
                            cell_value = cell.value
                            has_formula = isinstance(cell_value, str) and cell_value.startswith("=")

                            message = (
                                "\n\nHint:\n"
                                + self.wrapper.fill(
                                    f"Cell {cell.coordinate} on sheet `{sheet}`"
                                    " does not contain a formula."
                                    + (o.hint and f"  {o.hint}" or "")
                                )
                            )
                            self.assertTrue(has_formula, msg=message)
            else:
                height, width = range_shape(start_cell, end_cell)
                match_found = False

                for win_row, win_col in iter_rect_windows(sub_sheet, height, width):
                    candidate = read_rect_values(sub_sheet, win_row, win_col, height, width)
                    all_formulas = all(
                        isinstance(value, str) and value.startswith("=")
                        for row_values in candidate
                        for value in row_values
                    )
                    if all_formulas:
                        match_found = True
                        break

                self.assertTrue(
                    match_found,
                    msg=(
                        "\n\nHint:\n"
                        + self.wrapper.fill(
                            f"Could not find any {height}x{width} formula-only region"
                            f" on sheet `{sheet}`."
                            + (o.hint and f"  {o.hint}" or "")
                        )
                    ),
                )

            self.set_score(self, o.weight)

    return TestFormulasExist
