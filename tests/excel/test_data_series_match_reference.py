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
            sheet="Sheet1",
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


def test_doc_func(built_instance):
    assert (
        built_instance.test_data_series_match_reference_0.__doc__
        == "Check that the data series in range A2:A5 on sheet `Sheet1` exactly matches somewhere in the submission workbook."
    )


def test_passing_relocated_column_case(fix_syspath):
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
            sheet="Sheet1",
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_match_reference_0")
    test_method = built_instance.test_data_series_match_reference_0
    test_method()

    assert test_method.__score__ == test_method.__weight__


def test_passing_transposed_orientation_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": 1, "A3": 2, "A4": 3, "A5": 4},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"B6": 1, "C6": 2, "D6": 3, "E6": 4},
    )

    built_class = build(
        Options(
            weight=1,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            sheet="Sheet1",
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_match_reference_0")
    test_method = built_instance.test_data_series_match_reference_0
    test_method()

    assert test_method.__score__ == test_method.__weight__


def test_passing_numeric_tolerance_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": 1.0, "A3": 2.0, "A4": 3.0, "A5": 4.0},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"C2": 1.0, "C3": 2.0, "C4": 3.0000001, "C5": 4.0},
    )

    built_class = build(
        Options(
            weight=1,
            relative_tolerance=1e-6,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            sheet="Sheet1",
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_match_reference_0")
    test_method = built_instance.test_data_series_match_reference_0
    test_method()

    assert test_method.__score__ == test_method.__weight__


def test_failing_case(fix_syspath):
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
            sheet="Sheet1",
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_match_reference_0")
    test_method = built_instance.test_data_series_match_reference_0

    with pytest.raises(AssertionError) as exc_info:
        test_method()

    assert "No exact data series match" in str(exc_info.value)
    assert test_method.__score__ == 0
