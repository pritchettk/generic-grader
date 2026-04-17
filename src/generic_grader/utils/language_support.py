"""Helpers for language-aware feature gating in checks."""

import unittest

from generic_grader.utils.execution_backend import resolve_language
from generic_grader.utils.options import Options


def require_language_support(
    test: unittest.TestCase,
    options: Options,
    supported_languages: tuple[str, ...],
    feature_name: str,
):
    """Skip a test when the selected language is unsupported."""

    language = resolve_language(options)
    if language in supported_languages:
        return

    supported = ", ".join(supported_languages)
    raise unittest.SkipTest(
        f"{feature_name} is only supported for language(s): {supported}. "
        f"Current language is '{language}'."
    )
