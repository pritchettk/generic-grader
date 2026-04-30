import unittest

from generic_grader.excel import (
    chart_metadata_match_reference,
    data_table_match_reference,
    formulas_exist,
)
from generic_grader.utils.file_set_up import file_set_up
from generic_grader.utils.options import Options


# Example assignment assumptions:
# - Students submit exactly one workbook matching student_report*.xlsx.
# - The instructor provides tests/reference_report.xlsx as the reference workbook.
# - The workbook contains a Summary sheet with a sales table and a chart.


REFERENCE_FILE = "tests/reference_report.xlsx"
SUBMISSION_FILE = "student_report*.xlsx"


test_01_TestSummaryTable = data_table_match_reference.build(
    Options(
        weight=10,
        required_files=(SUBMISSION_FILE,),
        sheet="Summary",
        entries=("A1", "D6"),
        range_matches_reference=False,
        header_ratio=0.9,
        strict_headers=False,
        strict_column_order=False,
        absolute_tolerance=0.01,
        kwargs={"reference_file": REFERENCE_FILE},
        hint=(
            "Your summary table can appear anywhere on the sheet, but the"
            " headers and values must still match the required report."
        ),
    )
)


test_02_TestSummaryFormulas = formulas_exist.build(
    Options(
        weight=6,
        required_files=(SUBMISSION_FILE,),
        sheet="Summary",
        entries=("B2", "D6"),
        range_matches_reference=False,
        hint=(
            "The calculated cells in the summary table should be produced with"
            " Excel formulas, not typed in by hand."
        ),
    )
)


test_03_TestSummaryChart = chart_metadata_match_reference.build(
    Options(
        weight=8,
        required_files=(SUBMISSION_FILE,),
        sheet="Summary",
        chart_ratio=0.9,
        chart_fields=("title", "x_axis_label", "y_axis_label"),
        chart_require_title=True,
        kwargs={"reference_file": REFERENCE_FILE},
        hint=(
            "Your chart must communicate the same story as the reference: use"
            " the correct chart type, include the required series, and label it"
            " clearly."
        ),
    )
)


# Optional stricter follow-up example:
# Uncomment this if the assignment requires the table to stay in the exact
# reference location and keep the same left-to-right column order.
#
# test_04_TestStrictLayout = data_table_match_reference.build(
#     Options(
#         weight=3,
#         required_files=(SUBMISSION_FILE,),
#         sheet="Summary",
#         entries=("A1", "D6"),
#         range_matches_reference=True,
#         strict_headers=True,
#         strict_column_order=True,
#         kwargs={"reference_file": REFERENCE_FILE},
#         hint="This assignment also grades the exact worksheet layout.",
#     )
# )


if __name__ == "__main__":
    with file_set_up(Options(required_files=(SUBMISSION_FILE,))):
        unittest.main()