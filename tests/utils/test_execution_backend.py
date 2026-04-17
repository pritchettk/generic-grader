from io import StringIO
from types import SimpleNamespace

import pytest

from generic_grader.utils.execution_backend import (
    MatlabObject,
    MatlabExecutionBackend,
    PythonExecutionBackend,
    detect_language,
    get_execution_backend,
    resolve_language,
)
from generic_grader.utils.options import Options


def test_get_execution_backend_python_default():
    backend = get_execution_backend(Options())
    assert isinstance(backend, PythonExecutionBackend)


def test_get_execution_backend_matlab():
    backend = get_execution_backend(Options(language="matlab"))
    assert isinstance(backend, MatlabExecutionBackend)


def test_auto_detect_python_from_sub_module_file(fix_syspath):
    fake_file = fix_syspath / "submission.py"
    fake_file.write_text("def main():\n    return 1")

    language = detect_language(Options(sub_module="submission"))
    assert language == "python"


def test_auto_detect_matlab_from_sub_module_file(fix_syspath):
    fake_file = fix_syspath / "submission.m"
    fake_file.write_text("function out = main()\nout = 1;\nend")

    language = detect_language(Options(sub_module="submission"))
    assert language == "matlab"


def test_resolve_language_prefers_explicit_override(fix_syspath):
    fake_file = fix_syspath / "submission.m"
    fake_file.write_text("function out = main()\nout = 1;\nend")

    language = resolve_language(Options(language="python", sub_module="submission"))
    assert language == "python"


def test_detect_language_ambiguous_source_files_raises(fix_syspath):
    py_file = fix_syspath / "submission.py"
    py_file.write_text("def main():\n    return 1")
    m_file = fix_syspath / "reference.m"
    m_file.write_text("function out = main()\nout = 1;\nend")

    with pytest.raises(ValueError) as exc_info:
        detect_language(Options(sub_module="submission", ref_module="reference"))

    assert "Ambiguous language detection" in str(exc_info.value)


def test_detect_language_from_required_files(fix_syspath):
    m_file = fix_syspath / "submission.m"
    m_file.write_text("function out = submission()\nout = 1;\nend")

    language = detect_language(Options(required_files=("submission.m",)))
    assert language == "matlab"


def test_python_backend_load_and_call(fix_syspath):
    fake_file = fix_syspath / "fake_module.py"
    fake_file.write_text("def fake_func(x, y=0):\n    return x + y")

    backend = PythonExecutionBackend()
    obj = backend.load_object("fake_module", "fake_func")
    result = backend.call_object(obj, Options(args=(2,), kwargs={"y": 3}))

    assert result == 5


def test_matlab_backend_load_object_resolves_module_file(fix_syspath):
    m_file = fix_syspath / "submission.m"
    m_file.write_text("function out = submission()\nout = 1;\nend")

    backend = MatlabExecutionBackend()
    obj = backend.load_object("submission", "main")
    assert isinstance(obj, MatlabObject)
    assert obj.function_name == "submission"
    assert obj.module_path.name == "submission.m"


def test_matlab_backend_load_object_prefers_obj_name_when_file_exists(fix_syspath):
    module_file = fix_syspath / "submission.m"
    module_file.write_text("function out = submission()\nout = 1;\nend")
    obj_file = fix_syspath / "main.m"
    obj_file.write_text("function out = main()\nout = 2;\nend")

    backend = MatlabExecutionBackend()
    obj = backend.load_object("submission", "main")
    assert obj.function_name == "main"


def test_matlab_backend_load_object_missing_module_raises():
    backend = MatlabExecutionBackend()
    with pytest.raises(ModuleNotFoundError):
        backend.load_object("missing_module", "main")


def test_matlab_backend_call_object_requires_matlab_object():
    backend = MatlabExecutionBackend()
    with pytest.raises(TypeError):
        backend.call_object("not-an-object", Options(language="matlab"))


def test_matlab_backend_call_object_rejects_entries(fix_syspath):
    m_file = fix_syspath / "submission.m"
    m_file.write_text("function out = submission()\nout = 1;\nend")
    backend = MatlabExecutionBackend()
    obj = backend.load_object("submission", "main")
    with pytest.raises(NotImplementedError):
        backend.call_object(obj, Options(language="matlab", entries=("x",)))


def test_matlab_backend_call_object_rejects_kwargs(fix_syspath):
    m_file = fix_syspath / "submission.m"
    m_file.write_text("function out = submission()\nout = 1;\nend")
    backend = MatlabExecutionBackend()
    obj = backend.load_object("submission", "main")
    with pytest.raises(NotImplementedError):
        backend.call_object(obj, Options(language="matlab", kwargs={"x": 1}))


class _FakeEngine:
    def __init__(self):
        self.calls = []

    def addpath(self, path, nargout=0):
        self.calls.append(("addpath", path, nargout))

    def rmpath(self, path, nargout=0):
        self.calls.append(("rmpath", path, nargout))

    def feval(self, func_name, *args, nargout=0, stdout=None, stderr=None):
        self.calls.append(("feval", func_name, args, nargout))
        if stdout is not None:
            stdout.write("MATLAB stdout\n")
        if stderr is not None:
            stderr.write("")
        if nargout == 0:
            return None
        return 42


def test_matlab_backend_call_object_uses_engine_and_writes_log(fix_syspath, monkeypatch):
    MatlabExecutionBackend._engine = None
    m_file = fix_syspath / "submission.m"
    m_file.write_text("function out = submission(x)\nout = x + 1;\nend")

    fake_engine = _FakeEngine()
    fake_module = SimpleNamespace(start_matlab=lambda *args: fake_engine)
    monkeypatch.setattr(
        "generic_grader.utils.execution_backend.importlib.import_module",
        lambda name: fake_module,
    )

    backend = MatlabExecutionBackend()
    obj = backend.load_object("submission", "submission")
    log = StringIO()
    result = backend.call_object(
        obj,
        Options(
            language="matlab",
            obj_name="submission",
            args=(5,),
            patches=[{"args": ["sys.stdout", log]}],
        ),
    )

    assert result == 42
    assert "MATLAB stdout" in log.getvalue()
    assert any(call[0] == "addpath" for call in fake_engine.calls)
    assert any(call[0] == "rmpath" for call in fake_engine.calls)


def test_matlab_backend_call_object_nargout_zero_returns_none(fix_syspath, monkeypatch):
    MatlabExecutionBackend._engine = None
    m_file = fix_syspath / "main.m"
    m_file.write_text("function main()\ndisp('ok');\nend")

    fake_engine = _FakeEngine()
    fake_module = SimpleNamespace(start_matlab=lambda *args: fake_engine)
    monkeypatch.setattr(
        "generic_grader.utils.execution_backend.importlib.import_module",
        lambda name: fake_module,
    )

    backend = MatlabExecutionBackend()
    obj = backend.load_object("main", "main")
    result = backend.call_object(obj, Options(language="matlab", obj_name="main"))
    assert result is None


def test_matlab_backend_missing_engine_raises_helpful_error(fix_syspath, monkeypatch):
    MatlabExecutionBackend._engine = None
    m_file = fix_syspath / "submission.m"
    m_file.write_text("function out = submission()\nout = 1;\nend")

    monkeypatch.setattr(
        "generic_grader.utils.execution_backend.importlib.import_module",
        lambda name: (_ for _ in ()).throw(ModuleNotFoundError("missing")),
    )

    backend = MatlabExecutionBackend()
    obj = backend.load_object("submission", "submission")
    with pytest.raises(ModuleNotFoundError) as exc_info:
        backend.call_object(obj, Options(language="matlab", obj_name="submission"))
    assert "MATLAB Engine for Python is not installed" in str(exc_info.value)
