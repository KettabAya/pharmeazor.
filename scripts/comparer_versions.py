"""Comparer les versions successives de la nomenclature.

Le ministère republie son registre tous les deux mois. Cinq versions datées
(décembre 2025 → août 2026) permettent de voir ce qui change dans le temps :
produits ajoutés, produits retirés, et champs modifiés sur un produit qui reste.

C'est ce qui fournit les **désaccords réels** que le cahier des charges exige
(au moins dix, repérés et annotés), et c'est aussi l'extension « suivi des
versions ». Contrairement à une comparaison entre deux sites, les écarts trouvés
ici sont **datables** : on sait exactement entre quelles deux dates le registre
a changé d'avis.

Un écart n'est pas forcément une erreur. Un renouvellement d'enregistrement
change légitimement la date de fin de validité. C'est pourquoi chaque ligne du
rapport porte les deux versions et les deux valeurs : le lecteur tranche, pas
le script.

Usage::

    python scripts/comparer_versions.py
    python scripts/comparer_versions.py --inn PARACETAMOL
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmeazor.collect.nomenclature import read_workbook  # noqa: E402
from pharmeazor.reconcile.crosscheck import normalize_value  # noqa: E402

VERSIONS_DIR = ROOT / "data" / "raw" / "nomenclature"
SORTIE = ROOT / "data" / "reference" / "desaccords_versions.csv"

DEFAUT_INN = ("PARACETAMOL", "AMOXICILLINE", "AMLODIPINE")

# Champs suivis d'une version à l'autre, avec leur libellé pour le rapport.
CHAMPS: dict[str, str] = {
    "inn": "DCI",
    "brand_name": "nom de marque",
    "form": "forme",
    "strength_raw": "dosage",
    "packaging_raw": "conditionnement",
    "lab_name": "laboratoire",
    "lab_country": "pays du laboratoire",
    "list_class": "liste",
    "status": "statut",
    "date_final": "date de fin de validite",
}


def charger(cibles: tuple[str, ...]) -> dict[str, dict]:
    """Charger chaque version, indexée par numéro d'enregistrement."""
    versions: dict[str, dict] = {}
    for fichier in sorted(VERSIONS_DIR.glob("*.xlsx")):
        version = fichier.stem.replace("nomenclature_", "")
        lignes = [
            r for r in read_workbook(fichier, sheets={"nomenclature"})
            if not cibles or any(r.inn.upper().startswith(c) for c in cibles)
        ]
        versions[version] = {r.registration_no: r for r in lignes if r.registration_no}
        print(f"  {version}  {len(lignes):>5} produits")
    return versions


def comparer(versions: dict[str, dict]) -> tuple[list[dict], Counter, list[dict]]:
    """Comparer chaque version à la suivante."""
    noms = sorted(versions)
    desaccords: list[dict] = []
    mouvements: list[dict] = []
    par_champ: Counter = Counter()

    # strict=False volontaire : noms[1:] est plus court d'un element,
    # puisqu'on apparie chaque version avec la suivante.
    for avant, apres in zip(noms, noms[1:], strict=False):
        va, vb = versions[avant], versions[apres]
        communs = va.keys() & vb.keys()

        for reg in sorted(vb.keys() - va.keys()):
            mouvements.append({"version_avant": avant, "version_apres": apres,
                               "mouvement": "ajoute", "n_enregistrement": reg,
                               "marque": vb[reg].brand_name, "dci": vb[reg].inn})
        for reg in sorted(va.keys() - vb.keys()):
            mouvements.append({"version_avant": avant, "version_apres": apres,
                               "mouvement": "retire", "n_enregistrement": reg,
                               "marque": va[reg].brand_name, "dci": va[reg].inn})

        for reg in sorted(communs):
            for champ, libelle in CHAMPS.items():
                x = str(getattr(va[reg], champ, "") or "")
                y = str(getattr(vb[reg], champ, "") or "")
                # Une case vide d'un côté est une lacune, pas un désaccord.
                if not x.strip() or not y.strip():
                    continue
                if normalize_value(x) == normalize_value(y):
                    continue
                par_champ[libelle] += 1
                desaccords.append({
                    "n_enregistrement": reg,
                    "marque": vb[reg].brand_name,
                    "dci": vb[reg].inn,
                    "champ": libelle,
                    "version_avant": avant,
                    "valeur_avant": x,
                    "version_apres": apres,
                    "valeur_apres": y,
                    "valeur_retenue": y,
                    "justification": (
                        f"La version {apres} est posterieure a {avant} : a rang "
                        f"d'autorite egal, la collecte la plus recente l'emporte. "
                        f"Un ecart peut venir d'un renouvellement d'enregistrement "
                        f"et non d'une erreur."
                    ),
                })
    return desaccords, par_champ, mouvements


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparer les versions de la nomenclature.")
    parser.add_argument("--inn", nargs="*", default=list(DEFAUT_INN),
                        help="DCI a suivre ; vide = toutes.")
    args = parser.parse_args()
    cibles = tuple(x.upper() for x in args.inn)

    fichiers = list(VERSIONS_DIR.glob("*.xlsx"))
    if len(fichiers) < 2:
        print(f"Il faut au moins deux versions dans {VERSIONS_DIR}.")
        return 1

    print(f"Molecules suivies : {', '.join(cibles) if cibles else 'toutes'}\n")
    versions = charger(cibles)
    desaccords, par_champ, mouvements = comparer(versions)

    with open(SORTIE, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(desaccords[0].keys())) if desaccords else None
        if w:
            w.writeheader()
            w.writerows(desaccords)

    print(f"\n{'='*58}")
    print(f"DESACCORDS DATABLES : {len(desaccords)}")
    print(f"{'='*58}")
    exige = 10
    etat = "OK" if len(desaccords) >= exige else "INSUFFISANT"
    print(f"  exigence du cahier des charges : au moins {exige}  -> {etat}")
    print(f"  ecrits dans : {SORTIE.name}\n")
    for libelle, n in par_champ.most_common():
        print(f"    {n:>4}  {libelle}")

    ajouts = sum(1 for m in mouvements if m["mouvement"] == "ajoute")
    retraits = sum(1 for m in mouvements if m["mouvement"] == "retire")
    print(f"\n  mouvements : {ajouts} produit(s) ajoute(s), {retraits} retire(s)")

    print("\n--- trois exemples ---")
    for d in desaccords[:3]:
        print(f"  [{d['n_enregistrement']}] {d['marque']} — {d['champ']}")
        print(f"     {d['version_avant']} : {d['valeur_avant'][:48]}")
        print(f"     {d['version_apres']} : {d['valeur_apres'][:48]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
