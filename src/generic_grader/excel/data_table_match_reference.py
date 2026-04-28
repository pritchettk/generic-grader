"""Semantic table comparison — finds and matches tables by header names.

Unlike ``data_series_match_reference`` (which checks a single row/column), this
check treats the reference range as a *table* whose first row is a header row.
It then:

1. Reads the reference table (headers + data rows).
2. Locates the matching table in the submission either at the same coordinates
   (``range_matches_reference=True``) or anywhere on the sheet
   (``range_matches_reference=False``).
3. Matches reference columns to submission columns by header similarity
   (fuzzy by default; exact when ``strict_headers=True``).
4. Compares data values column-by-column, allowing column reordering unless
   ``strict_column_order=True``.
"""

import unittest

from openpyxl.utils.cell import range_boundaries
from parameterized import parameterized

from generic_grader.excel._series import _values_match
from generic_grader.excel._workbook import (
    _match_header_mapping,
    find_table_by_headers,
    load_sheet,
    read_rect_values,
    resolve_reference_file,
    resolve_sheet_and_range,
    resolve_submission_file,
)
from generic_grader.utils.decorators import merge_subtests, weighted
from generic_grader.utils.docs import get_wrapper
from generic_grader.utils.options import options_to_params


def doc_func(func, num, param):
    """Return parameterized docstring for data table match checks."""

    o = param.args[0]
    sheet = o.kwargs.get("sheet") or o.sheet or "<first worksheet>"
    start_cell, end_cell = o.entries
    location_clause = (
        "at the same location as"
        if o.range_matches_reference
        else "anywhere in the submission matching"
    )
    return (
        f"Check that the data table in range {start_cell}:{end_cell}"
        f" on sheet `{sheet}` matches {location_clause} the reference table,"
        " with columns matched by header name."
    )


def build(the_options):
    """Create a class for semantic data-table-to-reference checks."""

    the_params = options_to_params(the_options)

    class TestDataTableMatchReference(unittest.TestCase):
        """A class for semantic data table matching tests."""

        wrapper = get_wrapper()

        @parameterized.expand(the_params, doc_func=doc_func)
        @merge_subtests()
        @weighted
        def test_data_table_match_reference(self, options):
            """Check that a reference data table matches the submission."""

            o = options
            sheet, start_cell, end_cell = resolve_sheet_and_range(o)

            sub_file = resolve_submission_file(o)
            ref_file = resolve_reference_file(o)

            ref_sheet = load_sheet(ref_file, sheet, data_only=True)
            sub_sheet = load_sheet(sub_file, sheet, data_only=True)
            sheet = ref_sheet.title

            # Parse the reference range into a rectangular block.
            min_col, min_row, max_col, max_row = range_boundaries(
                f"{start_cell}:{end_cell}"
            )
            width = max_col - min_col + 1
            height = max_row - min_row + 1

            self.assertGreaterEqual(
                height,
                2,
                msg=(
                    "\n\nHint:\n"
                    + self.wrapper.fill(
                        f"Reference range {start_cell}:{end_cell} must contain at least"
                        " 2 rows (one header row and at least one data row)."
                    )
                ),
            )

            ref_block = read_rect_values(ref_sheet, min_row, min_col, height, width)
            ref_headers = ref_block[0]
            ref_data_rows = ref_block[1:]

            if o.range_matches_reference:
                # Read the same range from the submission and match columns.
                sub_block = read_rect_values(sub_sheet, min_row, min_col, height, width)
                sub_headers = sub_block[0]
                sub_data_rows = sub_block[1:]

                col_mapping = _match_header_mapping(
                    ref_headers,
                    sub_headers,
                    o.header_ratio,
                    o.strict_headers,
                    o.strict_column_order,
                )
                self.assertIsNotNone(
                    col_mapping,
                    msg=(
                        "\n\nHint:\n"
                        + self.wrapper.fill(
                            f"Could not match all reference headers to submission headers"
                            f" in range {start_cell}:{end_cell} on sheet `{sheet}`."
                            f" Reference headers: {[h for h in ref_headers if h is not None]}."
                            + (o.hint and f"  {o.hint}" or "")
                        )
                    ),
                )

            else:
                # Semantic search: scan the whole sheet for a matching header row.
                result = find_table_by_headers(
                    sub_sheet,
                    ref_headers,
                    o.header_ratio,
                    o.strict_headers,
                    o.strict_column_order,
                )
                self.assertIsNotNone(
                    result,
                    msg=(
                        "\n\nHint:\n"
                        + self.wrapper.fill(
                            "Could not find a table with headers matching"
                            f" {[h for h in ref_headers if h is not None]}"
                            f" anywhere on sheet `{sheet}`."
                            + (o.hint and f"  {o.hint}" or "")
                        )
                    ),
                )

                header_row_1based, col_start_1based, col_mapping = result

                available_rows = sub_sheet.max_row - header_row_1based
                self.assertGreaterEqual(
                    available_rows,
                    len(ref_data_rows),
                    msg=(
                        "\n\nHint:\n"
                        + self.wrapper.fill(
                            f"The table found on sheet `{sheet}` does not have enough"
                            f" data rows below the header."
                            f" Expected {len(ref_data_rows)} data row(s),"
                            f" but only {available_rows} row(s) are available."
                            + (o.hint and f"  {o.hint}" or "")
                        )
                    ),
                )

                sub_block = read_rect_values(
                    sub_sheet,
                    header_row_1based,
                    col_start_1based,
                    height,
                    width,
                )
                sub_data_rows = sub_block[1:]

            # Compare data values column-by-column using the header mapping.
            for ref_col_idx, sub_col_idx in col_mapping.items():
                ref_header = ref_headers[ref_col_idx]
                for row_offset, (ref_row, sub_row) in enumerate(
                    zip(ref_data_rows, sub_data_rows, strict=True), start=2
                ):
                    with self.subTest(header=ref_header, row=row_offset):
                        ref_val = ref_row[ref_col_idx]
                        sub_val = sub_row[sub_col_idx]
                        self.assertTrue(
                            _values_match(
                                ref_val,
                                sub_val,
                                o.relative_tolerance,
                                o.absolute_tolerance,
                            ),
                            msg=(
                                "\n\nHint:\n"
                                + self.wrapper.fill(
                                    f"Data mismatch in column `{ref_header}`,"
                                    f" row {row_offset} on sheet `{sheet}`."
                                    f" Expected {ref_val!r}, got {sub_val!r}."
                                    + (o.hint and f"  {o.hint}" or "")
                                )
                            ),
                        )

            self.set_score(self, o.weight)

    return TestDataTableMatchReference
