"""Language-aware execution backends for grader runtime integration."""

import importlib
import io
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

from generic_grader.utils.options import Options
from generic_grader.utils.patches import custom_stack


class ExecutionBackend(ABC):
    """Backend interface for loading and invoking graded callables."""

    language: str

    @abstractmethod
    def load_object(self, module: str, obj_name: str):
        """Load and return the callable/object requested by module and name."""

    @abstractmethod
    def call_object(self, obj, options: Options):
        """Invoke the loaded object using the provided options."""


@dataclass(frozen=True)
class MatlabObject:
    """A callable reference for MATLAB execution."""

    function_name: str
    module_path: Path


class PythonExecutionBackend(ExecutionBackend):
    """Python runtime backend using in-process import and patching."""

    language = "python"

    def load_object(self, module: str, obj_name: str):
        return getattr(__import__(module, fromlist=[obj_name]), obj_name)

    def call_object(self, obj, options: Options):
        with custom_stack(options):
            return obj(*deepcopy(options.args), **deepcopy(options.kwargs))


class MatlabExecutionBackend(ExecutionBackend):
    """Placeholder backend for MATLAB engine integration."""

    language = "matlab"

    _engine = None

    def load_object(self, module: str, obj_name: str):
        matlab_module_path = self._resolve_module_path(module, obj_name)

        function_name = matlab_module_path.stem
        if obj_name:
            obj_candidate = Path(obj_name)
            obj_candidate_file = (
                obj_candidate
                if obj_candidate.suffix.lower() == ".m"
                else obj_candidate.with_suffix(".m")
            )
            if obj_candidate_file.is_file():
                function_name = obj_candidate_file.stem

        return MatlabObject(function_name=function_name, module_path=matlab_module_path)

    def call_object(self, obj, options: Options):
        if options.entries:
            raise NotImplementedError(
                "MATLAB backend does not currently support interactive input entries. "
                "Use function arguments/kwargs instead."
            )
        if options.kwargs:
            raise NotImplementedError(
                "MATLAB backend does not currently support keyword arguments. "
                "Pass values through positional args instead."
            )

        if not isinstance(obj, MatlabObject):
            raise TypeError("MATLAB backend expected a MatlabObject.")

        engine = self._get_engine(options)
        module_dir = str(obj.module_path.parent.resolve())
        stdout = io.StringIO()
        stderr = io.StringIO()

        arg_values = [self._to_matlab_value(v) for v in options.args]
        nargout = self._resolve_nargout(options)

        added_path = False
        try:
            if module_dir:
                engine.addpath(module_dir, nargout=0)
                added_path = True

            if nargout == 0:
                engine.feval(
                    obj.function_name,
                    *arg_values,
                    nargout=0,
                    stdout=stdout,
                    stderr=stderr,
                )
                result = None
            else:
                result = engine.feval(
                    obj.function_name,
                    *arg_values,
                    nargout=nargout,
                    stdout=stdout,
                    stderr=stderr,
                )
        finally:
            if added_path:
                engine.rmpath(module_dir, nargout=0)

        self._write_backend_log(options, stdout.getvalue() + stderr.getvalue())
        return result

    @classmethod
    def _get_engine(cls, options: Options):
        configured_engine = options.execution_config.get("engine_instance")
        if configured_engine is not None:
            return configured_engine

        if cls._engine is not None:
            return cls._engine

        try:
            matlab_engine = importlib.import_module("matlab.engine")
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                "MATLAB Engine for Python is not installed. "
                "Install it from your MATLAB distribution and retry."
            ) from e

        start_args = options.execution_config.get("start_args")
        if start_args:
            cls._engine = matlab_engine.start_matlab(start_args)
        else:
            cls._engine = matlab_engine.start_matlab()

        return cls._engine

    @staticmethod
    def _resolve_module_path(module: str, obj_name: str) -> Path:
        direct_candidates = _collect_module_file_candidates(module)
        for candidate in direct_candidates:
            if candidate.suffix.lower() == ".m" and candidate.is_file():
                return candidate
            m_file = candidate.with_suffix(".m")
            if m_file.is_file():
                return m_file

        if obj_name:
            obj_candidate = Path(obj_name)
            if obj_candidate.suffix.lower() == ".m" and obj_candidate.is_file():
                return obj_candidate
            obj_m_file = obj_candidate.with_suffix(".m")
            if obj_m_file.is_file():
                return obj_m_file

        raise ModuleNotFoundError(module)

    @staticmethod
    def _to_matlab_value(value):
        # Most scalar types map directly through MATLAB Engine.
        if isinstance(value, (bool, int, float, str)) or value is None:
            return value

        # Preserve tuples/lists as plain Python collections when possible.
        if isinstance(value, tuple):
            return [MatlabExecutionBackend._to_matlab_value(v) for v in value]
        if isinstance(value, list):
            return [MatlabExecutionBackend._to_matlab_value(v) for v in value]

        return value

    @staticmethod
    def _resolve_nargout(options: Options) -> int:
        configured = options.execution_config.get("nargout")
        if configured is not None:
            return int(configured)
        return 0 if options.obj_name == "main" else 1

    @staticmethod
    def _write_backend_log(options: Options, text: str):
        if not text:
            return

        for patch in options.patches or []:
            args = patch.get("args", [])
            if len(args) == 2 and args[0] == "sys.stdout" and hasattr(args[1], "write"):
                args[1].write(text)
                break


def _collect_module_file_candidates(module_name: str) -> list[Path]:
    """Return possible filesystem paths for a dotted module/path name."""

    if not module_name:
        return []

    raw_path = Path(module_name)
    dotted_path = Path(module_name.replace(".", "/"))
    return [raw_path, dotted_path]


def detect_language(options: Options) -> str:
    """Detect runtime language from available source files.

    Detection rules:
    - explicit extension in module name: .py -> python, .m -> matlab
    - existing module paths with .py/.m suffixes
    - .py/.m files in required_files (if provided)
    - fallback to python when no language evidence is available
    """

    found_languages: set[str] = set()

    module_names = [options.sub_module, options.ref_module]
    for module_name in module_names:
        if not module_name:
            continue

        if module_name.endswith(".py"):
            found_languages.add("python")
            continue
        if module_name.endswith(".m"):
            found_languages.add("matlab")
            continue

        for candidate in _collect_module_file_candidates(module_name):
            py_file = candidate.with_suffix(".py")
            m_file = candidate.with_suffix(".m")
            if py_file.is_file():
                found_languages.add("python")
            if m_file.is_file():
                found_languages.add("matlab")

    for required_file in options.required_files:
        required_path = Path(required_file)
        suffix = required_path.suffix.lower()
        if suffix == ".py" and required_path.is_file():
            found_languages.add("python")
        if suffix == ".m" and required_path.is_file():
            found_languages.add("matlab")

    if len(found_languages) > 1:
        raise ValueError(
            "Ambiguous language detection: found both Python and MATLAB source files. "
            "Set `language` explicitly in Options."
        )

    if found_languages:
        return next(iter(found_languages))

    return "python"


def resolve_language(options: Options) -> str:
    """Resolve runtime language from explicit option or auto-detection."""

    configured = options.language.lower()
    if configured == "auto":
        return detect_language(options)

    return configured


def get_execution_backend(options: Options) -> ExecutionBackend:
    """Return the runtime backend selected by resolved language."""

    language = resolve_language(options)
    if language == "python":
        return PythonExecutionBackend()
    if language == "matlab":
        return MatlabExecutionBackend()

    raise ValueError(f"Unsupported language: {options.language}")
