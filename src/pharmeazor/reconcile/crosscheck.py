"""Comparing the nomenclature against dzair-pharma on the same product.

Both sources carry the registration number (``503/03 B 061/16``), which makes
them joinable. That join is what turns two separate datasets into a
reconciliation problem: for every product present in both, each field can be
compared, and a disagreement is detected rather than averaged away.

The arbitration rule is the project's golden rule: the higher-ranked source
wins, and the system says why. The official nomenclature outranks the
professional site, so the nomenclature's value is retained — but the divergent
value stays visible, with its own origin, because hiding it would be exactly
the behaviour the spec forbids.

A difference is not always an error. A product can legitimately have been
updated between two collection dates. That is why every disagreement carries
both dates: the reader, not the system, decides whether it is staleness or a
mistake.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from ..normalize.catalogue import Product
from ..schemas import Authority

__all__ = [
    "COMPARED_FIELDS",
    "Disagreement",
    "ProductPair",
    "normalize_value",
    "join_on_registration",
    "compare_pair",
    "compare_all",
]

# (field label, how to read it from each side)
COMPARED_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("dci", "inn", "inn"),
    ("nom_de_marque", "brand_name", "brand_name"),
    ("forme", "form", "form"),
    ("dosage", "strength_raw", "strength_raw"),
    ("conditionnement", "packaging_raw", "packaging_raw"),
    ("laboratoire", "lab_name", "lab_name"),
    ("date_enregistrement", "date_initial", "date_initial"),
)


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_value(value: str | None) -> str:
    """Flatten case, accents, punctuation and spacing before comparing.

    Without this, ``COMPRIME PELLICULE`` and ``Comprimé pelliculé`` would be
    reported as a disagreement, which would drown the real ones in noise.
    """
    text = _strip_accents(str(value or "").upper())
    text = re.sub(r"[^\w]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class Disagreement:
    """One field where the two sources do not say the same thing."""

    registration_no: str
    field_name: str
    official_value: str
    secondary_value: str
    official_source: str
    secondary_source: str
    official_collected: str
    secondary_collected: str

    @property
    def retained(self) -> str:
        """The official value always wins — and we record why below."""
        return self.official_value

    @property
    def reason_fr(self) -> str:
        return (
            f"Valeur retenue : « {self.official_value} » "
            f"({self.official_source}, rang {int(Authority.NOMENCLATURE)}). "
            f"Valeur divergente signalée : « {self.secondary_value} » "
            f"({self.secondary_source}, rang {int(Authority.PROFESSIONAL)}). "
            f"Dates de collecte : {self.official_collected} contre "
            f"{self.secondary_collected} — une différence peut venir d'une "
            f"mise à jour entre les deux relevés."
        )


@dataclass
class ProductPair:
    """The same registered product, seen by both sources."""

    registration_no: str
    official: Product
    secondary: object  # DzairProduct; kept loose to avoid a circular import


@dataclass
class CrossCheckReport:
    """What the comparison found."""

    pairs: list[ProductPair] = field(default_factory=list)
    disagreements: list[Disagreement] = field(default_factory=list)
    official_only: list[str] = field(default_factory=list)
    secondary_only: list[str] = field(default_factory=list)

    @property
    def agreement_rate(self) -> float:
        """Share of compared fields on which the two sources agree."""
        total = len(self.pairs) * len(COMPARED_FIELDS)
        if not total:
            return 0.0
        return 1 - len(self.disagreements) / total

    def by_field(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for d in self.disagreements:
            counts[d.field_name] = counts.get(d.field_name, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def join_on_registration(
    official: list[Product],
    secondary: list,
) -> tuple[list[ProductPair], list[str], list[str]]:
    """Match products by registration number.

    Returns the pairs, then the registration numbers seen only in the official
    source, then those seen only in the secondary one. Both lists matter: a
    product missing from the official registry but advertised on a professional
    site is a finding, not a gap to paper over.
    """
    by_reg_official: dict[str, Product] = {
        normalize_value(p.registration_no): p for p in official if p.registration_no
    }
    by_reg_secondary: dict[str, object] = {
        normalize_value(p.registration_no): p for p in secondary if p.registration_no
    }

    pairs = [
        ProductPair(reg, by_reg_official[reg], by_reg_secondary[reg])
        for reg in by_reg_official.keys() & by_reg_secondary.keys()
    ]
    pairs.sort(key=lambda p: p.registration_no)

    only_official = sorted(by_reg_official.keys() - by_reg_secondary.keys())
    only_secondary = sorted(by_reg_secondary.keys() - by_reg_official.keys())
    return pairs, only_official, only_secondary


def compare_pair(pair: ProductPair) -> list[Disagreement]:
    """Compare one product across the two sources."""
    found: list[Disagreement] = []
    official_prov = pair.official.provenance()
    secondary_prov = pair.secondary.provenance()

    for label, official_attr, secondary_attr in COMPARED_FIELDS:
        official_value = str(getattr(pair.official, official_attr, "") or "")
        secondary_value = str(getattr(pair.secondary, secondary_attr, "") or "")

        # An empty value on either side is a gap, not a disagreement.
        if not official_value.strip() or not secondary_value.strip():
            continue
        if normalize_value(official_value) == normalize_value(secondary_value):
            continue

        found.append(
            Disagreement(
                registration_no=pair.official.registration_no,
                field_name=label,
                official_value=official_value,
                secondary_value=secondary_value,
                official_source=official_prov.source_id,
                secondary_source=secondary_prov.source_id,
                official_collected=f"{official_prov.collected_at:%d/%m/%Y}",
                secondary_collected=f"{secondary_prov.collected_at:%d/%m/%Y}",
            )
        )
    return found


def compare_all(official: list[Product], secondary: list) -> CrossCheckReport:
    """Join the two sources and compare every product they share."""
    pairs, only_official, only_secondary = join_on_registration(official, secondary)
    report = CrossCheckReport(
        pairs=pairs, official_only=only_official, secondary_only=only_secondary
    )
    for pair in pairs:
        report.disagreements.extend(compare_pair(pair))
    return report
