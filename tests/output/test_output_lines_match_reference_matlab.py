from types import SimpleNamespace

from generic_grader.output.output_lines_match_reference import build
from generic_grader.utils.execution_backend import MatlabExecutionBackend
from generic_grader.utils.options import Options


class _FakeEngine:
    def addpath(self, path, nargout=0):
        return None

    def rmpath(self, path, nargout=0):
        return None

    def feval(self, func_name, *args, nargout=0, stdout=None, stderr=None):
        if stdout is not None:
            stdout.write("value: 42\n")
        return None if nargout == 0 else 42


def test_output_lines_match_reference_matlab(fix_syspath, monkeypatch):
    MatlabExecutionBackend._engine = None

    ref_file = fix_syspath / "reference.m"
    ref_file.write_text("function reference()\ndisp('value: 42');\nend")

    sub_file = fix_syspath / "submission.m"
    sub_file.write_text("function submission()\ndisp('value: 42');\nend")

    fake_module = SimpleNamespace(start_matlab=lambda *args: _FakeEngine())
    monkeypatch.setattr(
        "generic_grader.utils.execution_backend.importlib.import_module",
        lambda name: fake_module,
    )

    built_class = build(
        Options(
            language="matlab",
            ref_module="reference",
            sub_module="submission",
            obj_name="main",
            weight=1,
        )
    )
    built_instance = built_class(methodName="test_output_lines_match_reference_0")
    test_method = built_instance.test_output_lines_match_reference_0

    test_method()
    assert test_method.__score__ == 1
