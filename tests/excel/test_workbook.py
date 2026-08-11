"""Unit tests for the shared excel/_workbook.py helpers."""

from openpyxl.worksheet.formula import ArrayFormula

from generic_grader.excel._workbook import get_formula_text, is_formula_value


def test_ordinary_string_formula_is_a_formula():
    assert is_formula_value("=A1+B1") is True
    assert get_formula_text("=A1+B1") == "=A1+B1"


def test_array_formula_with_text_is_a_formula():
    value = ArrayFormula("A1", "=MODE.MULT(B1:B10)")
    assert is_formula_value(value) is True
    assert get_formula_text(value) == "=MODE.MULT(B1:B10)"


def test_array_formula_with_no_text_is_still_a_formula():
    """openpyxl's ArrayFormula.__init__ defaults text=None (e.g. for
    non-anchor cells of a multi-cell array range). is_formula_value must
    still report True -- an array formula with no text of its own is not
    the same thing as "not a formula", and misreading it that way is the
    exact bug class this module fixes."""
    value = ArrayFormula("A1")
    assert value.text is None
    assert is_formula_value(value) is True
    assert get_formula_text(value) is None


def test_plain_value_is_not_a_formula():
    assert is_formula_value(42) is False
    assert get_formula_text(42) is None


def test_none_is_not_a_formula():
    assert is_formula_value(None) is False
    assert get_formula_text(None) is None


def test_plain_string_starting_with_something_else_is_not_a_formula():
    assert is_formula_value("hello") is False
    assert get_formula_text("hello") is None
