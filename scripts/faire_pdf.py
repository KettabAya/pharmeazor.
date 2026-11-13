"""Assembler les documents du projet en un seul fichier imprimable.

Produit un HTML autonome, mis en page pour l'impression. Pour obtenir le PDF :
ouvrir le fichier dans un navigateur, puis Ctrl+P et « Enregistrer au format
PDF ». Cette voie evite d'installer LaTeX ou wkhtmltopdf, et donne un rendu
identique a ce que le navigateur affiche.

Usage::

    python scripts/faire_pdf.py
    python scripts/faire_pdf.py --sortie mon_rapport.html
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Ordre de lecture : le rapport d'abord, les annexes ensuite.
DOCUMENTS = [
    ("docs/RAPPORT-SEMAINE-1.md", "Rapport — Semaine 1"),
    ("docs/MISSION.md", "Annexe A — Mission et question-test"),
    ("docs/JOURNAL-TRAITEMENT.md", "Annexe B — Journal du traitement"),
    ("docs/ARCHITECTURE.md", "Annexe C — Architecture"),
    ("docs/DATA_SOURCES.md", "Annexe D — Sources et conformité"),
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Segoe UI", Calibri, Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.55; color: #1a1a1a; max-width: 190mm; margin: 0 auto; }
h1 { font-size: 20pt; border-bottom: 2.5px solid #2c6e9b; padding-bottom: 6px;
     margin-top: 1.2em; color: #11405c; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
h2 { font-size: 14pt; color: #11405c; margin-top: 1.5em;
     border-bottom: 1px solid #d0d7de; padding-bottom: 3px; }
h3 { font-size: 11.5pt; color: #2c6e9b; margin-top: 1.2em; }
table { border-collapse: collapse; width: 100%; margin: 0.9em 0; font-size: 9.5pt;
        page-break-inside: avoid; }
th { background: #eef4f8; text-align: left; font-weight: 600; }
th, td { border: 1px solid #c8d1d9; padding: 5px 8px; vertical-align: top; }
tr:nth-child(even) td { background: #fafbfc; }
code { background: #f3f5f7; padding: 1px 4px; border-radius: 3px;
       font-family: Consolas, "Courier New", monospace; font-size: 9pt; }
pre { background: #f6f8fa; border: 1px solid #d8dee4; border-left: 3px solid #2c6e9b;
      padding: 9px 12px; overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 8.8pt; line-height: 1.4; }
blockquote { border-left: 3px solid #c8d1d9; margin-left: 0; padding-left: 14px;
             color: #495057; font-style: italic; }
hr { border: none; border-top: 1px solid #d0d7de; margin: 1.6em 0; }
a { color: #2c6e9b; text-decoration: none; }
.couverture { text-align: center; padding: 55mm 0 0 0; page-break-after: always; }
.couverture h1 { font-size: 30pt; border: none; page-break-before: avoid; margin: 0; }
.couverture .sous { font-size: 13pt; color: #495057; margin-top: 10px; }
.couverture .etab { font-size: 10.5pt; color: #6a737d; margin-top: 40px; line-height: 1.9; }
.sommaire { page-break-after: always; }
.sommaire ol { font-size: 11pt; line-height: 2; }
@media print { a { color: #1a1a1a; } }
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Assembler les documents en un HTML imprimable.")
    parser.add_argument("--sortie", default="RAPPORT-PHARMEAZOR.html")
    args = parser.parse_args()

    try:
        import markdown
    except ImportError:
        print("Installez le convertisseur :  pip install markdown")
        return 1

    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"])

    presents = [(c, t) for c, t in DOCUMENTS if (ROOT / c).exists()]
    if not presents:
        print("Aucun document trouve dans docs/.")
        return 1

    aujourdhui = dt.date.today()
    morceaux = [f"""<div class="couverture">
<h1>Pharmeazor</h1>
<div class="sous">Base de connaissances médicamenteuse<br>et assistant à preuves</div>
<div class="sous" style="margin-top:28px;font-size:11pt">Rapport — Semaine 1</div>
<div class="etab">
Projet 2 — Module RCR, M1 IA<br>
Université Constantine 2 Abdelhamid Mehri<br>
Faculté des Nouvelles Technologies de l'Information et de la Communication<br>
Département Informatique Fondamentale et ses Applications<br><br>
Encadrant : Pr. BOURAMOUL<br>
{aujourdhui:%d/%m/%Y}
</div></div>"""]

    sommaire = ["<div class='sommaire'><h1 style='page-break-before:avoid'>Sommaire</h1><ol>"]
    for _, titre in presents:
        sommaire.append(f"<li>{titre}</li>")
    sommaire.append("</ol></div>")
    morceaux.append("".join(sommaire))

    for chemin, _titre in presents:
        texte = (ROOT / chemin).read_text(encoding="utf-8")
        md.reset()
        corps = md.convert(texte)
        morceaux.append(f"<section>{corps}</section>")
        print(f"  inclus : {chemin}")

    html = (
        "<!doctype html>\n<html lang='fr'>\n<head>\n<meta charset='utf-8'>\n"
        "<title>Pharmeazor — Rapport Semaine 1</title>\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n" + "\n".join(morceaux) + "\n</body>\n</html>\n"
    )

    sortie = ROOT / args.sortie
    sortie.write_text(html, encoding="utf-8")
    taille = sortie.stat().st_size / 1024

    print(f"\n  ecrit : {sortie.name}  ({taille:.0f} Ko)")
    print("\n  Pour le PDF :")
    print("    1. double-cliquer sur le fichier (il s'ouvre dans le navigateur)")
    print("    2. Ctrl+P")
    print("    3. Destination : « Enregistrer au format PDF »")
    print("    4. cocher « Graphiques d'arriere-plan » pour garder les couleurs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
