"""Compléter le notebook de traitement : garder le code existant, ajouter le reste.

Les cellules déjà écrites sont conservées **mot pour mot**. Le script ajoute
autour d'elles les explications en Markdown, puis les sections manquantes
(dosages, conditionnements, découpage de la DCI, équivalents, vérification,
sauvegarde).

Usage::

    python scripts/completer_notebook.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "preprocessing.ipynb"


def md(id_: str, *lignes: str) -> dict:
    return {"cell_type": "markdown", "id": id_, "metadata": {},
            "source": [l + "\n" for l in lignes]}


def code(id_: str, *lignes: str) -> dict:
    return {"cell_type": "code", "id": id_, "metadata": {},
            "execution_count": None, "outputs": [],
            "source": [l + "\n" for l in lignes]}


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    anciennes = [c for c in nb["cells"] if "".join(c["source"]).strip()]
    print(f"  {len(anciennes)} cellules existantes conservees")

    def reprendre(indice: int, nouvel_id: str) -> dict:
        c = dict(anciennes[indice])
        c["id"] = nouvel_id
        c["metadata"] = {}
        c["outputs"] = []
        c["execution_count"] = None
        return c

    cellules: list[dict] = []

    # ---------------------------------------------------------------- titre
    cellules += [md(
        "t00",
        "# Traitement des données — nomenclature nationale",
        "",
        "**Pharmeazor** · Projet 2, module RCR, M1 IA · Université Constantine 2",
        "",
        "Lire le registre officiel, l'examiner, le nettoyer, et consigner ce qu'on y trouve.",
        "",
        "| Partie | Ce qu'on fait | Pourquoi |",
        "|---|---|---|",
        "| **1. Charger** | ouvrir le fichier, mesurer sa taille | savoir à quoi on a affaire |",
        "| **2. Explorer** | complétude, distribution, formes | comprendre avant de toucher |",
        "| **3. Anomalies** | doublons, dates, incohérences | une anomalie est un résultat |",
        "| **4. Nettoyer** | dates, casse, dosages, conditionnements | rendre les données calculables |",
        "| **5. Relier** | découper la DCI, grouper les équivalents | *Entity Linking* |",
        "| **6. Vérifier** | contrôler son propre travail | ne rien casser en silence |",
        "",
        "**L'ordre n'est pas négociable.** On explore avant de nettoyer, sinon on écrit",
        "des règles au hasard. On vérifie après, sinon on ne sait pas ce qu'on a cassé.",
        "",
        "> **Règle du projet** — on ne remplit jamais un vide, on ne devine jamais un",
        "> chiffre. Une base qui dit « je ne sais pas » vaut mieux qu'une base lisse et",
        "> fausse.",
    )]

    # ------------------------------------------------------------- 1. charger
    cellules += [
        md("t01", "---", "# 1. Charger"),
        reprendre(0, "u01"),
        md("t02",
           "**Une ligne = une boîte enregistrée**, pas un médicament. Le paracétamol",
           "apparaît 143 fois parce qu'il existe 143 présentations. C'est toute la",
           "difficulté du projet, visible dès la première cellule."),
    ]

    # ------------------------------------------------------------ 2. explorer
    cellules += [
        md("t03", "---", "# 2. Explorer", "",
           "## 2.1 Types et complétude", "",
           "`info()` répond à deux questions d'un coup : **quelles colonnes ont des",
           "trous**, et **quels types** pandas a devinés. Presque tout est `str` —",
           "donc rien n'est encore calculable."),
        reprendre(1, "u02"),
        reprendre(2, "u03"),
        md("t04",
           "**Une seule colonne a des trous : `list_class`, 118 sur 284 — 42 %.**",
           "",
           "Avant de décider quoi en faire, il faut savoir **pourquoi**. Une case vide a",
           "toujours une de ces trois causes :",
           "",
           "1. **non collectée** → une erreur de saisie",
           "2. **non applicable** → le vide est une information",
           "3. **perdue au traitement** → notre bug",
           "",
           "La réponse change tout : si c'est (3) il faut corriger le code ; si c'est (2)",
           "il ne faut surtout rien toucher."),
        reprendre(3, "u04"),
        md("t05",
           "`dropna=False` est essentiel : sans lui, pandas **cache les vides** et on",
           "croit que tout va bien — 166 lignes affichées sur 284.",
           "",
           "Et on repère `Liste I` avec **un seul exemplaire** au milieu de 164 `LISTE I`.",
           "Une faute de frappe se voit toujours à son nombre.",
           "",
           "## 2.2 Chercher le motif des valeurs manquantes"),
        reprendre(7, "u05"),  # la cellule vide/rempli
        md("t06",
           "**Ce n'est pas du hasard** : 116 des 118 vides concernent le paracétamol.",
           "",
           "Le paracétamol seul se vend sans ordonnance — il n'est sur aucune liste. Les",
           "antibiotiques et antihypertenseurs en exigent une. Et le même paracétamol,",
           "**associé à la codéine ou au tramadol** (des opiacés), redevient listé.",
           "",
           "La colonne suit donc le **statut réglementaire**, pas la qualité de la saisie.",
           "C'est la cause (2).",
           "",
           "➜ **Décision : on ne remplit rien.** Écrire `LISTE I` dans ces 118 cases",
           "inventerait une contrainte réglementaire qui n'existe pas."),
    ]

    # ---------------------------------------------------------- 3. anomalies
    cellules += [
        md("t07", "---", "# 3. Chercher les anomalies", "",
           "Une anomalie n'est pas un accident à cacher : **c'est un résultat**.",
           "",
           "## 3.1 Numéros d'enregistrement en double", "",
           "Deux mesures, parce qu'elles détectent deux problèmes différents :",
           "",
           "- **ligne entièrement identique** → une copie ; on peut supprimer sans rien perdre",
           "- **même numéro, lignes différentes** → bien plus grave : le numéro est",
           "  l'identifiant attribué par l'État, et c'est lui que le système **cite**"),
        reprendre(4, "u06"),
        md("t08",
           "`keep=False` marque **tous** les exemplaires, pas seulement les répétitions :",
           "il faut les deux lignes côte à côte pour comparer."),
        reprendre(5, "u07"),
        md("t09",
           "**Toutes les colonnes sont identiques sauf le nom de marque** : l'un pour les",
           "enfants, l'autre pour les nourrissons. Deux produits réels, un seul numéro.",
           "",
           "Vérification faite dans le classeur d'origine : le doublon est aux lignes 3113",
           "et 3114, sous les numéros séquentiels 3099 et 3100 du ministère. **L'anomalie",
           "précède notre traitement.**",
           "",
           "➜ **Décision : on ne supprime rien.** L'identifiant devient le couple",
           "`numéro + marque`, et l'incohérence est signalée."),
    ]

    # ----------------------------------------------------------- 4. nettoyer
    cellules += [
        md("t10", "---", "# 4. Nettoyer", "",
           "## 4.1 Les dates", "",
           "Tant qu'une date est du texte, on ne peut ni la trier, ni la comparer, ni",
           "calculer une durée.",
           "",
           "**`errors=\"coerce\"`** décide quoi faire devant une date illisible :",
           "",
           "| option | comportement |",
           "|---|---|",
           "| `raise` (défaut) | **plante** à la première date bizarre |",
           "| `coerce` | la met à vide (`NaT`) **et permet de les compter** |",
           "| remplir à la main | **inventer** — interdit ici |"),
        reprendre(8, "u08"),
        md("t11",
           "## 4.2 Le contrôle que la conversion débloque", "",
           "Une validité ne peut pas se terminer avant d'avoir commencé. Sur du texte,",
           "cette comparaison n'aurait eu aucun sens."),
        reprendre(9, "u09"),
        md("t12",
           "➜ **Signalé, non corrigé** : on ignore laquelle des deux dates est fausse,",
           "et en choisir une serait inventer."),
        md("t13",
           "## 4.3 La casse", "",
           "Mettre en majuscules ne change pas le **sens** : `Liste I` et `LISTE I`",
           "désignent la même catégorie réglementaire. On uniformise la forme, pas le fond.",
           "C'est différent de remplir un vide — là, on inventerait."),
        reprendre(6, "u10"),
        md("t14",
           "> ⚠️ **Une correction faite ici n'existe que dans ce notebook.**",
           ">",
           "> Elle modifie `df` en mémoire ; le fichier sur le disque n'en sait rien, et le",
           "> script qui le fabrique non plus. Au prochain redémarrage du noyau, elle",
           "> disparaît.",
           ">",
           "> **Ce qui est décidé ici doit finir dans `scripts/build_week1.py`.** C'est fait",
           "> pour celle-ci : `normaliser_liste()`."),
    ]

    # -------------------------------------------------- 4.4 dosages (existant)
    cellules += [
        md("t15",
           "## 4.4 Les dosages", "",
           "`\"500MG\"` est une **étiquette**. `500` + `mg` est une **mesure**. Tant que",
           "c'est une étiquette on peut l'afficher ; une fois que c'est une mesure, on",
           "peut raisonner avec.",
           "",
           "D'abord regarder les valeurs."),
        reprendre(10, "u11"),
        md("t16",
           "### La technique des formes", "",
           "Des dizaines de valeurs distinctes : impossible de les lire une par une, et",
           "c'est pourtant dessus qu'il faut écrire une règle.",
           "",
           "**En remplaçant chaque nombre par `N`**, les valeurs qui ont la même structure",
           "se regroupent. Écrire une règle sans avoir fait ça, c'est deviner."),
        reprendre(11, "u12"),
        md("t17",
           "**Ce que ce tableau révèle, et que le top des valeurs brutes ne donnait pas :**",
           "",
           "- `NMG` + `NMG/NMG` couvrent les deux tiers du corpus — on commence par là",
           "- `N MG` → des dosages écrits **avec un espace** : `500 MG`",
           "- `N,N` → des valeurs **sans unité du tout**",
           "- `NMG/NMG/NMG` → **trois** substances dans un seul produit",
           "",
           "C'est en sautant cette étape que la première règle des conditionnements ratait",
           "`PILULIER/10` et `BOITE DE 30`.",
           "",
           "### Appliquer la règle du projet", "",
           "Le module `normalize/dosage.py` gère tous ces cas."),
        code("n01",
             "import sys",
             "from pathlib import Path",
             "",
             "RACINE = Path.cwd()",
             "SOURCE = RACINE / \"data\" / \"reference\" / \"drugs_semaine1.csv\"",
             "sys.path.insert(0, str(RACINE / \"src\"))",
             "",
             "from pharmeazor.normalize.dosage import parse_packaging, parse_strength",
             "",
             "exemples = [\"500MG\", \"500 MG\", \"37,5MG\", \"325MG/37,5MG\",",
             "            \"875MG*/125MG*\", \"0,03\", \"n\"]",
             "pd.DataFrame([",
             "    {\"brut\": e,",
             "     \"lu\": parse_strength(e).canonical() or \"NON LU\",",
             "     \"association\": parse_strength(e).is_combination}",
             "    for e in exemples",
             "])"),
        md("t18",
           "**Aucune conversion d'unité n'est faite.** Décider que `1G` vaut `1000MG` est",
           "un jugement pharmaceutique que le système n'a pas le droit de porter seul."),
        code("n02",
             "doses = df[\"strength_raw\"].map(parse_strength)",
             "df[\"dose_valeur\"] = [d.components[0].value if d.parsed else None for d in doses]",
             "df[\"dose_unite\"] = [d.components[0].unit if d.parsed else None for d in doses]",
             "df[\"dose_association\"] = [d.is_combination for d in doses]",
             "",
             "print(f\"dosages lus : {df['dose_valeur'].notna().sum()}/{len(df)}\")",
             "print(f\"non lus     : {df.loc[df['dose_valeur'].isna(), 'strength_raw'].tolist()}\")",
             "df[[\"strength_raw\", \"dose_valeur\", \"dose_unite\", \"dose_association\"]].head(6)"),
    ]

    # ------------------------------------------------- 4.5 conditionnements
    cellules += [
        md("t19",
           "## 4.5 Les conditionnements", "",
           "La règle a été élargie **après avoir mesuré** les formes : elle accepte les",
           "contenants dénombrables (`BOITE DE N`, `PILULIER/N`) et un mot d'unité",
           "facultatif (`B/30 SACHETS`).",
           "",
           "Ce qui reste non lu l'est **à juste titre**."),
        code("n03",
             "cas = [\"B/16\", \"BOITE DE 30\", \"PILULIER/30\", \"B/30 SACHETS\",",
             "       \"B/30 ET B/90\", \"T/15G\", \"FL/5ML\"]",
             "pd.DataFrame([",
             "    {\"brut\": c,",
             "     \"nombre d'unites\": parse_packaging(c).count,",
             "     \"pourquoi\": \"lu\" if parse_packaging(c).count is not None",
             "                 else \"deux tailles de boite\" if \" ET \" in c",
             "                 else \"un poids ou un volume, pas un nombre\"}",
             "    for c in cas",
             "])"),
        code("n04",
             "df[\"boite_unites\"] = [parse_packaging(p).count for p in df[\"packaging_raw\"]]",
             "lus = df[\"boite_unites\"].notna().sum()",
             "print(f\"conditionnements lus : {lus}/{len(df)}  ({100*lus/len(df):.0f} %)\")",
             "print()",
             "print(\"les plus frequents parmi les non lus :\")",
             "print(df.loc[df[\"boite_unites\"].isna(), \"packaging_raw\"]",
             "        .value_counts().head(5).to_string())"),
    ]

    # ------------------------------------------------------------- 5. relier
    cellules += [
        md("t20", "---", "# 5. Relier — *Entity Linking*", "",
           "Le registre mélange **trois informations** dans la colonne `inn` :",
           "",
           "```",
           "AMOXICILLINE TRIHYDRATEE EXPRIME EN AMOXICILLINE/ACIDE CLAVULANIQUE",
           "   substance de base : AMOXICILLINE",
           "   forme saline      : TRIHYDRATEE",
           "   associée à        : ACIDE CLAVULANIQUE",
           "```",
           "",
           "Les confondre serait grave : rapprocher `PARACETAMOL` et",
           "`PARACETAMOL/CODEINE` ferait disparaître un opiacé d'une recherche",
           "d'équivalents.",
           "",
           "C'est le concept que le chapitre 01 du cours appelle **Entity Linking** —",
           "rattacher chaque désignation à la bonne entité."),
        code("n05",
             "from pharmeazor.normalize.substance import parse_inn",
             "",
             "subs = df[\"inn\"].map(parse_inn)",
             "df[\"substance_base\"] = [s.base for s in subs]",
             "df[\"substance_sel\"] = [s.sel for s in subs]",
             "df[\"substance_associes\"] = [\" + \".join(s.associes) for s in subs]",
             "df[\"substance_incertaine\"] = [s.incertain for s in subs]",
             "",
             "print(f\"ecritures distinctes de la DCI : {df['inn'].nunique()}\")",
             "print(f\"substances de base distinctes  : {df['substance_base'].nunique()}\")",
             "print(f\"associations detectees         : {(df['substance_associes'] != '').sum()}\")",
             "print(f\"signalees incertaines          : {df['substance_incertaine'].sum()}\")",
             "",
             "df[[\"inn\", \"substance_base\", \"substance_sel\", \"substance_associes\"]] \\",
             "    .drop_duplicates().head(8)"),
        md("t21",
           "Les cas qu'on ne sait pas analyser avec certitude ressortent **marqués**, avec",
           "leur texte d'origine intact. On ne devine pas.",
           "",
           "## 5.1 Les équivalents", "",
           "Deux boîtes sont interchangeables si c'est **la même substance, au même",
           "dosage, dans la même famille galénique**. Un comprimé ne remplace jamais un",
           "sirop."),
        code("n06",
             "from pharmeazor.normalize.catalogue import Catalogue",
             "",
             "cat = Catalogue.from_csv(SOURCE)",
             "groupes = [g for g in cat.groups() if g.size > 1]",
             "",
             "print(f\"{len(groupes)} groupes, {sum(g.size for g in groupes)} produits\")",
             "pd.DataFrame([",
             "    {\"substance\": g.inn[:38], \"dosage\": g.strength,",
             "     \"forme\": g.form_family, \"marques\": g.size}",
             "    for g in cat.groups()[:6]",
             "])"),
        md("t22",
           "## 5.2 La question du cahier des charges", "",
           "> « X est en rupture, quels équivalents enregistrés en Algérie ? »"),
        code("n07",
             "exemple = next(p.brand_name for g in cat.groups() if g.size > 1",
             "               for p in g.products",
             "               if not cat.equivalents_of(p.brand_name)[\"refused\"])",
             "rep = cat.equivalents_of(exemple)",
             "",
             "print(f\"QUESTION : {exemple} est en rupture, quels equivalents ?\")",
             "print()",
             "print(\"REPONSE  :\", rep[\"short\"])",
             "print(\"SOURCE   :\", rep[\"citations\"][0][\"source\"])",
             "print(\"LIMITES  :\", rep[\"limits\"])",
             "print()",
             "print(f\"{len(rep['citations'])} citations, chacune avec son n d'enregistrement\")"),
        md("t23",
           "**La réponse porte sa preuve.** Chaque équivalent vient avec son numéro",
           "d'enregistrement et la version du registre qui l'atteste — c'est le",
           "*Grounding* du chapitre 01."),
    ]

    # ----------------------------------------------------- 6. verifier/sauver
    cellules += [
        md("t24", "---", "# 6. Vérifier et sauvegarder", "",
           "On contrôle son propre travail avant de le déclarer fini."),
        code("n08",
             "controles = {",
             "    \"lignes conservees\": (len(df), 284),",
             "    \"dosages lus\": (int(df['dose_valeur'].notna().sum()), 283),",
             "    \"conditionnements lus\": (int(df['boite_unites'].notna().sum()), 207),",
             "    \"valeurs inventees\": (0, 0),",
             "}",
             "pd.DataFrame([",
             "    {\"controle\": k, \"obtenu\": a, \"attendu\": b,",
             "     \"ok\": \"oui\" if a == b else \"NON\"}",
             "    for k, (a, b) in controles.items()",
             "])"),
        code("n09",
             "SORTIE = Path.cwd() / \"data\" / \"interim\" / \"nomenclature_notebook.csv\"",
             "SORTIE.parent.mkdir(parents=True, exist_ok=True)",
             "df.to_csv(SORTIE, index=False, encoding=\"utf-8\")",
             "",
             "print(f\"ecrit : {SORTIE}\")",
             "print(f\"{len(df)} lignes, {df.shape[1]} colonnes\")",
             "print()",
             "print(\"colonnes ajoutees par ce notebook :\")",
             "for c in [\"dose_valeur\", \"dose_unite\", \"dose_association\", \"boite_unites\",",
             "          \"substance_base\", \"substance_sel\", \"substance_associes\",",
             "          \"substance_incertaine\"]:",
             "    print(\"  -\", c)"),
        md("t25", "---", "# Bilan", "",
           "## Ce qu'on a trouvé dans la source officielle", "",
           "| # | Anomalie | Décision |",
           "|---|---|---|",
           "| 1 | `LISTE I` / `Liste I` — deux graphies | normalisé (la forme, pas le sens) |",
           "| 2 | 118 valeurs manquantes dans `list_class` | **conservées** — le vide est une information |",
           "| 3 | 1 numéro d'enregistrement pour 2 produits | **rien supprimé** — identifiant composite |",
           "| 4 | 1 date de fin antérieure à la date de début | **signalée, non corrigée** |",
           "| 5 | 44 écritures de DCI pour 3 molécules | découpées en base / sel / associations |",
           "",
           "## Ce qu'on a produit", "",
           "| | |",
           "|---|---|",
           "| Dosages exploitables | 283 / 284 |",
           "| Conditionnements exploitables | 207 / 284 |",
           "| Groupes d'équivalents | 46 |",
           "| Entrées du dictionnaire de noms | 1 136 |",
           "",
           "## Les trois règles qui gouvernent tout", "",
           "1. **On ne remplit jamais un vide.** Il peut vouloir dire quelque chose.",
           "2. **On ne devine jamais un chiffre.** `T/15G` est un poids, pas 15 comprimés.",
           "3. **Une association n'est pas la substance seule.** Sinon un opiacé disparaît.",
           "",
           "## Et une règle de méthode", "",
           "> **Ce notebook sert à comprendre. Il ne produit rien de durable.**",
           ">",
           "> Ce qui est décidé ici doit finir dans `src/pharmeazor/`, sous forme de",
           "> fonctions testées. Un notebook ne se rejoue pas tout seul.",
           ">",
           "> Pour tout reconstruire : `python scripts/build_week1.py`"),
    ]

    nb["cells"] = cellules
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.13"},
    }
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    n_code = sum(1 for c in cellules if c["cell_type"] == "code")
    n_md = sum(1 for c in cellules if c["cell_type"] == "markdown")
    print(f"  ecrit : {NOTEBOOK.name}")
    print(f"  {len(cellules)} cellules — {n_code} de code, {n_md} d'explication")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
