"""Example grader config for MATLAB submissions."""

from generic_grader.function import function_return_values_match_reference
from generic_grader.output import output_lines_match_reference
from generic_grader.utils.options import Options


test_01_output_lines = output_lines_match_reference.build(
    Options(
        language="matlab",
        sub_module="submission",
        ref_module="reference",
        obj_name="main",
        weight=1,
    )
)


test_02_return_value = function_return_values_match_reference.build(
    Options(
        language="matlab",
        sub_module="submission",
        ref_module="reference",
        obj_name="main",
        execution_config={"nargout": 1},
        weight=1,
    )
)
