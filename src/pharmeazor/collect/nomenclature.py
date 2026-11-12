"""Reading the official nomenclature workbooks.

The ministry publishes the registry as Excel, and the layout fights you:

* the sheet opens with a letterhead block, so the column titles sit on row 14
  in the version workbooks and row 11 in the per-year ones — the header is
  therefore **found**, never hardcoded;
* each workbook holds three sheets (``Nomenclature``, ``Non Renouvelés``,
  ``Retraits``) and the last one has different columns, so every cell is read
  **by title**, never by position. Reading ``Retraits`` positionally puts dates
  into the laboratory field and reports nothing;
* the source contains genuine typos (``SUSPENSSION``) and footnote markers
  (``875MG*``), which are preserved rather than silently corrected.
"""

from __future__ import annotations

import datetime as _dt
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "CANONICAL_COLUMNS",
    "NomenclatureRow",
    "find_header_row",
    "read_sheet",
    "read_workbook",
    "sheet_kind",
]

# Column title in the file -> field name we use everywhere else. Titles are
# matched loosely (accents, case and spacing are flattened first).
CANONICAL_COLUMNS: dict[str, str] = {
    "N": "row_no",
    "NENREGISTREMENT": "registration_no",
    "CODE": "code",
    "DENOMINATION COMMUNE INTERNATIONALE": "inn",
    "NOM DE MARQUE": "brand_name",
    "FORME": "form",
    "DOSAGE": "strength_raw",
    "CONDITIONNEMENT": "packaging_raw",
    "LISTE": "list_class",
    "P1": "p1",
    "P2": "p2",
    "OBS": "obs",
    "LABORATOIRES DETENTEUR DE LA DECISION DENREGISTREMENT": "lab_name",
    "PAYS DU LABORATOIRE DETENTEUR DE LA DECISION DENREGISTREMENT": "lab_country",
    "DATE DENREGISTREMENT INITIAL": "date_initial",
    "DATE DENREGISTREMENT FINAL": "date_final",
    "TYPE": "type_code",
    "STATUT": "status",
    "DUREE DE STABILITE": "stability",
    "DATE DE RETRAIT": "withdrawal_date",
    "MOTIF DE RETRAIT": "withdrawal_reason",
}

_MIN_HEADER_CELLS = 15


def _flatten(text: object) -> str:
    """Upper-case, strip accents and punctuation, collapse spaces."""
    import unicodedata

    raw = unicodedata.normalize("NFKD", str(text or ""))
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", raw.upper())).strip()


def sheet_kind(title: str) -> str:
    """Classify a sheet by its name: nomenclature, non_renouveles or retraits."""
    flat = _flatten(title)
    if "RETRAIT" in flat:
        return "retraits"
    if "RENOUVEL" in flat:
        return "non_renouveles"
    return "nomenclature"


def find_header_row(worksheet, max_scan: int = 30) -> int:
    """Return the 1-based row number holding the column titles.

    The first row carrying at least :data:`_MIN_HEADER_CELLS` non-empty cells is
    the header: the letterhead lines above it hold one cell each.

    Raises:
        ValueError: when no such row exists in the first ``max_scan`` rows.
    """
    for index, row in enumerate(
        worksheet.iter_rows(min_row=1, max_row=max_scan, values_only=True), start=1
    ):
        filled = [c for c in row if c not in (None, "")]
        if len(filled) >= _MIN_HEADER_CELLS:
            return index
    raise ValueError(
        f"En-tête introuvable dans les {max_scan} premières lignes de "
        f"« {worksheet.title} »."
    )


def _column_map(header: tuple) -> dict[str, int]:
    """Map our field names to column positions, using the titles found."""
    mapping: dict[str, int] = {}
    for position, title in enumerate(header):
        flat = _flatten(title)
        if not flat:
            continue
        field = CANONICAL_COLUMNS.get(flat)
        if field is None:
            # Tolerate small wording drifts between versions.
            for known, candidate in CANONICAL_COLUMNS.items():
                if flat.startswith(known[:18]) and len(known) > 6:
                    field = candidate
                    break
        if field and field not in mapping:
            mapping[field] = position
    return mapping


def _as_iso_date(value: object) -> str:
    if isinstance(value, (_dt.datetime, _dt.date)):
        return value.strftime("%Y-%m-%d")
    text = str(value or "").strip()
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
    return match.group(0) if match else ""


@dataclass
class NomenclatureRow:
    """One row of a nomenclature sheet, read by column title."""

    registration_no: str = ""
    code: str = ""
    inn: str = ""
    brand_name: str = ""
    form: str = ""
    strength_raw: str = ""
    packaging_raw: str = ""
    list_class: str = ""
    lab_name: str = ""
    lab_country: str = ""
    date_initial: str = ""
    date_final: str = ""
    type_code: str = ""
    status: str = ""
    stability: str = ""
    withdrawal_date: str = ""
    withdrawal_reason: str = ""
    source_version: str = ""
    source_sheet: str = ""

    @property
    def is_usable(self) -> bool:
        """A row needs at least a registration number and a substance."""
        return bool(self.registration_no and self.inn)


def read_sheet(worksheet, source_version: str) -> Iterator[NomenclatureRow]:
    """Yield the rows of one sheet.

    Cells are read by column title, so the different layout of ``Retraits``
    needs no special case: its extra columns simply map to extra fields.
    """
    header_index = find_header_row(worksheet)
    header = next(
        worksheet.iter_rows(
            min_row=header_index, max_row=header_index, values_only=True
        )
    )
    columns = _column_map(header)
    kind = sheet_kind(worksheet.title)
    date_fields = {"date_initial", "date_final", "withdrawal_date"}

    for row in worksheet.iter_rows(min_row=header_index + 1, values_only=True):
        if not any(c not in (None, "") for c in row):
            continue
        record = NomenclatureRow(source_version=source_version, source_sheet=kind)
        for field, position in columns.items():
            if not hasattr(record, field) or position >= len(row):
                continue
            value = row[position]
            if field in date_fields:
                setattr(record, field, _as_iso_date(value))
            else:
                setattr(record, field, str(value).strip() if value is not None else "")
        if record.is_usable:
            yield record


def read_workbook(
    path: str | Path,
    source_version: str | None = None,
    sheets: set[str] | None = None,
) -> list[NomenclatureRow]:
    """Read every sheet of one workbook.

    Args:
        path: the .xlsx file.
        source_version: label such as ``2026-06``; taken from the file name when
            omitted.
        sheets: restrict to these kinds (``nomenclature``, ``non_renouveles``,
            ``retraits``). All three by default.
    """
    from openpyxl import load_workbook

    path = Path(path)
    if source_version is None:
        match = re.search(r"(\d{4})[-_](\d{2})", path.stem)
        source_version = f"{match.group(1)}-{match.group(2)}" if match else path.stem

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        rows: list[NomenclatureRow] = []
        for worksheet in workbook.worksheets:
            if sheets and sheet_kind(worksheet.title) not in sheets:
                continue
            rows.extend(read_sheet(worksheet, source_version))
        return rows
    finally:
        workbook.close()
