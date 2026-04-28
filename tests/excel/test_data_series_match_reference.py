import unittest

import pytest
from openpyxl import Workbook

from generic_grader.excel.data_series_match_reference import build
from generic_grader.utils.options import Options


def write_workbook(path, sheet_name="Sheet1", cells=None):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet_name
    for cell, value in (cells or {}).items():
        worksheet[cell] = value
    workbook.save(path)


@pytest.fixture()
def built_class():
    return build(
        Options(
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            kwargs={"reference_file": "reference.xlsx"},
        )
    )


@pytest.fixture()
def built_instance(built_class):
    return built_class()


def test_build_class(built_class):
    assert issubclass(built_class, unittest.TestCase)


def test_build_class_name(built_class):
    assert built_class.__name__ == "TestDataSeriesMatchReference"


def test_instance_has_test_method(built_instance):
    assert hasattr(built_instance, "test_data_series_match_reference_0")


def test_doc_func_same_range_default(built_instance):
    assert (
        built_instance.test_data_series_match_reference_0.__doc__
        == "Check that the data series in range A2:A5 on sheet `<first worksheet>` exactly matches the reference values at the same cell locations."
    )


def test_doc_func_search_mode():
    built_class = build(
        Options(
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            range_matches_reference=False,
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class()

    assert (
        built_instance.test_data_series_match_reference_0.__doc__
        == "Check that the data series in range A2:A5 on sheet `<first worksheet>` exactly matches somewhere in the submission workbook."
    )


def test_passing_same_range_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": 10, "A3": 20, "A4": 30, "A5": 40},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"A2": 10, "A3": 20, "A4": 30, "A5": 40},
    )

    built_class = build(
        Options(
            weight=1,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_match_reference_0")
    test_method = built_instance.test_data_series_match_reference_0
    test_method()

    assert test_method.__score__ == test_method.__weight__


def test_failing_same_range_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": 10, "A3": 20, "A4": 30, "A5": 40},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"A2": 10, "A3": 20, "A4": 999, "A5": 40},
    )

    built_class = build(
        Options(
            weight=1,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_match_reference_0")
    test_method = built_instance.test_data_series_match_reference_0

    with pytest.raises(AssertionError) as exc_info:
        test_method()

    assert "did not meet the expected" in str(exc_info.value)
    assert test_method.__score__ == 0


def test_passing_search_mode_relocated_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": 10, "A3": 20, "A4": 30, "A5": 40},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"D2": 10, "D3": 20, "D4": 30, "D5": 40},
    )

    built_class = build(
        Options(
            weight=1,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            range_matches_reference=False,
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_match_reference_0")
    test_method = built_instance.test_data_series_match_reference_0
    test_method()

    assert test_method.__score__ == test_method.__weight__


def test_passing_search_mode_ratio_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": 10, "A3": 20, "A4": 30, "A5": 40},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"D2": 10, "D3": 20, "D4": 999, "D5": 40},
    )

    built_class = build(
        Options(
            weight=1,
            ratio=0.75,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            range_matches_reference=False,
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_match_reference_0")
    test_method = built_instance.test_data_series_match_reference_0
    test_method()

    assert test_method.__score__ == test_method.__weight__


def test_failing_search_mode_exact_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": 10, "A3": 20, "A4": 30, "A5": 40},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"D2": 10, "D3": 20, "D4": 999, "D5": 40},
    )

    built_class = build(
        Options(
            weight=1,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            range_matches_reference=False,
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_match_reference_0")
    test_method = built_instance.test_data_series_match_reference_0

    with pytest.raises(AssertionError) as exc_info:
        test_method()

    assert "No exact data series match" in str(exc_info.value)
    assert test_method.__score__ == 0


def test_first_worksheet_default_sheet_fallback(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        sheet_name="Grades",
        cells={"A2": 10, "A3": 20, "A4": 30, "A5": 40},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        sheet_name="Grades",
        cells={"A2": 10, "A3": 20, "A4": 30, "A5": 40},
    )

    built_class = build(
        Options(
            weight=1,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_match_reference_0")
    test_method = built_instance.test_data_series_match_reference_0
    test_method()

    assert test_method.__score__ == test_method.__weight__
