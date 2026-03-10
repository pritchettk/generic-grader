"""Shared workbook helpers for excel checks."""

import glob
import posixpath
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from generic_grader.utils.options import Options

from openpyxl import load_workbook

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
}


def resolve_single_file(file_patterns: tuple[str, ...], label: str) -> str:
    """Resolve exactly one file from a tuple of file patterns."""

    if not file_patterns:
        raise ValueError(f"No {label} file pattern provided.")

    pattern = file_patterns[0]
    matches = glob.glob(pattern)

    if len(matches) == 0:
        raise FileNotFoundError(
            f'Could not find a {label} file matching pattern "{pattern}".'
        )

    if len(matches) > 1:
        raise ValueError(
            f'Found multiple {label} files matching pattern "{pattern}".'
        )

    return matches[0]


def resolve_sheet_and_range(options):
    """Read sheet and cell-range settings from Options."""

    if len(options.entries) != 2:
        raise ValueError(
            "Excel checks require `entries=(start_cell, end_cell)`,"
            " e.g. ('A1', 'C4')."
        )

    sheet = options.kwargs.get("sheet", options.sheet)
    start_cell, end_cell = options.entries
    return sheet, start_cell, end_cell


def load_sheet(path: str, sheet: str, data_only: bool):
    """Load a workbook and return the requested sheet."""

    workbook = load_workbook(filename=path, data_only=data_only)
    return workbook[sheet]


def _rels_path_for_source(source_path: str) -> str:
    source_dir = posixpath.dirname(source_path)
    source_file = posixpath.basename(source_path)
    return posixpath.join(source_dir, "_rels", f"{source_file}.rels")


def _resolve_target(source_path: str, target: str) -> str:
    if target.startswith("/"):
        return target.lstrip("/")
    source_dir = posixpath.dirname(source_path)
    return posixpath.normpath(posixpath.join(source_dir, target))


def _read_relationships(archive: zipfile.ZipFile, source_path: str) -> dict[str, str]:
    rels_path = _rels_path_for_source(source_path)
    if rels_path not in archive.namelist():
        return {}

    rels_xml = archive.read(rels_path)
    root = ET.fromstring(rels_xml)

    relationship_map = {}
    for relationship in root.findall("rel:Relationship", NS):
        rel_id = relationship.get("Id")
        target = relationship.get("Target")
        if rel_id and target:
            relationship_map[rel_id] = _resolve_target(source_path, target)

    return relationship_map


def _extract_title_text(parent_node):
    if parent_node is None:
        return None

    title_node = parent_node.find(".//c:title", NS)
    if title_node is None:
        return None

    text_nodes = title_node.findall(".//a:t", NS)
    text = "".join(node.text for node in text_nodes if node.text)
    return text or None


def _extract_chart_info(chart_xml: bytes, chart_file: str) -> dict:
    root = ET.fromstring(chart_xml)
    chart_info = {
        "chart_file": chart_file,
        "title": _extract_title_text(root),
        "x_axis_label": None,
        "y_axis_label": None,
        "types": [],
        "series": [],
    }

    cat_axis = root.find(".//c:catAx", NS)
    chart_info["x_axis_label"] = _extract_title_text(cat_axis)

    val_axis = root.find(".//c:valAx", NS)
    chart_info["y_axis_label"] = _extract_title_text(val_axis)

    plot_area = root.find(".//c:plotArea", NS)
    if plot_area is not None:
        for child in plot_area:
            tag_name = child.tag.split("}")[-1]
            if tag_name.endswith("Chart"):
                chart_info["types"].append(tag_name)

    for i, series in enumerate(root.findall(".//c:ser", NS), start=1):
        series_info = {"series_number": i, "x_range": None, "y_range": None}
        cat_formula = series.find(".//c:cat//c:f", NS)
        if cat_formula is not None:
            series_info["x_range"] = cat_formula.text

        val_formula = series.find(".//c:val//c:f", NS)
        if val_formula is not None:
            series_info["y_range"] = val_formula.text

        chart_info["series"].append(series_info)

    return chart_info


def extract_chart_info_from_workbook(xlsx_filepath: str, sheet: str | None = None) -> list[dict]:
    """Extract chart metadata from workbook XML for one sheet or all sheets."""

    workbook_chart_info = []
    with zipfile.ZipFile(xlsx_filepath, "r") as archive:
        workbook_path = "xl/workbook.xml"
        workbook_xml = archive.read(workbook_path)
        workbook_root = ET.fromstring(workbook_xml)
        workbook_relationships = _read_relationships(archive, workbook_path)

        for sheet_node in workbook_root.findall("s:sheets/s:sheet", NS):
            sheet_name = sheet_node.get("name")
            if sheet and sheet_name != sheet:
                continue

            rel_id = sheet_node.get(f"{{{NS['r']}}}id")
            if rel_id is None or rel_id not in workbook_relationships:
                continue

            sheet_path = workbook_relationships[rel_id]
            sheet_xml = archive.read(sheet_path)
            sheet_root = ET.fromstring(sheet_xml)
            sheet_relationships = _read_relationships(archive, sheet_path)

            drawing_rel_ids = [
                node.get(f"{{{NS['r']}}}id")
                for node in sheet_root.findall(".//s:drawing", NS)
                if node.get(f"{{{NS['r']}}}id")
            ]

            for drawing_rel_id in drawing_rel_ids:
                drawing_path = sheet_relationships.get(drawing_rel_id)
                if drawing_path is None:
                    continue

                drawing_xml = archive.read(drawing_path)
                drawing_root = ET.fromstring(drawing_xml)
                drawing_relationships = _read_relationships(archive, drawing_path)

                chart_rel_ids = [
                    node.get(f"{{{NS['r']}}}id")
                    for node in drawing_root.findall(".//c:chart", NS)
                    if node.get(f"{{{NS['r']}}}id")
                ]

                for chart_rel_id in chart_rel_ids:
                    chart_path = drawing_relationships.get(chart_rel_id)
                    if chart_path is None:
                        continue

                    chart_xml = archive.read(chart_path)
                    chart_info = _extract_chart_info(chart_xml, chart_path)
                    chart_info["sheet"] = sheet_name
                    workbook_chart_info.append(chart_info)

    return workbook_chart_info


def _resolve_from_patterns(patterns: tuple[str, ...], label: str) -> str:
    """Resolve exactly one file from multiple candidate patterns."""

    if not patterns:
        raise ValueError(f"No {label} file pattern provided.")

    matches = []
    for pattern in patterns:
        matches.extend(glob.glob(pattern))

    matches = list(dict.fromkeys(matches))

    if len(matches) == 0:
        pattern_str = '", "'.join(patterns)
        raise FileNotFoundError(
            f'Could not find a {label} file matching any pattern in ("{pattern_str}").'
        )

    if len(matches) > 1:
        pattern_str = '", "'.join(patterns)
        raise ValueError(
            f'Found multiple {label} files matching patterns in ("{pattern_str}").'
        )

    return matches[0]


def resolve_submission_file(options: Options) -> str:
    """Resolve submission workbook from sub_module or required_files."""

    if options.sub_module:
        return resolve_module_workbook(options.sub_module, "submission")

    if options.required_files:
        return resolve_single_file(options.required_files, "submission")

    raise ValueError("No submission file pattern provided.")


def resolve_reference_file(options: Options) -> str:
    """Resolve reference workbook from ref_module or kwargs['reference_file']."""

    default_ref_module = Options().ref_module
    if options.ref_module and options.ref_module != default_ref_module:
        return resolve_module_workbook(options.ref_module, "reference")

    explicit_reference = options.kwargs.get("reference_file")
    if explicit_reference:
        return resolve_single_file((explicit_reference,), "reference")

    raise ValueError(
        "No reference file provided. Set `ref_module`"
        " or `kwargs['reference_file']`.")


def resolve_module_workbook(module: str, label: str) -> str:
    """Resolve an exact workbook path from module-like syntax."""

    if not module:
        raise ValueError(f"No {label} module provided.")

    if any(char in module for char in "*?[]"):
        return _resolve_from_patterns((module,), label)

    candidate_paths = [
        module,
        f"{module}.xlsx",
        f"{module.replace('.', '/')}.xlsx",
        f"{module.replace('.', str(Path('/')))}.xlsx",
    ]

    existing_paths = {}
    for candidate in candidate_paths:
        candidate_path = Path(candidate)
        if candidate_path.is_file():
            normalized = str(candidate_path.resolve())
            existing_paths[normalized] = str(candidate_path)

    existing_paths = list(existing_paths.values())

    if len(existing_paths) == 0:
        candidate_str = '", "'.join(candidate_paths)
        raise FileNotFoundError(
            f'Could not find a {label} file from module "{module}".'
            f' Tried ("{candidate_str}").'
        )

    if len(existing_paths) > 1:
        candidate_str = '", "'.join(existing_paths)
        raise ValueError(
            f'Found multiple {label} files for module "{module}"'
            f' in ("{candidate_str}").'
        )

    return existing_paths[0]
