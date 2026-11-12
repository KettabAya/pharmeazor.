"""Loading the dzair-pharma.net product exports.

These JSON files carry far more than the nomenclature: interactions with their
severity, registered generics, and occasional links to official ANPP leaflets.
They are also, by the project's own ranking, a **secondary** source — practical
but not official — so everything taken from them is labelled as such.

One subtlety the project has to get right. The interaction records state
``"source": "ANSM"``: the content originates from the ANSM thesaurus, an
institutional source, but we obtained it through a non-official relay. Both
facts are recorded, and the **lower** of the two authorities governs, because a
relay can introduce an error the original never had. Claiming ANSM authority for
a page we read on another site would overstate what we actually verified.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..schemas import Authority, InteractionLevel, Provenance

__all__ = [
    "DZAIR_SOURCE_ID",
    "Interaction",
    "GenericRef",
    "DzairProduct",
    "load_file",
    "load_directory",
    "parse_level",
]

DZAIR_SOURCE_ID = "dzair_pharma"
DZAIR_BASE_URL = "https://www.dzair-pharma.net/"

# The site's wording for the four ANSM levels.
_LEVELS: dict[str, InteractionLevel] = {
    "contre-indication": InteractionLevel.CONTRAINDICATED,
    "association deconseillee": InteractionLevel.DISCOURAGED,
    "association déconseillée": InteractionLevel.DISCOURAGED,
    "precaution d'emploi": InteractionLevel.PRECAUTION,
    "précaution d'emploi": InteractionLevel.PRECAUTION,
    "a prendre en compte": InteractionLevel.TAKE_INTO_ACCOUNT,
    "à prendre en compte": InteractionLevel.TAKE_INTO_ACCOUNT,
}

_FLAG_RE = re.compile(r"[\U0001F1E6-\U0001F1FF]{2}\s*")


def _clean(value: object) -> str:
    """Strip flag emoji and surrounding whitespace; None becomes ''."""
    if value is None:
        return ""
    text = str(value).strip()
    return _FLAG_RE.sub("", text).strip()


def parse_level(label: str | None) -> InteractionLevel | None:
    """Map the site's severity wording to the ANSM scale.

    Returns None when the wording is not recognised. The caller must then keep
    the raw label and must **not** fall back to a milder level: softening an
    unknown severity is exactly what the project forbids.

    >>> parse_level("Contre-indication") is InteractionLevel.CONTRAINDICATED
    True
    >>> parse_level("inconnu") is None
    True
    """
    if not label:
        return None
    return _LEVELS.get(_clean(label).lower())


@dataclass(frozen=True)
class Interaction:
    """One interaction, as relayed by dzair-pharma from the ANSM thesaurus."""

    substance: str
    target_kind: str          # "Substance" or "Classe"
    level_label: str          # the site's own wording, kept verbatim
    level: InteractionLevel | None
    risks: str
    what_to_do: str
    availability: str
    origin_source: str        # what the record claims, e.g. "ANSM"

    @property
    def level_fr(self) -> str:
        return self.level.label_fr if self.level else self.level_label

    @property
    def recognised(self) -> bool:
        return self.level is not None

    def effective_authority(self) -> Authority:
        """The lower of origin and relay — a relay can introduce errors."""
        origin = (
            Authority.INSTITUTIONAL
            if self.origin_source.upper() in {"ANSM", "EMA", "DAILYMED"}
            else Authority.PROFESSIONAL
        )
        return min(origin, Authority.PROFESSIONAL)


@dataclass(frozen=True)
class GenericRef:
    """A generic listed alongside a product."""

    name: str
    form: str
    strength: str
    lab: str
    kind: str
    year: str
    url: str


@dataclass
class DzairProduct:
    """One product page from dzair-pharma."""

    url: str
    status: str
    inn: str
    brand_name: str
    registration_no: str
    code: str
    atc_code: str
    product_type: str
    form: str
    route: str
    strength_raw: str
    packaging_raw: str
    prescription: str
    stability: str
    lab_name: str
    lab_country: str
    date_initial: str
    date_final: str
    nomenclature_year: str
    source_version: str
    description: str
    list_class: str
    withdrawal_reason: str
    withdrawal_date: str
    rcp_pdf_url: str
    interactions: list[Interaction] = field(default_factory=list)
    generics: list[GenericRef] = field(default_factory=list)
    collected_at: _dt.date = field(default_factory=_dt.date.today)

    @property
    def is_registered(self) -> bool:
        return self.status.lower().startswith("enregistr")

    @property
    def has_official_leaflet(self) -> bool:
        """True when the record links an ANPP RCP — a rank-4 official document."""
        return "rcp.anpp.dz" in self.rcp_pdf_url

    def provenance(self) -> Provenance:
        """dzair-pharma is a professional site: secondary, always labelled."""
        return Provenance(
            source_id=DZAIR_SOURCE_ID,
            url=self.url or DZAIR_BASE_URL,
            authority=Authority.PROFESSIONAL,
            collected_at=self.collected_at,
            language="fr",
            country="DZ",
        )

    def official_leaflet_provenance(self) -> Provenance | None:
        """Provenance of the linked ANPP leaflet, when there is one."""
        if not self.has_official_leaflet:
            return None
        return Provenance(
            source_id="anpp_rcp",
            url=self.rcp_pdf_url,
            authority=Authority.OFFICIAL,
            collected_at=self.collected_at,
            language="fr",
            country="DZ",
        )

    def interactions_by_level(self) -> dict[str, list[Interaction]]:
        out: dict[str, list[Interaction]] = {}
        for item in self.interactions:
            out.setdefault(item.level_fr, []).append(item)
        return out


def _interaction(raw: dict) -> Interaction:
    label = _clean(raw.get("gravite"))
    return Interaction(
        substance=_clean(raw.get("substance")),
        target_kind=_clean(raw.get("type")),
        level_label=label,
        level=parse_level(label),
        risks=_clean(raw.get("risques")),
        what_to_do=_clean(raw.get("conduite_a_tenir")),
        availability=_clean(raw.get("disponibilite")),
        origin_source=_clean(raw.get("source")),
    )


def _generic(raw: dict) -> GenericRef:
    return GenericRef(
        name=_clean(raw.get("nom")),
        form=_clean(raw.get("forme")),
        strength=_clean(raw.get("dosage")),
        lab=_clean(raw.get("laboratoire")),
        kind=_clean(raw.get("type")),
        year=_clean(raw.get("annee")),
        url=_clean(raw.get("url")),
    )


def _product(raw: dict, collected_at: _dt.date) -> DzairProduct:
    return DzairProduct(
        url=_clean(raw.get("url")),
        status=_clean(raw.get("status")),
        inn=_clean(raw.get("DCI (Substance active)")),
        brand_name=_clean(raw.get("Nom de marque")),
        registration_no=_clean(raw.get("N° d'enregistrement")),
        code=_clean(raw.get("Code produit")),
        atc_code=_clean(raw.get("Code ATC")),
        product_type=_clean(raw.get("Type de produit")),
        form=_clean(raw.get("Forme pharmaceutique")),
        route=_clean(raw.get("Voie d'administration")),
        strength_raw=_clean(raw.get("Dosage")),
        packaging_raw=_clean(raw.get("Conditionnement")),
        prescription=_clean(raw.get("Prescription")),
        stability=_clean(raw.get("Stabilité")),
        lab_name=_clean(raw.get("Laboratoire")),
        lab_country=_clean(raw.get("Pays d'origine")),
        date_initial=_clean(raw.get("Date d'enregistrement")),
        date_final=_clean(raw.get("Date de fin de validité")),
        nomenclature_year=_clean(raw.get("Année de nomenclature")),
        source_version=_clean(raw.get("Version source")),
        description=_clean(raw.get("description")),
        list_class=_clean(raw.get("Liste")),
        withdrawal_reason=_clean(raw.get("Motif de retrait")),
        withdrawal_date=_clean(raw.get("Date de retrait")),
        rcp_pdf_url=_clean(raw.get("RCP PDF")),
        interactions=[_interaction(i) for i in (raw.get("interactions") or [])],
        generics=[_generic(g) for g in (raw.get("generiques") or [])],
        collected_at=collected_at,
    )


def load_file(path: str | Path, collected_at: _dt.date | None = None) -> list[DzairProduct]:
    """Load one export.

    When ``collected_at`` is not given it defaults to the file's modification
    date, which is the closest honest estimate of when the data was taken.
    """
    path = Path(path)
    if collected_at is None:
        collected_at = _dt.date.fromtimestamp(path.stat().st_mtime)
    with open(path, encoding="utf-8") as handle:
        records = json.load(handle)
    return [_product(r, collected_at) for r in records]


def load_directory(
    directory: str | Path,
    only_inn: set[str] | None = None,
) -> list[DzairProduct]:
    """Load every ``*.json`` export in a directory.

    Args:
        directory: where the exports live.
        only_inn: keep just these INNs, upper-cased and matched as a prefix, so
            "PARACETAMOL" also keeps "PARACETAMOL CODEINE".
    """
    products: list[DzairProduct] = []
    for path in sorted(Path(directory).glob("*.json")):
        for product in load_file(path):
            if only_inn and not any(
                product.inn.upper().startswith(p.upper()) for p in only_inn
            ):
                continue
            products.append(product)
    return products
