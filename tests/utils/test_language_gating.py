import unittest

import pytest

from generic_grader.class_.class_is_defined import build as class_is_defined_build
from generic_grader.function.static_loop_depth import build as static_loop_depth_build
from generic_grader.style.comments import build as comments_build
from generic_grader.utils.options import Options


def test_comments_check_skips_for_matlab(fix_syspath):
    ref_file = fix_syspath / "reference.m"
    ref_file.write_text("function y = reference()\ny = 1;\nend")
    sub_file = fix_syspath / "submission.m"
    sub_file.write_text("function y = submission()\ny = 1;\nend")

    built_class = comments_build(
        Options(language="matlab", ref_module="reference", sub_module="submission")
    )
    built_instance = built_class(methodName="test_comment_length_0")

    with pytest.raises(unittest.SkipTest):
        built_instance.test_comment_length_0()


def test_static_loop_depth_skips_for_matlab(fix_syspath):
    ref_file = fix_syspath / "reference.m"
    ref_file.write_text("function y = reference()\ny = 1;\nend")
    sub_file = fix_syspath / "submission.m"
    sub_file.write_text("function y = submission()\ny = 1;\nend")

    built_class = static_loop_depth_build(
        Options(language="matlab", ref_module="reference", sub_module="submission")
    )
    built_instance = built_class(methodName="test_static_loop_depth_0")

    with pytest.raises(unittest.SkipTest):
        built_instance.test_static_loop_depth_0()


def test_class_is_defined_skips_for_matlab(fix_syspath):
    sub_file = fix_syspath / "submission.m"
    sub_file.write_text("function y = submission()\ny = 1;\nend")

    built_class = class_is_defined_build(
        Options(language="matlab", sub_module="submission", obj_name="MyClass")
    )
    built_instance = built_class(methodName="test_class_is_defined_0")

    with pytest.raises(unittest.SkipTest):
        built_instance.test_class_is_defined_0()
