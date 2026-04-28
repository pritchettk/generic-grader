"""Test that chart metadata in a workbook matches a reference workbook."""

import unittest

from parameterized import parameterized
from rapidfuzz.distance.Levenshtein import normalized_similarity

from generic_grader.excel._workbook import (
    extract_chart_info_from_workbook,
    resolve_reference_file,
    resolve_submission_file,
)
from generic_grader.utils.decorators import merge_subtests, weighted
from generic_grader.utils.docs import get_wrapper
from generic_grader.utils.options import options_to_params


def _normalize_text(text: str | None) -> str:
    if text is None:
        return ""
    lowered = text.lower()
    filtered = "".join(ch if ch.isalnum() else " " for ch in lowered)
    return " ".join(filtered.split())


def _is_meaningful(text: str | None) -> bool:
    normalized = _normalize_text(text)
    return bool(normalized)


def _similarity(actual: str | None, expected: str | None) -> float:
    actual_normalized = _normalize_text(actual)
    expected_normalized = _normalize_text(expected)
    if not actual_normalized and not expected_normalized:
        return 1.0
    return normalized_similarity(actual_normalized, expected_normalized)


def _match_reference_to_submission(ref_charts: list[dict], sub_charts: list[dict], ratio: float):
    available = sub_charts.copy()
    pairs = []

    for ref_chart in ref_charts:
        ref_title = ref_chart.get("title")
        if not _is_meaningful(ref_title):
            raise AssertionError(
                "Reference chart is missing a meaningful title on the selected sheet."
            )

        best_match = None
        best_ratio = -1.0
        for sub_chart in available:
            score = _similarity(sub_chart.get("title"), ref_title)
            if score > best_ratio:
                best_ratio = score
                best_match = sub_chart

        if best_match is None or best_ratio < ratio:
            raise AssertionError(
                f"Could not find a submission chart title similar to '{ref_title}'."
            )

        available.remove(best_match)
        pairs.append((ref_chart, best_match))

    return pairs


def doc_func(func, num, param):
    """Return parameterized docstring for chart metadata checks."""

    o = param.args[0]
    return (
        f"Check that chart title and axis labels on sheet `{o.sheet}` are"
        " meaningfully similar to the reference workbook."
    )


def build(the_options):
    """Create a class for chart metadata-to-reference checks."""

    the_params = options_to_params(the_options)

    class TestChartMetadataMatchReference(unittest.TestCase):
        """A class for chart metadata matching tests."""

        wrapper = get_wrapper()

        @parameterized.expand(the_params, doc_func=doc_func)
        @merge_subtests()
        @weighted
        def test_chart_metadata_match_reference(self, options):
            """Check chart title and axis labels against reference workbook."""

            o = options
            sub_file = resolve_submission_file(o)
            reference_file = resolve_reference_file(o)

            ref_charts = extract_chart_info_from_workbook(reference_file, sheet=o.sheet)
            sub_charts = extract_chart_info_from_workbook(sub_file, sheet=o.sheet)

            self.assertTrue(
                ref_charts,
                msg=(
                    "\n\nHint:\n"
                    + self.wrapper.fill(
                        f"No charts were found in the reference workbook on sheet `{o.sheet}`."
                    )
                ),
            )

            self.assertTrue(
                sub_charts,
                msg=(
                    "\n\nHint:\n"
                    + self.wrapper.fill(
                        f"No charts were found in your workbook on sheet `{o.sheet}`."
                        + (o.hint and f"  {o.hint}" or "")
                    )
                ),
            )

            if o.chart_require_title:
                for chart in sub_charts:
                    with self.subTest(chart=chart.get("chart_file")):
                        self.assertTrue(
                            _is_meaningful(chart.get("title")),
                            msg=(
                                "\n\nHint:\n"
                                + self.wrapper.fill(
                                    f"Chart `{chart.get('chart_file')}` on sheet `{o.sheet}`"
                                    " is missing a meaningful title."
                                    + (o.hint and f"  {o.hint}" or "")
                                )
                            ),
                        )

            matched_charts = _match_reference_to_submission(
                ref_charts,
                sub_charts,
                o.chart_ratio,
            )

            for ref_chart, sub_chart in matched_charts:
                for field in o.chart_fields:
                    with self.subTest(chart=sub_chart.get("chart_file"), field=field):
                        expected = ref_chart.get(field)
                        actual = sub_chart.get(field)
                        if expected is None:
                            continue

                        self.assertTrue(
                            _is_meaningful(actual),
                            msg=(
                                "\n\nHint:\n"
                                + self.wrapper.fill(
                                    f"The `{field}` for chart `{sub_chart.get('chart_file')}`"
                                    f" on sheet `{o.sheet}` is missing or not meaningful."
                                    + (o.hint and f"  {o.hint}" or "")
                                )
                            ),
                        )

                        ratio = _similarity(actual, expected)
                        self.assertGreaterEqual(
                            ratio,
                            o.chart_ratio,
                            msg=(
                                "\n\nHint:\n"
                                + self.wrapper.fill(
                                    f"The `{field}` for chart `{sub_chart.get('chart_file')}`"
                                    " is not sufficiently similar to the reference chart."
                                    f" Required similarity: {o.chart_ratio:.2f}."
                                    + (o.hint and f"  {o.hint}" or "")
                                )
                            ),
                        )

            self.set_score(self, o.weight)

    return TestChartMetadataMatchReference
