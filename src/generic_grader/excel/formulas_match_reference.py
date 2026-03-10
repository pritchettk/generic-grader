"""Test that spreadsheet formulas match a reference workbook."""

import unittest

from parameterized import parameterized

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
    """Return parameterized docstring for formula matching checks."""

    o = param.args[0]
    sheet = o.kwargs.get("sheet", o.sheet)
    start_cell, end_cell = o.entries
    return (
        f"Check that formulas in range {start_cell}:{end_cell}"
        f" on sheet `{sheet}` exactly match the reference formulas."
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

            self.set_score(self, o.weight)

    return TestFormulasMatchReference
