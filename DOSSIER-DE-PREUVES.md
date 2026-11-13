# Dossier de preuves — Pharmeazor

Généré le **13/11/2026 à 22:55** depuis le dépôt lui-même.
Aucune valeur n'est saisie à la main : tout est relevé à l'exécution.

- Dépôt : `https://github.com/KettabAya/pharmeazor..git`
- Branche : `main`
- Commit : `a9a615c`
- Total : **50 commits**, 91 fichiers suivis

---

## 1. Contribution par personne

Relevée dans l'historique Git. Un commit porte un auteur, une date et une
empreinte : ces chiffres ne sont pas déclarés, ils sont constatés.

| Auteur | Commits | Lignes ajoutées | Lignes retirées | Première | Dernière |
|---|---:|---:|---:|---|---|
| **Kettab Aya** | 34 | +16,276 | −3,367 | 2026-11-10 | 2026-11-13 |
| **Ryma Ait** | 10 | +105 | −53 | 2026-11-13 | 2026-11-13 |
| **aya** | 6 | +149 | −6 | 2026-11-13 | 2026-11-13 |

### Fichiers touchés par chaque personne

**Kettab Aya** — 88 fichiers

- `.env.example`
- `.gitattributes`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/task.md`
- `.github/pull_request_template.md`
- `.github/workflows/ci.yml`
- `.gitignore`
- `CONTRIBUTING.md`
- `LICENSE`
- `Makefile`
- `README.md`
- `data/interim/.gitkeep`
- `data/processed/.gitkeep`
- `data/raw/.gitkeep`
- *… et 74 autres*

**Ryma Ait** — 4 fichiers

- `data/reference/source_registry.yaml`
- `docs/DATA_SOURCES.md`
- `src/pharmeazor/extract/sections.py`
- `tests/fixtures/amlodipine_sections_sample.txt`

**aya** — 5 fichiers

- `.gitignore`
- `data/processed/cache.json`
- `data/processed/call_counter.json`
- `scripts/run_baseline.py`
- `src/pharmeazor/answer/llm_client.py`

---

## 2. Livrables, avec leur empreinte

L'empreinte SHA-256 permet de vérifier qu'un fichier est bien celui-ci et
qu'il n'a pas été modifié depuis.

| Fichier | Contenu | Lignes | Empreinte |
|---|---|---:|---|
| `data/reference/drugs_semaine1.csv` | table produit nettoyée | 284 | `308b1a6381bb7fa3` |
| `data/reference/name_index.csv` | dictionnaire des noms | 1136 | `155c4160ffb412f1` |
| `data/reference/equivalents_semaine1.csv` | groupes d'équivalents | 242 | `eb659e61a1b49c6a` |
| `data/reference/interactions_semaine1.csv` | interactions avec niveau ANSM | 87 | `55180b7af231b717` |
| `data/reference/desaccords_versions.csv` | désaccords entre versions datées | 13 | `076d777a71ca7667` |
| `data/reference/source_registry.yaml` | registre des sources et conformité | — | `7b28c65de1c2ef6c` |
| `data/reference/documents_a_collecter.csv` | liste de collecte des notices | 18 | `e620d7233cd39f8a` |
| `eval/llm_alone_test.json` | trace du test du modèle seul | — | `d17e6983bdb19967` |
| `preprocessing.ipynb` | notebook de traitement | — | `63f77957d94bf329` |

---

## 3. Suite de tests

```
........................................................................ [ 45%]
........................................................................ [ 90%]
...............                                                          [100%]
```

Code de sortie : **0** — tous les tests passent.

---

## 4. Reproduire chaque chiffre

| Commande | Ce qu'elle établit |
|---|---|
| `git log --format='%an %ad %s' --date=short` | qui a contribué, et quand |
| `python scripts/build_week1.py` | régénère table, dictionnaire, équivalents, interactions |
| `python scripts/comparer_versions.py` | les désaccords entre versions du registre |
| `python scripts/verifier_echantillon.py` | tire 5 produits à vérifier à la main |
| `pytest` | la suite de tests |

---

## 5. Les vingt derniers commits

```
a9a615c  2026-11-13  14an  chore: sorties du notebook apres execution complete
b81ccbf  2026-11-13  14an  feat(eval): trace du test du modele seul, par Aya
727e0f3  2026-11-13  14an  merge: travail de Ryma — extraction des rubriques et conformite des sources
c8dea4e  2026-11-13  14an  docs: register ANSM public medicines database
b387306  2026-11-13  14an  test: add amlodipine section extraction fixture
008c648  2026-11-13  14an  Support long leaflet headings and document amoxicillin coverage
426fa7d  2026-11-13  14an  Document paracetamol notice extraction coverage
686d5ba  2026-11-13  14an  style: nom de variable explicite dans completer_notebook
3f41653  2026-11-13  14an  style: corrections ruff sur les deux nouveaux scripts
4c43d1f  2026-11-13  14an  docs: notebook complete, rapport imprimable, perimetre clarifie
4afc6f0  2026-11-13  14an  docs: rapport complet de la semaine 1
9c86cb1  2026-11-13  14an  style: correction ruff sur le harnais de test
1c4cbda  2026-11-13  14an  feat(scripts): le test du modele seul pose la question trois fois
e6d85b4  2026-11-13  14an  feat(normalize): decoupage de la DCI et regle de conditionnement elargie
b03e890  2026-11-13  14an  Merge pull request #2 from KettabAya/feat/baseline
c2c779a  2026-11-13  14an  fix: normalisation portee dans le pipeline, et une seule version par table
774ca8e  2026-11-13  14an  feat: mission, question-test et harnais du test du modele seul
9f01cf2  2026-11-13  14an  style: zip(strict=False) explicite dans comparer_versions
f1266d0  2026-11-13  14an  feat(scripts): comparaison des versions successives de la nomenclature
ae42050  2026-11-13  14an  chore(llm): l'equipe retient openai/gpt-oss-20b
```

---

*Pour régénérer ce dossier : `python scripts/dossier_preuves.py`*
