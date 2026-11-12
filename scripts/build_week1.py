"""Build the week-1 deliverables from the two sources.

Reads the official nomenclature workbook and the dzair-pharma exports, keeps the
three starter molecules, then produces:

* ``data/reference/drugs_semaine1.csv``        — the merged product table
* ``data/reference/name_index.csv``            — every written form -> a product
* ``data/reference/equivalents_semaine1.csv``  — interchangeable boxes
* ``data/reference/interactions_semaine1.csv`` — interactions with their level
* ``data/reference/conflits_semaine1.csv``     — where the two sources disagree

and prints a worked answer with its citations.

Usage::

    python scripts/build_week1.py
    python scripts/build_week1.py --question BRUFEN
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmeazor.collect.dzair import load_directory  # noqa: E402
from pharmeazor.collect.nomenclature import read_workbook  # noqa: E402
from pharmeazor.normalize.catalogue import Catalogue  # noqa: E402
from pharmeazor.reconcile.crosscheck import compare_all  # noqa: E402

# The three starter molecules: one per therapeutic class, as the spec asks.
# Override on the command line with --inn.
TARGET_INN: tuple[str, ...] = ("PARACETAMOL", "AMOXICILLINE", "AMLODIPINE")

# Which class each INN belongs to. Anything unlisted is reported rather than
# silently filed under a default.
CLASS_OF: dict[str, str] = {
    "PARACETAMOL": "antalgique_ains",
    "IBUPROFENE": "antalgique_ains",
    "DICLOFENAC": "antalgique_ains",
    "AMOXICILLINE": "antibiotique",
    "AMLODIPINE": "antihypertenseur",
}

RAW_XLSX = ROOT / "data" / "raw" / "nomenclature"
RAW_JSON = ROOT / "data" / "raw" / "dzair"
REFERENCE = ROOT / "data" / "reference"

PRODUCTS = REFERENCE / "drugs_semaine1.csv"
NAME_INDEX = REFERENCE / "name_index.csv"
EQUIVALENTS = REFERENCE / "equivalents_semaine1.csv"
INTERACTIONS = REFERENCE / "interactions_semaine1.csv"
CONFLICTS = REFERENCE / "conflits_semaine1.csv"

PRODUCT_FIELDS = [
    "drug_id", "therapeutic_class", "inn", "brand_name", "code",
    "registration_no", "form", "strength_raw", "packaging_raw", "list_class",
    "lab_name", "lab_country", "date_initial", "date_final", "type_code",
    "status", "source_version", "source_sheet",
]


def targeted(inn: str, targets: tuple[str, ...]) -> bool:
    upper = (inn or "").upper()
    return any(upper.startswith(t) for t in targets)


def therapeutic_class(inn: str) -> str:
    upper = (inn or "").upper()
    for prefix, klass in CLASS_OF.items():
        if upper.startswith(prefix):
            return klass
    return "non_classe"


def extract_nomenclature(targets: tuple[str, ...]) -> list[dict]:
    """Read every workbook in data/raw/nomenclature and keep the three INNs."""
    books = sorted(RAW_XLSX.glob("*.xlsx"))
    if not books:
        raise SystemExit(
            f"Aucun classeur dans {RAW_XLSX}. Copiez-y la nomenclature "
            "(voir docs/SEMAINE-1.md, etape 0.2)."
        )

    rows: list[dict] = []
    for book in books:
        for row in read_workbook(book, sheets={"nomenclature"}):
            if not targeted(row.inn, targets):
                continue
            rows.append({
                "drug_id": f"DZ-{len(rows) + 1:04d}",
                "therapeutic_class": therapeutic_class(row.inn),
                "inn": row.inn,
                "brand_name": row.brand_name,
                "code": row.code,
                "registration_no": row.registration_no,
                "form": row.form,
                "strength_raw": row.strength_raw,
                "packaging_raw": row.packaging_raw,
                "list_class": row.list_class,
                "lab_name": row.lab_name,
                "lab_country": row.lab_country,
                "date_initial": row.date_initial,
                "date_final": row.date_final,
                "type_code": row.type_code,
                "status": row.status,
                "source_version": row.source_version,
                "source_sheet": row.source_sheet,
            })

    with open(PRODUCTS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PRODUCT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_name_index(catalogue: Catalogue) -> int:
    aliases = catalogue.aliases()
    with open(NAME_INDEX, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["alias", "alias_normalized", "kind", "drug_id", "inn"])
        for a in sorted(aliases, key=lambda x: (x.kind, x.alias)):
            product = catalogue.get(a.drug_id)
            writer.writerow([a.alias, a.alias_normalized, a.kind, a.drug_id,
                             product.inn if product else ""])
    return len(aliases)


def write_equivalents(catalogue: Catalogue) -> int:
    groups = [g for g in catalogue.groups() if g.size > 1]
    with open(EQUIVALENTS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "group_id", "inn", "strength", "form_family", "group_size",
            "drug_id", "brand_name", "form", "packaging", "lab_name",
            "registration_no", "status",
        ])
        for i, group in enumerate(groups, 1):
            for p in group.products:
                writer.writerow([
                    f"EQ-{i:04d}", group.inn, group.strength, group.form_family,
                    group.size, p.drug_id, p.brand_name, p.form,
                    p.packaging.raw, p.lab_name, p.registration_no, p.status,
                ])
    return len(groups)


def write_interactions(dzair_products: list) -> tuple[int, dict[str, int]]:
    """Export every interaction, with its level and both sources."""
    levels: dict[str, int] = {}
    seen: set[tuple] = set()
    written = 0

    with open(INTERACTIONS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "inn", "brand_name", "registration_no", "substance_cible",
            "type_cible", "niveau", "niveau_reconnu", "risques",
            "conduite_a_tenir", "source_origine", "source_relais",
            "autorite_effective", "url",
        ])
        for product in dzair_products:
            for item in product.interactions:
                key = (product.inn.upper(), item.substance.upper(), item.level_label)
                if key in seen:
                    continue
                seen.add(key)
                levels[item.level_fr] = levels.get(item.level_fr, 0) + 1
                writer.writerow([
                    product.inn, product.brand_name, product.registration_no,
                    item.substance, item.target_kind, item.level_fr,
                    "oui" if item.recognised else "non",
                    item.risks, item.what_to_do,
                    item.origin_source or "(non precisee)", "dzair_pharma",
                    item.effective_authority().label_fr, product.url,
                ])
                written += 1
    return written, levels


def write_conflicts(report) -> int:
    with open(CONFLICTS, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "n_enregistrement", "champ", "valeur_officielle", "valeur_secondaire",
            "source_officielle", "source_secondaire", "collecte_officielle",
            "collecte_secondaire", "valeur_retenue", "justification",
        ])
        for d in report.disagreements:
            writer.writerow([
                d.registration_no, d.field_name, d.official_value,
                d.secondary_value, d.official_source, d.secondary_source,
                d.official_collected, d.secondary_collected, d.retained,
                d.reason_fr,
            ])
    return len(report.disagreements)


def show_answer(catalogue: Catalogue, name: str) -> None:
    answer = catalogue.equivalents_of(name)
    print("\n" + "=" * 74)
    print(f"QUESTION : « {name} est en rupture, quels équivalents enregistrés ? »")
    print("=" * 74)
    if answer["refused"]:
        print(f"\nRÉPONSE   : {answer['short']}")
        print(f"LIMITES   : {answer['limits']}")
        print("\n(Refus assumé : le système ne devine pas.)")
        return
    print(f"\nRÉPONSE   : {answer['short']}")
    print(f"\nEXPLICATION : {answer['explanation']}")
    print(f"\nSOURCES CITÉES ({len(answer['citations'])}) :")
    print(f"  {answer['citations'][0]['source']}")
    for c in answer["citations"][:8]:
        print(f"    [{c['registration_no']}] {c['quote']}")
    if len(answer["citations"]) > 8:
        print(f"    … et {len(answer['citations']) - 8} autres")
    print(f"\nLIMITES   : {answer['limits']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Livrables de la semaine 1.")
    parser.add_argument("--question", help="Nom de marque pour l'exemple travaillé.")
    parser.add_argument(
        "--inn", nargs="+", default=list(TARGET_INN),
        help="DCI à retenir (par défaut : une par classe thérapeutique).",
    )
    args = parser.parse_args()
    targets = tuple(x.upper() for x in args.inn)

    print(f"Molécules retenues : {', '.join(targets)}\n")

    rows = extract_nomenclature(targets)
    print(f"[1] Nomenclature officielle : {len(rows)} produits -> {PRODUCTS.name}")
    for inn in targets:
        n = sum(1 for r in rows if r["inn"].upper().startswith(inn))
        klass = therapeutic_class(inn)
        print(f"      {inn:<14} {n:>4}   ({klass})")

    dzair = load_directory(RAW_JSON, only_inn=set(targets))
    covered = {inn for inn in targets
               if any(p.inn.upper().startswith(inn) for p in dzair)}
    missing = [inn for inn in targets if inn not in covered]
    n_inter = sum(len(p.interactions) for p in dzair)
    n_rcp = sum(1 for p in dzair if p.has_official_leaflet)
    print(f"\n[2] dzair-pharma (secondaire) : {len(dzair)} produits, "
          f"{n_inter} interactions, {n_rcp} lien(s) RCP officiel")
    if missing:
        print(f"      ATTENTION — aucune donnée dzair pour : {', '.join(missing)}")
        print("      Ces molécules n'ont qu'une seule source : pas d'interactions,")
        print("      pas de RCP officiel, et rien à réconcilier.")

    catalogue = Catalogue.from_csv(PRODUCTS)
    unparsed = [p for p in catalogue.products if not p.strength.parsed]
    print(f"\n[3] Dosages lus : {len(catalogue.products) - len(unparsed)}"
          f"/{len(catalogue.products)}")
    if unparsed:
        print(f"      non lus : {[p.strength.raw for p in unparsed][:6]}")

    n_aliases = write_name_index(catalogue)
    print(f"[4] Dictionnaire des noms : {n_aliases} entrées -> {NAME_INDEX.name}")

    n_groups = write_equivalents(catalogue)
    grouped = sum(g.size for g in catalogue.groups() if g.size > 1)
    print(f"[5] Équivalents : {n_groups} groupes, {grouped} produits -> {EQUIVALENTS.name}")

    n_written, levels = write_interactions(dzair)
    print(f"[6] Interactions : {n_written} uniques -> {INTERACTIONS.name}")
    for level, count in sorted(levels.items(), key=lambda kv: -kv[1]):
        print(f"      {count:>5}  {level}")

    report = compare_all(catalogue.products, dzair)
    n_conflicts = write_conflicts(report)
    print("\n[7] Réconciliation des deux sources")
    print(f"      produits présents dans les deux : {len(report.pairs)}")
    print(f"      désaccords détectés             : {n_conflicts} -> {CONFLICTS.name}")
    print(f"      taux d'accord sur les champs    : {report.agreement_rate:.1%}")
    if report.by_field():
        print("      par champ :")
        for field_name, count in report.by_field().items():
            print(f"        {count:>4}  {field_name}")
    print(f"      seulement dans la nomenclature  : {len(report.official_only)}")
    print(f"      seulement chez dzair-pharma     : {len(report.secondary_only)}")

    demo = args.question
    if not demo:
        for group in catalogue.groups():
            for product in group.products:
                if not catalogue.equivalents_of(product.brand_name)["refused"]:
                    demo = product.brand_name
                    break
            if demo:
                break
    if demo:
        show_answer(catalogue, demo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
