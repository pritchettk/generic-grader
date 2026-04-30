"""Test that spreadsheet formulas match a reference workbook."""

import unittest

from parameterized import parameterized

from generic_grader.excel._workbook import (
    iter_rect_windows,
    load_sheet,
    range_shape,
    read_rect_values,
    resolve_reference_file,
    resolve_sheet_and_range,
    resolve_submission_file,
)
from generic_grader.utils.decorators import merge_subtests, weighted
from generic_grader.utils.docs import get_wrapper
from generic_grader.utils.options import options_to_params


def doc_func(func, num, param):
    """Return parameterized docstring for formula matching checks."""

    o = param.args[0]
    sheet = o.kwargs.get("sheet") or o.sheet or "<first worksheet>"
    start_cell, end_cell = o.entries
    location_clause = (
        "exactly match the reference formulas"
        if o.range_matches_reference
        else "match the reference formulas in a same-sized region somewhere in the submission workbook"
    )
    return (
        f"Check that formulas in range {start_cell}:{end_cell}"
        f" on sheet `{sheet}` {location_clause}."
    )


def build(the_options):
    """Create a class for excel formula-to-reference checks."""

    the_params = options_to_params(the_options)

    class TestFormulasMatchReference(unittest.TestCase):
        """A class for formula matching tests."""

        wrapper = get_wrapper()

        @parameterized.expand(the_params, doc_func=doc_func)
        @merge_subtests()
        @weighted
        def test_formulas_match_reference(self, options):
            """Check that formula text matches reference formula text."""

            o = options
            sheet, start_cell, end_cell = resolve_sheet_and_range(o)

            sub_file = resolve_submission_file(o)
            reference_file = resolve_reference_file(o)

            ref_sheet = load_sheet(reference_file, sheet, data_only=False)
            sub_sheet = load_sheet(sub_file, sheet, data_only=False)

            if o.range_matches_reference:
                for row in sub_sheet[start_cell:end_cell]:
                    for sub_cell in row:
                        with self.subTest(sub_cell=sub_cell):
                            ref_cell = ref_sheet.cell(sub_cell.row, sub_cell.column)

                            message = (
                                "\n\nHint:\n"
                                + self.wrapper.fill(
                                    f"Formula in cell {sub_cell.coordinate} on sheet `{sheet}`"
                                    " does not match the reference formula."
                                    + (o.hint and f"  {o.hint}" or "")
                                )
                            )
                            self.assertEqual(ref_cell.value, sub_cell.value, msg=message)
            else:
                height, width = range_shape(start_cell, end_cell)
                ref_values = [
                    [cell.value for cell in row]
                    for row in ref_sheet[start_cell:end_cell]
                ]

                match_found = False
                for win_row, win_col in iter_rect_windows(sub_sheet, height, width):
                    candidate_values = read_rect_values(sub_sheet, win_row, win_col, height, width)
                    if candidate_values == ref_values:
                        match_found = True
                        break

                self.assertTrue(
                    match_found,
                    msg=(
                        "\n\nHint:\n"
                        + self.wrapper.fill(
                            f"Could not find a {height}x{width} formula region on sheet `{sheet}`"
                            " that exactly matches the reference formulas."
                            + (o.hint and f"  {o.hint}" or "")
                        )
                    ),
                )

            self.set_score(self, o.weight)

    return TestFormulasMatchReference
