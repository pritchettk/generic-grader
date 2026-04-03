"""Compatibility wrapper for the consolidated data series check."""

from attrs import evolve

from generic_grader.excel.data_series_match_reference import build as build_data_series
from generic_grader.utils.options import options_to_params


def build(the_options):
    """Build a same-range data-series check via data_series_match_reference."""

    params = options_to_params(the_options)
    evolved = [
        evolve(option.args[0], range_matches_reference=True)
        for option in params
    ]

    return build_data_series([option for option in evolved])
