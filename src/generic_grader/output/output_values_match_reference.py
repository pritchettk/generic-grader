"""Test all values in the output from a function."""

import unittest

from attrs import evolve

from parameterized import parameterized

from generic_grader.utils.decorators import merge_subtests, weighted
from generic_grader.utils.docs import get_wrapper, make_call_str, ordinalize, oxford_list
from generic_grader.utils.options import options_to_params
from generic_grader.utils.reference_test import reference_test
from generic_grader.utils.safe_equal import safe_assert_equal


def _line_numbers(options):
    """Return the output line numbers to validate."""
    return options.line_ns or (options.line_n,)


def _line_label(options):
    """Return a human-readable label for one or many output lines."""
    line_numbers = _line_numbers(options)
    if len(line_numbers) == 1:
        return f"output line {line_numbers[0]}"
    return f"output lines {oxford_list([str(n) for n in line_numbers])}"


def doc_func(func, num, param):
    """Return parameterized docstring when checking output values."""

    o = param.args[0]

    call_str = make_call_str(o.obj_name, o.args, o.kwargs)

    nth_value_string = f"{ordinalize(o.value_n)} value" if o.value_n else "values"
    line_label = _line_label(o)

    docstring = (
        f"Check that the {nth_value_string} on {line_label}"
        + f" from your `{o.obj_name}` function when called as `{call_str}`"
        + (o.entries and f" with entries={o.entries}" or "")
        + " match the reference values."
    )

    return docstring


def build(the_options):
    """Create a class for output value tests."""

    the_params = options_to_params(the_options)

    class TestOutputValuesMatchReference(unittest.TestCase):
        """A class for formatting tests."""

        wrapper = get_wrapper()

        @parameterized.expand(the_params, doc_func=doc_func)
        @merge_subtests()
        @weighted
        @reference_test
        def test_output_values_match_reference(self, options):
            """Compare values in the output to reference values."""

            o = options
            call_str = make_call_str(o.obj_name, o.args, o.kwargs)
            value_string = f"{ordinalize(o.value_n)} value" if o.value_n else "values"
            for line_n in _line_numbers(o):
                with self.subTest(line_n=line_n):
                    line_nth = ordinalize(line_n)
                    line_o = evolve(o, line_n=line_n)

                    # Set temporary line-specific options for per-line checks.
                    self.student_user.options = line_o
                    self.ref_user.options = line_o

                    # Get the actual and expected values.
                    actual = (
                        self.student_user.get_value()
                        if o.value_n
                        else self.student_user.get_values()
                    )
                    expected = (
                        self.ref_user.get_value() if o.value_n else self.ref_user.get_values()
                    )

                    message = (
                        "\n\nHint:\n"
                        + self.wrapper.fill(
                            "Your output values did not match the expected values."
                            + f"  Double check the {value_string} in the {line_nth} output line"
                            + f" of your `{o.obj_name}` function when called as `{call_str}`"
                            + (o.entries and f" with entries={o.entries}." or ".")
                            + (o.hint and f"  {o.hint}")
                        )
                        + f"{self.student_user.format_log()}"
                    )

                    safe_assert_equal(self, actual, expected, msg=message)

            # Restore original options after line-specific checks.
            self.student_user.options = o
            self.ref_user.options = o

            self.set_score(self, o.weight)  # Full credit

    return TestOutputValuesMatchReference
