import unittest

import pytest
from openpyxl import Workbook

from generic_grader.excel.data_series_exists import build
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
    assert built_class.__name__ == "TestDataSeriesExists"


def test_instance_has_test_method(built_instance):
    assert hasattr(built_instance, "test_data_series_exists_0")


def test_doc_func(built_instance):
    assert (
        built_instance.test_data_series_exists_0.__doc__
        == "Check that the data series in range A2:A5 on sheet `Sheet1` exists somewhere in the submission workbook."
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
    built_instance = built_class(methodName="test_data_series_exists_0")
    test_method = built_instance.test_data_series_exists_0
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
    built_instance = built_class(methodName="test_data_series_exists_0")
    test_method = built_instance.test_data_series_exists_0
    test_method()

    assert test_method.__score__ == test_method.__weight__


def test_passing_ratio_threshold_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": 1, "A3": 2, "A4": 3, "A5": 4},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"B2": 1, "B3": 2, "B4": 99, "B5": 4},
    )

    built_class = build(
        Options(
            weight=1,
            ratio=0.75,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            sheet="Sheet1",
            kwargs={"reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_series_exists_0")
    test_method = built_instance.test_data_series_exists_0
    test_method()

    assert test_method.__score__ == test_method.__weight__


def test_failing_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": 10, "A3": 20, "A4": 30, "A5": 40},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"D2": 1, "D3": 2, "D4": 3, "D5": 4},
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
    built_instance = built_class(methodName="test_data_series_exists_0")
    test_method = built_instance.test_data_series_exists_0

    with pytest.raises(AssertionError) as exc_info:
        test_method()

    assert "Could not find data series" in str(exc_info.value)
    assert test_method.__score__ == 0


def test_passing_formula_required_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": "=1+9", "A3": "=10+10", "A4": "=10+20", "A5": "=20+20"},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"D2": "=1+9", "D3": "=10+10", "D4": "=10+20", "D5": "=20+20"},
    )

    built_class = build(
        Options(
            weight=1,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            sheet="Sheet1",
            kwargs={
                "reference_file": "reference.xlsx",
                "series_require_formulas": True,
                "search_orientation": "column",
            },
        )
    )
    built_instance = built_class(methodName="test_data_series_exists_0")
    test_method = built_instance.test_data_series_exists_0
    test_method()

    assert test_method.__score__ == test_method.__weight__


def test_failing_formula_required_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A2": "=1+9", "A3": "=10+10", "A4": "=10+20", "A5": "=20+20"},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"D2": "=1+9", "D3": "=10+10", "D4": 30, "D5": "=20+20"},
    )

    built_class = build(
        Options(
            weight=1,
            ratio=0.75,
            required_files=("submission.xlsx",),
            entries=("A2", "A5"),
            sheet="Sheet1",
            kwargs={
                "reference_file": "reference.xlsx",
                "series_require_formulas": True,
                "search_orientation": "column",
            },
        )
    )
    built_instance = built_class(methodName="test_data_series_exists_0")
    test_method = built_instance.test_data_series_exists_0

    with pytest.raises(AssertionError) as exc_info:
        test_method()

    assert "not a formula cell" in str(exc_info.value)
    assert test_method.__score__ == 0
