# Semaine 2 — recherche par le sens

**Échéance : vendredi 20 novembre 2026.**

> Découper les documents, calculer les embeddings, monter la base vectorielle,
> comparer mots-clés et recherche sémantique.

C'est la **3ᵉ et la 4ᵉ difficulté** du chapitre 01 : les mots de la question ne
sont pas ceux des documents, et il faut donc représenter le *sens* plutôt que
les mots.

---

## Ce qui est déjà en place

| | |
|---|---|
| **BM25** — la recherche par mots-clés | ✅ `retrieve/bm25.py`, 10 tests |
| **Le type `Passage`** — texte + provenance + rubrique + positions | ✅ `schemas.py` |
| **4 documents collectés** — 2 RCP officiels, 2 notices | ✅ par Ryma |
| **Le découpage en passages** | ❌ rien ne fabrique encore de `Passage` |
| **Les embeddings** | ❌ `sentence-transformers` pas installé |
| **La base vectorielle** | ❌ à monter |

BM25 n'est pas un brouillon : c'est **la référence que la recherche sémantique
devra battre**, chiffres à l'appui. Le cahier des charges demande explicitement
de comparer au moins deux approches.

---

## À régler dès lundi — sinon rien ne démarre

### 1. Partager les documents

`data/raw/notices/` est ignoré par git. Les documents de Ryma n'existent que sur
sa machine : personne d'autre ne peut découper, indexer ni comparer.

**Deux options, à trancher ensemble :**

- **Partage hors dépôt** — clé USB ou Drive, chacun les place dans
  `data/raw/notices/`. Le dépôt reste propre, mais l'enseignant ne peut pas
  reproduire la chaîne.
- **Versionner le texte extrait** (`.txt`, pas les PDF) — tout devient
  reproductible, mais c'est une republication. Le relevé de conformité dit que
  les conditions de réutilisation de l'ANPP **ne sont pas confirmées**.

➜ **Question à poser à l'enseignant :** peut-on verser au dépôt le texte extrait
des RCP de l'ANPP, ou faut-il s'en tenir au corpus de dépannage qu'il a prévu ?

### 2. Les documents manquants

| Molécule | Documents | État |
|---|---|---|
| Paracétamol | RCP ANPP + notice Pharm'Net | ✅ 2 |
| Amoxicilline | RCP Pharm'Net + notice ANSM | ✅ 2 |
| **Amlodipine** | — | ❌ **aucun** |

Sans document sur l'amlodipine, une classe thérapeutique sur trois reste muette.

### 3. Le modèle d'embeddings

Le modèle imposé (Groq, `openai/gpt-oss`) ne produit pas d'embeddings. Le cahier
des charges l'a prévu : *« embeddings ouverts exécutés localement ou modèle
d'embeddings gratuit du même service »*.

➜ **E5 ou BGE-M3 en local**, via `sentence-transformers`. Tous deux sont
multilingues, ce qui compte : le corpus est en français.

```bash
pip install -e ".[dense]"
```

---

## Répartition

### Vous — découpage et jeu d'évaluation

| # | Tâche | Terminé quand |
|---|---|---|
| 1 | `retrieve/chunking.py` : document → `Passage`, avec provenance et rubrique conservées | un RCP produit des passages portant chacun sa source et sa rubrique |
| 2 | Choisir la taille de passage et le recouvrement, **après mesure** | un tableau compare 2 ou 3 tailles sur le même jeu de questions |
| 3 | Écrire 15 questions avec leur passage de référence | `eval/questions.yaml` passe de 8 à 23 entrées annotées |

La tâche 3 est la plus importante : **sans questions annotées, la comparaison
entre BM25 et les vecteurs n'est pas mesurable.** C'est elle qui transforme
« les vecteurs ont l'air meilleurs » en un chiffre.

Et elle avance en même temps l'exigence des 30 questions du jeu de test.

### Ryma — documents et extraction

| # | Tâche |
|---|---|
| 1 | Collecter au moins un RCP d'amlodipine |
| 2 | Extraire le texte des documents restants |
| 3 | Mesurer la couverture des rubriques sur l'ensemble |
| 4 | Compléter le relevé de conformité pour les sources ajoutées |

### Aya — embeddings et base vectorielle

| # | Tâche |
|---|---|
| 1 | Installer et comparer E5 et BGE-M3 sur quelques phrases du corpus |
| 2 | `retrieve/embeddings.py` : passages → vecteurs, **avec cache** |
| 3 | `retrieve/vectorstore.py` : index FAISS ou Chroma, recherche par similarité |
| 4 | Compter le temps de calcul et la taille de l'index |

Le cache est le même principe que pour le modèle de langage : recalculer les
embeddings à chaque exécution coûte des minutes pour rien.

### Ensemble — jeudi soir

La comparaison, qui est **le livrable de la semaine** :

| Méthode | Rappel @1 | Rappel @5 | Rappel @10 | Latence médiane |
|---|---|---|---|---|
| BM25 | | | | |
| Vecteurs | | | | |
| Hybride | | | | |

Avec, en dessous, **trois questions où BM25 gagne et trois où les vecteurs
gagnent** — c'est là que se trouve la compréhension, pas dans la moyenne.

---

## Ce qu'on cherche à démontrer

Le chapitre 01 annonce le résultat attendu :

> « Les mots utilisés dans la requête ne sont pas nécessairement ceux présents
> dans les documents pertinents. »

Concrètement, sur votre corpus : un pharmacien demandera
*« peut-on le prendre enceinte ? »* quand le RCP écrit *« grossesse et
allaitement »*. BM25 ne trouvera rien — aucun mot commun. La recherche
sémantique devrait trouver.

**Mais attention au revers**, que le cours mentionne aussi : la recherche par le
sens *« confond parfois deux médicaments proches »*. Sur un corpus où
`AMOXICILLINE` et `AMOXICILLINE/ACIDE CLAVULANIQUE` coexistent, c'est un risque
réel — et le signaler serait un meilleur résultat que de l'ignorer.

---

## Attention à ne pas se répéter

La semaine dernière, deux personnes ont écrit le même script le même soir.

**Avant de coder : dire dans le groupe quel fichier on ouvre.** Les trois lots
ci-dessus touchent des fichiers différents — `chunking.py`, `embeddings.py`,
`vectorstore.py` — donc aucun conflit n'est possible si chacun s'en tient au
sien.

Et un seul dépôt : **`github.com/KettabAya/pharmeazor.`**, avec le point.
