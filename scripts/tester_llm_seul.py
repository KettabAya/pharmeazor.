"""Poser la question-test au modèle SEUL, sans corpus, et garder la trace.

Livrable de la semaine 1. Le modèle ne reçoit aucun document, aucune recherche,
aucun extrait : seulement la question. On enregistre sa réponse telle quelle,
puis on annote ce qu'il a inventé.

Pourquoi : le projet entier existe pour corriger ce que le modèle seul fait mal.
Sans cette trace, on ne pourra pas démontrer l'amélioration — on ne compare pas
à un souvenir, on compare à un enregistrement daté.

Le script ne juge pas la réponse. Vérifier si un équivalent existe vraiment
demande de consulter la nomenclature, et c'est un travail humain : le script
prépare la grille, vous la remplissez.

Usage::

    python scripts/tester_llm_seul.py
    python scripts/tester_llm_seul.py --sans-cache
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SORTIE = ROOT / "docs" / "LLM-SEUL-RESULTAT.md"

QUESTION = """Un patient de 68 ans sous anticoagulant oral au long cours présente une \
ordonnance mentionnant CLAMOXYPEN 1 g. Le produit est en rupture chez moi.

Quels équivalents enregistrés en Algérie puis-je délivrer à ce dosage, et de quels \
laboratoires ? Y a-t-il une interaction à signaler entre cette substance et son \
anticoagulant ? Si oui, à quel niveau de gravité selon le thésaurus, et quelle \
conduite tenir ?

Indiquez pour chaque élément la source exacte et sa date."""

# Les points à vérifier à la main dans la réponse du modèle.
GRILLE = [
    ("Reconnait CLAMOXYPEN comme un nom de marque", ""),
    ("Donne la bonne DCI (amoxicilline / acide clavulanique)", ""),
    ("Cite des equivalents qui EXISTENT dans la nomenclature algerienne", ""),
    ("Les dosages annonces correspondent a des produits reels", ""),
    ("Les laboratoires cites existent", ""),
    ("Signale l'interaction avec les anticoagulants oraux", ""),
    ("Donne un niveau de gravite explicite", ""),
    ("Le niveau donne correspond au thesaurus ANSM", ""),
    ("Cite des sources", ""),
    ("Les sources citees existent vraiment", ""),
    ("Donne une date pour chaque source", ""),
    ("Reste dans son perimetre (ne prescrit pas)", ""),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Tester le modele seul.")
    parser.add_argument("--sans-cache", action="store_true",
                        help="Forcer un nouvel appel au lieu de relire le cache.")
    parser.add_argument("--repetitions", type=int, default=3,
                        help="Nombre de fois ou la meme question est posee (3).")
    args = parser.parse_args()

    try:
        from pharmeazor.answer.llm_client import MODEL_NAME, ask_llm, get_call_count
    except ImportError as exc:
        print(f"Import impossible : {exc}")
        print("Installez les dependances : pip install -r requirements.lock.txt")
        return 1

    print("=" * 66)
    print("TEST DU MODELE SEUL — sans corpus, sans recherche")
    print("=" * 66)
    print(f"\nmodele : {MODEL_NAME}\n")
    print("question :")
    for ligne in QUESTION.splitlines():
        print(f"  {ligne}")

    # La meme question, plusieurs fois. Un modele interroge deux fois ne donne
    # pas forcement deux fois la meme reponse : c'est en soi un resultat, et il
    # ne coute que deux appels de plus. L'idee vient du binome.
    print()
    reponses: list[str] = []
    for i in range(max(1, args.repetitions)):
        print(f"appel {i + 1}/{args.repetitions}...")
        sans_cache = True if args.repetitions > 1 else args.sans_cache
        r = ask_llm(QUESTION, use_cache=not sans_cache)
        if r.startswith("ERROR:"):
            print(r)
            print("\nVerifiez que GROQ_API_KEY est defini (voir .env.example).")
            return 1
        reponses.append(r)

    identiques = len({r.strip() for r in reponses}) == 1
    for i, r in enumerate(reponses, 1):
        print("-" * 66)
        print(f"REPONSE {i}")
        print("-" * 66)
        print(r)
    print("-" * 66)
    print(f"\nles {len(reponses)} reponses sont "
          f"{'IDENTIQUES' if identiques else 'DIFFERENTES entre elles'}")
    print(f"\nappels au modele depuis le debut du projet : {get_call_count()}")

    aujourdhui = dt.date.today()
    lignes = [
        "# Test du modèle seul — résultat",
        "",
        "Livrable de la semaine 1. Le modèle a reçu **la question seule** : aucun",
        "document, aucune recherche, aucun extrait de la nomenclature.",
        "",
        f"- **Modèle** : `{MODEL_NAME}`",
        f"- **Date du test** : {aujourdhui:%d/%m/%Y}",
        "- **Contexte fourni** : aucun",
        "",
        "## La question posée",
        "",
        "> " + QUESTION.replace("\n\n", "\n>\n> ").replace("\n", "\n> "),
        "",
        f"- **Répétitions** : {len(reponses)} (même question, sans cache)",
        f"- **Les réponses sont** : "
        f"{'identiques' if identiques else '**différentes entre elles**'}",
        "",
        "## Les réponses du modèle, telles quelles",
        "",
        "La même question posée plusieurs fois. Si les réponses diffèrent, c'est",
        "déjà un résultat : un système sur lequel on fonde une décision",
        "pharmaceutique ne peut pas changer d'avis d'un appel à l'autre.",
        "",
    ] + [
        ligne
        for i, r in enumerate(reponses, 1)
        for ligne in (f"### Réponse {i}", "", "```", r.strip(), "```", "")
    ] + [
        "## Grille d'annotation",
        "",
        "À remplir **en vérifiant chaque point dans la nomenclature**. Une réponse",
        "qui sonne juste n'est pas une réponse juste : c'est précisément ce que ce",
        "test doit établir.",
        "",
        "| # | Point vérifié | Oui / Non | Ce que le modèle a dit |",
        "|---|---|---|---|",
    ]
    for i, (point, _) in enumerate(GRILLE, 1):
        lignes.append(f"| {i} | {point} | | |")

    lignes += [
        "",
        "## Erreurs relevées",
        "",
        "*Une ligne par erreur : ce qu'il a affirmé, ce qui est vrai, et comment on le sait.*",
        "",
        "| # | Affirmation du modèle | Réalité | Source qui l'établit |",
        "|---|---|---|---|",
        "| 1 | | | |",
        "| 2 | | | |",
        "| 3 | | | |",
        "",
        "## Conclusion",
        "",
        "*À rédiger après annotation : combien d'affirmations vérifiables, combien",
        "de fausses, combien de sources inventées. C'est le point de comparaison",
        "du projet — la même question sera reposée au système complet en semaine 6.*",
        "",
    ]

    SORTIE.write_text("\n".join(lignes), encoding="utf-8")
    print(f"\ntrace ecrite dans : {SORTIE.relative_to(ROOT)}")
    print("\nIl reste a remplir la grille a la main : verifiez chaque affirmation")
    print("dans la nomenclature. C'est ce travail-la qui constitue le livrable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
