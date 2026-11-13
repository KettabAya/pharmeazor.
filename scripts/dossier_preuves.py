"""Produire un dossier de preuves horodaté, extrait du dépôt lui-même.

Rassemble en un seul fichier ce qu'un correcteur peut vouloir vérifier sans
cloner le projet : la contribution de chaque personne relevée dans l'historique
Git, l'inventaire des livrables avec leur empreinte, le résultat de la suite de
tests, et les commandes qui reproduisent chaque chiffre.

Rien n'est saisi à la main : tout est lu dans le dépôt au moment de
l'exécution. Un dossier de preuves qu'on écrirait soi-même ne prouverait rien.

Usage::

    python scripts/dossier_preuves.py
    python scripts/dossier_preuves.py --sortie DOSSIER.md
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LIVRABLES = [
    ("data/reference/drugs_semaine1.csv", "table produit nettoyée"),
    ("data/reference/name_index.csv", "dictionnaire des noms"),
    ("data/reference/equivalents_semaine1.csv", "groupes d'équivalents"),
    ("data/reference/interactions_semaine1.csv", "interactions avec niveau ANSM"),
    ("data/reference/desaccords_versions.csv", "désaccords entre versions datées"),
    ("data/reference/source_registry.yaml", "registre des sources et conformité"),
    ("data/reference/documents_a_collecter.csv", "liste de collecte des notices"),
    ("eval/llm_alone_test.json", "trace du test du modèle seul"),
    ("preprocessing.ipynb", "notebook de traitement"),
]

COMMANDES = [
    ("git log --format='%an %ad %s' --date=short", "qui a contribué, et quand"),
    ("python scripts/build_week1.py", "régénère table, dictionnaire, équivalents, interactions"),
    ("python scripts/comparer_versions.py", "les désaccords entre versions du registre"),
    ("python scripts/verifier_echantillon.py", "tire 5 produits à vérifier à la main"),
    ("pytest", "la suite de tests"),
]


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", errors="replace").stdout.strip()
    except FileNotFoundError:
        return ""


def empreinte(chemin: Path) -> str:
    """SHA-256 tronquée : permet de prouver qu'un fichier n'a pas bougé."""
    h = hashlib.sha256()
    h.update(chemin.read_bytes())
    return h.hexdigest()[:16]


def lignes_csv(chemin: Path) -> int:
    with open(chemin, encoding="utf-8", newline="") as fh:
        return max(0, sum(1 for _ in csv.reader(fh)) - 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Dossier de preuves horodaté.")
    parser.add_argument("--sortie", default="DOSSIER-DE-PREUVES.md")
    args = parser.parse_args()

    maintenant = dt.datetime.now()
    out: list[str] = [
        "# Dossier de preuves — Pharmeazor",
        "",
        f"Généré le **{maintenant:%d/%m/%Y à %H:%M}** depuis le dépôt lui-même.",
        "Aucune valeur n'est saisie à la main : tout est relevé à l'exécution.",
        "",
        f"- Dépôt : `{git('config', '--get', 'remote.origin.url') or '(local)'}`",
        f"- Branche : `{git('rev-parse', '--abbrev-ref', 'HEAD')}`",
        f"- Commit : `{git('rev-parse', '--short', 'HEAD')}`",
        f"- Total : **{git('rev-list', '--count', 'HEAD')} commits**, "
        f"{len(git('ls-files').splitlines())} fichiers suivis",
        "",
        "---",
        "",
        "## 1. Contribution par personne",
        "",
        "Relevée dans l'historique Git. Un commit porte un auteur, une date et une",
        "empreinte : ces chiffres ne sont pas déclarés, ils sont constatés.",
        "",
        "| Auteur | Commits | Lignes ajoutées | Lignes retirées | Première | Dernière |",
        "|---|---:|---:|---:|---|---|",
    ]

    auteurs = sorted(set(git("log", "--format=%an").splitlines()))
    for auteur in auteurs:
        if not auteur:
            continue
        n = len(git("log", f"--author={auteur}", "--format=%h").splitlines())
        stats = git("log", f"--author={auteur}", "--pretty=tformat:", "--numstat")
        add = dele = 0
        for ligne in stats.splitlines():
            morceaux = ligne.split("\t")
            if len(morceaux) >= 2:
                add += int(morceaux[0]) if morceaux[0].isdigit() else 0
                dele += int(morceaux[1]) if morceaux[1].isdigit() else 0
        dates = git("log", f"--author={auteur}", "--format=%ad", "--date=short").splitlines()
        out.append(f"| **{auteur}** | {n} | +{add:,} | −{dele:,} | "
                   f"{dates[-1] if dates else '—'} | {dates[0] if dates else '—'} |")

    out += ["", "### Fichiers touchés par chaque personne", ""]
    for auteur in auteurs:
        if not auteur:
            continue
        fichiers = sorted(set(
            f for f in git("log", f"--author={auteur}", "--pretty=tformat:",
                           "--name-only").splitlines() if f.strip()
        ))
        out.append(f"**{auteur}** — {len(fichiers)} fichiers")
        out.append("")
        for f in fichiers[:14]:
            out.append(f"- `{f}`")
        if len(fichiers) > 14:
            out.append(f"- *… et {len(fichiers) - 14} autres*")
        out.append("")

    out += [
        "---",
        "",
        "## 2. Livrables, avec leur empreinte",
        "",
        "L'empreinte SHA-256 permet de vérifier qu'un fichier est bien celui-ci et",
        "qu'il n'a pas été modifié depuis.",
        "",
        "| Fichier | Contenu | Lignes | Empreinte |",
        "|---|---|---:|---|",
    ]
    for rel, desc in LIVRABLES:
        chemin = ROOT / rel
        if not chemin.exists():
            out.append(f"| `{rel}` | {desc} | — | *absent* |")
            continue
        n = lignes_csv(chemin) if rel.endswith(".csv") else "—"
        out.append(f"| `{rel}` | {desc} | {n} | `{empreinte(chemin)}` |")

    out += ["", "---", "", "## 3. Suite de tests", ""]
    res = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header"],
                         cwd=ROOT, capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    derniere = [x for x in (res.stdout or "").strip().splitlines() if x.strip()]
    out += [
        "```",
        *(derniere[-6:] if derniere else ["(pytest indisponible)"]),
        "```",
        "",
        f"Code de sortie : **{res.returncode}** " +
        ("— tous les tests passent." if res.returncode == 0 else "— **des tests échouent**."),
        "",
        "---",
        "",
        "## 4. Reproduire chaque chiffre",
        "",
        "| Commande | Ce qu'elle établit |",
        "|---|---|",
    ]
    for cmd, quoi in COMMANDES:
        out.append(f"| `{cmd}` | {quoi} |")

    out += [
        "",
        "---",
        "",
        "## 5. Les vingt derniers commits",
        "",
        "```",
        git("log", "-20", "--format=%h  %ad  %-14an  %s", "--date=short"),
        "```",
        "",
        "---",
        "",
        "*Pour régénérer ce dossier : `python scripts/dossier_preuves.py`*",
        "",
    ]

    sortie = ROOT / args.sortie
    sortie.write_text("\n".join(out), encoding="utf-8")
    print(f"  ecrit : {sortie.name}  ({sortie.stat().st_size / 1024:.0f} Ko)")
    print(f"  {len([a for a in auteurs if a])} auteur(s), "
          f"{len([r for r, _ in LIVRABLES if (ROOT / r).exists()])} livrable(s), "
          f"tests : {'OK' if res.returncode == 0 else 'ECHEC'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
