import unittest

import pytest
from openpyxl import Workbook

from generic_grader.excel.data_match_reference import build
from generic_grader.utils.options import Options


def write_workbook(path, sheet_name="Sheet", cells=None):
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
            entries=("A1", "B1"),
            kwargs={"sheet": "Sheet", "reference_file": "reference.xlsx"},
        )
    )


@pytest.fixture()
def built_instance(built_class):
    return built_class()


def test_build_class(built_class):
    assert issubclass(built_class, unittest.TestCase)


def test_build_class_name(built_class):
    assert built_class.__name__ == "TestDataMatchReference"


def test_instance_has_test_method(built_instance):
    assert hasattr(built_instance, "test_data_match_reference_0")


def test_doc_func(built_instance):
    assert (
        built_instance.test_data_match_reference_0.__doc__
        == "Check that cells in range A1:B1 on sheet `Sheet` match the reference values."
    )


def test_passing_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A1": 10, "B1": 20},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"A1": 10, "B1": 20},
    )

    built_class = build(
        Options(
            weight=1,
            required_files=("submission.xlsx",),
            entries=("A1", "B1"),
            kwargs={"sheet": "Sheet", "reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_match_reference_0")
    test_method = built_instance.test_data_match_reference_0
    test_method()

    assert test_method.__score__ == test_method.__weight__


def test_failing_case(fix_syspath):
    write_workbook(
        fix_syspath / "reference.xlsx",
        cells={"A1": 10, "B1": 20},
    )
    write_workbook(
        fix_syspath / "submission.xlsx",
        cells={"A1": 10, "B1": 99},
    )

    built_class = build(
        Options(
            weight=1,
            required_files=("submission.xlsx",),
            entries=("A1", "B1"),
            kwargs={"sheet": "Sheet", "reference_file": "reference.xlsx"},
        )
    )
    built_instance = built_class(methodName="test_data_match_reference_0")
    test_method = built_instance.test_data_match_reference_0

    with pytest.raises(AssertionError) as exc_info:
        test_method()

    assert "Cell B1" in str(exc_info.value)
    assert test_method.__score__ == 0
