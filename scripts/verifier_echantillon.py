"""Tirer un échantillon au hasard, à vérifier à la main dans le classeur source.

La table extraite est le socle de tout le reste : si elle est fausse, tout ce qui
est construit dessus l'est aussi, sans qu'aucun test ne s'en aperçoive. Un test
vérifie que le code fait ce qu'on lui a dit ; il ne vérifie pas que ce qu'on lui
a dit correspond au document d'origine. Cela, seul un humain peut le faire.

Ce script n'ouvre jamais le classeur : il imprime des lignes au hasard et vous
laisse les retrouver vous-même. S'il les cherchait pour vous, il vérifierait sa
propre lecture, ce qui ne prouve rien.

Usage::

    python scripts/verifier_echantillon.py
    python scripts/verifier_echantillon.py --nombre 10
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "reference" / "drugs_semaine1.csv"

CHAMPS = [
    ("registration_no", "N° d'enregistrement"),
    ("inn", "DCI"),
    ("brand_name", "Nom de marque"),
    ("form", "Forme"),
    ("strength_raw", "Dosage"),
    ("packaging_raw", "Conditionnement"),
    ("lab_name", "Laboratoire"),
    ("date_initial", "Date d'enregistrement"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Échantillon à vérifier à la main.")
    parser.add_argument("--nombre", type=int, default=5, help="Lignes à tirer (5).")
    parser.add_argument("--graine", type=int, help="Pour retirer le même échantillon.")
    args = parser.parse_args()

    if not SOURCE.exists():
        print(f"Fichier introuvable : {SOURCE}")
        print("Lancez d'abord : python scripts/build_week1.py")
        return 1

    with open(SOURCE, encoding="utf-8", newline="") as fh:
        lignes = list(csv.DictReader(fh))

    if args.graine is not None:
        random.seed(args.graine)
    echantillon = random.sample(lignes, min(args.nombre, len(lignes)))

    classeurs = sorted((ROOT / "data" / "raw" / "nomenclature").glob("*.xlsx"))
    nom_classeur = classeurs[0].name if classeurs else "le classeur de la nomenclature"

    print("=" * 72)
    print(f"VÉRIFICATION À LA MAIN — {len(echantillon)} lignes sur {len(lignes)}")
    print("=" * 72)
    print(f"""
Ouvrez {nom_classeur}, feuille « Nomenclature ».

Pour chaque produit ci-dessous :
  1. Ctrl+F, collez le N° d'enregistrement, Entrée
  2. Comparez les sept champs, un par un
  3. Cochez la case si tout correspond

Un seul écart suffit à arrêter : prévenez l'équipe avant de continuer.
""")

    for i, ligne in enumerate(echantillon, 1):
        print("-" * 72)
        print(f"[ ]  Produit {i} / {len(echantillon)}   ({ligne['drug_id']})")
        for cle, libelle in CHAMPS:
            valeur = ligne.get(cle, "") or "(vide)"
            print(f"       {libelle:<22} {valeur}")

    print("-" * 72)
    print(f"""
Si les {len(echantillon)} correspondent : la table est fiable, continuez.
Si une ligne diffère : notez laquelle et quel champ, et signalez-le.

Pour retirer exactement le même échantillon plus tard :
    python scripts/verifier_echantillon.py --graine 42
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
