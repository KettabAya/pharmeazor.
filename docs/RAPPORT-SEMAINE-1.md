# Rapport — Semaine 1 · Partie « données structurées »

**Pharmeazor** · Projet 2, module RCR, M1 IA
Université Constantine 2 Abdelhamid Mehri — Faculté NTIC, Département IFA
Vendredi 13 novembre 2026

**Périmètre de ce rapport.** Il ne couvre que la moitié « données structurées »
du projet : collecte, nettoyage et normalisation de la nomenclature nationale.
La partie documentaire — notices, RCP, extraction des rubriques — fait l'objet
d'un travail distinct et n'est pas traitée ici.

---

## 1. Résumé

| | |
|---|---|
| Produits traités | **284** sur trois classes thérapeutiques |
| Registre analysé | **5 425** produits, **1 414** DCI distinctes |
| Sources mobilisées | **3** niveaux d'autorité, **5** versions datées |
| Interactions disponibles | **2 239**, classées en 3 niveaux ANSM |
| Désaccords datables | **13** (exigence du cahier des charges : 10) |
| Anomalies trouvées dans la source officielle | **5** |
| Tests automatisés | **159** |

**Le résultat principal n'est pas un chiffre de couverture mais une méthode :**
mesurer la distribution d'une colonne avant d'écrire la règle qui la lit, et
refuser d'inventer là où la source est ambiguë.

---

## 2. Point de départ

### Les données reçues

| Source | Nature | Volume | Rang |
|---|---|---|---|
| Nomenclature nationale (Ministère de l'Industrie pharmaceutique) | 5 classeurs Excel datés, déc. 2025 → août 2026 | 5 425 produits par version, 3 feuilles | **3 — officielle** |
| dzair-pharma.net | 11 exports JSON | 497 produits, 5 353 interactions | **1 — secondaire** |
| Thésaurus ANSM | relayé dans les exports dzair | champ `source` des interactions | **2 — institutionnelle** |
| RCP de l'ANPP | 2 liens PDF trouvés dans les exports | non encore téléchargés | **4 — officielle** |

### Les trois molécules retenues

Une par classe thérapeutique, comme le demande le périmètre du projet.

| DCI | Classe | Produits |
|---|---|---|
| PARACETAMOL | antalgique / anti-inflammatoire | 143 |
| AMOXICILLINE | antibiotique | 61 |
| AMLODIPINE | antihypertenseur | 80 |

**Limite assumée :** seul le paracétamol dispose d'exports dzair. L'amoxicilline
et l'amlodipine n'ont qu'une source — ni interactions, ni RCP. Le script le
signale à chaque exécution plutôt que de laisser croire à une couverture
complète.

### Les obstacles du format

Trois difficultés, repérées avant d'écrire la moindre ligne de traitement :

1. **L'en-tête n'est pas sur la première ligne.** Un bloc à en-tête
   ministériel précède le tableau ; les titres de colonnes sont ligne 14 dans
   les versions du registre, ligne 11 dans les fichiers par année.
2. **La feuille `Retraits` n'a pas les mêmes colonnes.** Elle omet `OBS` et
   ajoute `DATE DE RETRAIT` et `MOTIF DE RETRAIT` : toute lecture par position
   y déplacerait les laboratoires dans un champ de date, **sans erreur
   affichée**.
3. **Tout est du texte.** Dates, dosages et conditionnements sont des chaînes
   de caractères : rien n'est comparable ni calculable en l'état.

---

## 3. La méthode

Elle tient en une phrase : **mesurer avant d'écrire, et ne jamais deviner.**

### La séquence appliquée à chaque colonne

| # | Question | Outil |
|---|---|---|
| 1 | Combien de lignes, de colonnes ? | `df.shape` |
| 2 | À quoi ressemble un enregistrement ? | `df.iloc[0]` |
| 3 | Quelles colonnes sont vides, et combien ? | `df.isna().sum()` |
| 4 | Combien de valeurs distinctes ? | `df.nunique()` |
| 5 | Quelles valeurs reviennent le plus ? | `value_counts()` |
| 6 | Quelle **structure** ont les valeurs ? | remplacer les chiffres par `N` |
| 7 | Qu'est-ce qui cloche ? | contrôles de cohérence |

### L'étape 6, et pourquoi elle est décisive

La colonne `CONDITIONNEMENT` compte 1 304 valeurs distinctes — impossible à
lire une par une, et c'est pourtant dessus qu'il faut écrire une règle.

En remplaçant chaque groupe de chiffres par `N`, ces 1 304 valeurs se
regroupent en une dizaine de **formes**, classables par fréquence :

```
 2869  53,3 %   B/N
  242   4,5 %   FL/NML
  220   4,1 %   B/N ET B/N
  158   2,9 %   T/NG
   62   1,2 %   BOITE DE N
```

**Cette étape avait d'abord été sautée.** La première règle de lecture, écrite
à partir de cinq exemples observés au hasard, ne reconnaissait que `B/N` et
ratait `PILULIER/10` — présent 23 fois dans le registre — ainsi que
`BOITE DE N` (62 fois) et `B/N SACHETS` (34 fois).

L'erreur a été trouvée par une **vérification manuelle** d'un échantillon de
cinq lignes, pas par les tests : un test ne vérifie que les cas auxquels son
auteur a pensé.

### La règle qui en découle

> On ne corrige pas une anomalie de la source. On la mesure, on la documente,
> et on choisit explicitement de ne pas la deviner.

---

## 4. Ce que l'examen a révélé

Cinq anomalies, chacune établie par une mesure reproductible.

### 4.1 Deux graphies pour la même valeur réglementaire

```
LISTE I     164
Liste I       1      <-- même catégorie, autre casse
```

Pour un humain, identique. Pour un programme, deux catégories : un regroupement
en aurait produit trois au lieu de deux.

**Traitement** — normalisation en majuscules. L'opération touche la forme, pas
le sens. Résultat : 165.

### 4.2 Cent dix-huit valeurs manquantes, qui sont une information

`list_class` est vide 118 fois sur 284 — 42 %. Avant de décider quoi en faire,
il fallait savoir **pourquoi**.

| Quand c'est vide | Quand c'est rempli |
|---|---|
| PARACETAMOL — 88 | AMLODIPINE — 35, 15, 11 |
| PARACETAMOL/CAFEINE — 6 | AMOXICILLINE — 15, 12, 8 |
| autres associations de paracétamol | **PARACETAMOL/TRAMADOL — 12** |
| | **PARACETAMOL/CODEINE — 11** |

116 des 118 vides concernent le paracétamol. La répartition n'est pas aléatoire.

Le paracétamol seul se vend sans ordonnance : il n'est sur aucune liste. Les
antibiotiques et antihypertenseurs en exigent une. **Et le même paracétamol,
associé à la codéine ou au tramadol — des opiacés — redevient listé.**

Cette dernière observation est décisive : la colonne suit le **statut
réglementaire**, pas la qualité de la saisie.

**Traitement** — rien n'est rempli. Le vide signifie « hors liste ».

### 4.3 Un numéro d'enregistrement pour deux produits

```
ligne Excel 3113 : n° 3099 | 003/13 G 181/13/24 | CLAMOXYPEN ENFANTS
ligne Excel 3114 : n° 3100 | 003/13 G 181/13/24 | CLAMOXYPEN NOURRISSONS
```

Toutes les autres colonnes sont identiques. Seul le nom de marque diffère :
l'un pour les enfants, l'autre pour les nourrissons.

Le numéro d'enregistrement est l'identifiant attribué par l'État. Une citation
de la forme « produit n° 003/13 G 181/13/24 » ne permet plus de savoir duquel
on parle — ce qui touche directement la règle d'or du projet.

**Vérification que l'anomalie vient de la source** : le doublon figure dans le
classeur du ministère avant tout traitement, et le ministère lui-même numérote
ces lignes 3099 et 3100 — deux enregistrements distincts portant le même
numéro.

**Traitement** — rien n'est supprimé, les deux produits existent. L'identifiant
devient le couple `numéro + marque`.

### 4.4 Une date de fin antérieure à la date de début

```
APAP CAFEINE BEKER : enregistré le 2023-03-29, validité expirée le 2023-03-21
```

Huit jours **avant**. Une validité ne peut pas se terminer avant d'avoir
commencé.

**Traitement** — signalé, non corrigé : on ignore laquelle des deux dates est
fausse, et en choisir une serait inventer.

Ce contrôle n'était possible qu'après conversion des colonnes en vraies dates.
Sur du texte, la comparaison n'aurait eu aucun sens.

### 4.5 Vingt-sept écritures pour trois molécules

```
AMOXICILLINE TRIHYDRATEE EXPRIME EN AMOXICILLINE
AMOXICILLINE TRIHYDRATE  EXPRIME EN AMOXICILLINE
AMOXICILLINE TRIHYDRATE E EXPRIME EN AMOXICILLINE ANHYDRE     <-- espace parasite
AMOXICILLINE TRIHYDRAT2E/ACIDE CLAVULANIQUE POTASSIQUE        <-- « 2 » au lieu de « É »
ATROVASTATINE CALCIQUE TRIHYDRATEE                            <-- ATORVASTATINE
```

**Traitement** — découpage de la colonne, détaillé au § 5.3.

---

## 5. Les traitements appliqués

Tout le code est dans `src/pharmeazor/`, testé, et exécutable par une seule
commande.

### 5.1 Lecture des classeurs — `collect/nomenclature.py`

Deux décisions structurent ce module :

**L'en-tête est cherché, jamais codé en dur.** La première ligne portant au
moins 15 cellules non vides est l'en-tête — les lignes du bloc ministériel n'en
ont qu'une. La fonction renvoie 14 sur les versions du registre et 11 sur les
fichiers par année, sans qu'on le lui dise.

**Chaque cellule est lue par titre de colonne, jamais par position.** La
feuille `Retraits` n'a donc besoin d'aucun cas particulier : ses colonnes
supplémentaires se rattachent simplement à des champs supplémentaires.

### 5.2 Dosages et conditionnements — `normalize/dosage.py`

**Dosages.** Le module sépare la valeur de l'unité, en traitant :

| Cas | Exemple | Résultat |
|---|---|---|
| simple | `500MG` | 500 + mg |
| virgule décimale | `37,5MG` | 37.5 + mg |
| espace | `500 MG` | 500 + mg |
| association | `325MG/37,5MG` | 325 mg + 37,5 mg |
| astérisque de bas de page | `875MG*/125MG*` | 875 mg + 125 mg |
| sans unité | `0,03` | 0.03, unité vide |
| illisible | `n` | **non lu** |

**Aucune conversion d'unité n'est faite.** Décider que `1G` vaut `1000MG` est
un jugement pharmaceutique que le système n'a pas le droit de porter seul.

**Conditionnements.** La règle a été élargie **après mesure** :

| | couverture |
|---|---|
| règle initiale (`B/N` seul) | 53,1 % |
| règle élargie | **56,1 %** — +159 produits |

Elle accepte désormais les autres contenants dénombrables (`BOITE DE N`,
`PILULIER/N`, `PLAQUETTE`) et un mot d'unité facultatif (`B/30 SACHETS`).

Ce qui reste non lu l'est à juste titre : `T/15G` est un poids, `FL/5ML` un
volume, et `B/30 ET B/90` porte deux tailles de boîte entre lesquelles choisir
serait inventer. Le `$` final de l'expression régulière est ce qui garantit ce
refus.

### 5.3 Découpage de la DCI — `normalize/substance.py`

Le registre mélange trois informations dans un seul champ :

```
"AMOXICILLINE TRIHYDRATEE EXPRIME EN AMOXICILLINE/ACIDE CLAVULANIQUE"
   substance de base : AMOXICILLINE
   forme saline      : TRIHYDRATEE
   associée à        : ACIDE CLAVULANIQUE
```

Mesure préalable sur les 1 414 DCI distinctes :

| motif | cas | part |
|---|---|---|
| `/` (association ou sel) | 273 | 19 % |
| `EXPRIME EN` | 181 | 13 % |
| parenthèses | 121 | 9 % |
| `SOUS FORME` | 73 | 5 % |

**Résultat sur le registre complet :**

```
1 405 / 1 414  DCI analysées sans ambiguïté
        9      signalées incertaines plutôt que devinées
      268      associations repérées
      426      formes salines extraites
1 237          substances distinctes (contre 1 414 écritures)
```

**La garantie la plus importante, vérifiée par un test :** une association ne
se confond jamais avec la substance seule. Rapprocher `PARACETAMOL` et
`PARACETAMOL/CODEINE` ferait disparaître un opiacé d'une recherche
d'équivalents.

Les neuf cas incertains — parenthèses ouvrant sur « OU » (un synonyme, pas une
forme saline), ou deux présentations décrites dans une même cellule — ressortent
marqués, avec leur texte d'origine intact.

### 5.4 Réconciliation — `reconcile/crosscheck.py` et `comparer_versions.py`

**Première tentative : nomenclature contre dzair-pharma.**

```
173 produits communs, 865 comparaisons de champs
  1 désaccord — 99,9 % d'accord
```

Deux sources indépendantes ne s'accordent jamais à ce point. Vérification
faite, chaque enregistrement dzair porte `"Version source": "Aout 2026"` :
**le site republie la nomenclature officielle.** Ce n'est pas une source
indépendante pour les données produit ; sa valeur ajoutée réside dans les
interactions ANSM, absentes du registre.

**Seconde approche : les cinq versions datées du registre.**

```
13 désaccords datables  (exigence : 10)
   9  conditionnement     BOITE DE 16 -> B/16
   2  laboratoire         LAM -> LABORATOIRE ALGERIEN DU MEDICAMENT
   2  date de validité    2023-12-27 -> 2026-01-07  (renouvellement)
 + 6 produits ajoutés, 4 retirés
```

Ces désaccords ont un avantage décisif : **ils sont datables.** On sait entre
quelles deux publications le registre a changé d'avis.

Le script ne tranche pas seul : chaque ligne porte les deux versions, les deux
valeurs, et rappelle qu'un écart peut venir d'un renouvellement légitime.

### 5.5 Provenance — `schemas.py`

`Provenance` est un champ **obligatoire** : source, URL, niveau d'autorité, date
de collecte, langue, pays. Une donnée sans provenance ne peut pas exister dans
le modèle.

`Citation` refuse à la construction toute citation dont le texte n'apparaît pas
dans le passage cité.

**Note sur les interactions.** Elles portent `"source": "ANSM"` — contenu
institutionnel (rang 2), obtenu via un relais non officiel (rang 1). Les deux
sont enregistrés et **la plus basse des deux autorités gouverne** : un relais
peut introduire une erreur que l'original n'avait pas. C'est implémenté dans
`effective_authority()`.

---

## 6. Résultats chiffrés

### Table produit

| | |
|---|---|
| Produits | 284 — 143 antalgiques, 61 antibiotiques, 80 antihypertenseurs |
| Dosages exploitables | **283 / 284** (99,6 %) |
| Conditionnements exploitables | **207 / 284** (73 %) |
| Groupes d'équivalents | **46**, couvrant **242** produits |
| Entrées du dictionnaire de noms | **1 136** |
| Associations détectées | 139 |
| DCI signalées incertaines | 2 |

### Interactions disponibles

| Niveau ANSM | Nombre |
|---|---|
| Contre-indication | 171 |
| Association déconseillée | 1 166 |
| Précaution d'emploi | 902 |
| **Total** | **2 239** |

### Fichiers produits

| Fichier | Lignes |
|---|---|
| `drugs_semaine1.csv` | 284 |
| `name_index.csv` | 1 136 |
| `equivalents_semaine1.csv` | 242 |
| `interactions_semaine1.csv` | 105 |
| `desaccords_versions.csv` | 13 |
| `documents_a_collecter.csv` | 18 |

### Qualité du code

```
159 tests automatisés, tous verts
ruff  : aucune erreur
 33   commits
```

---

## 7. Correspondance avec le cahier des charges

| Exigence | État | Preuve |
|---|---|---|
| Au moins 3 sources, dont une officielle | ✅ | nomenclature (3), ANSM relayé (2), dzair (1) |
| Provenance conservée par document | ✅ | `Provenance` obligatoire dans `schemas.py` |
| Collecte rejouable sans doublons | ✅ | `build_week1.py` |
| Conditions d'utilisation consignées **avant** collecte | ✅ | `assert_collectable()` refuse tant que le relevé est vide |
| Relier nom commercial, DCI, code, variantes | ✅ | 1 136 entrées |
| Retrouver les équivalents | ✅ | 46 groupes |
| Cas ambigus signalés, non tranchés | ✅ | `Ambiguity`, testé |
| **Au moins 10 désaccords réels annotés** | ✅ | **13** |
| Contrôle des chiffres mot pour mot | ✅ | `number_guard.py`, 12 tests |
| Jamais d'information sans source | ✅ | imposé par le modèle de données |
| Tableau d'évaluation sur 40 noms | ⬜ | **reste à produire** |
| Rubriques des notices | ⬜ | partie du binôme |

### Les trois règles du projet

1. **Le système ne prescrit ni ne diagnostique.** `equivalents_of()` refuse les
   questions hors périmètre.
2. **Rien ne s'affiche sans source.** Imposé par le type, pas par convention.
3. **Les ordonnances de test sont fictives.** Aucune donnée patient n'est
   utilisée.

---

## 8. Correspondance avec le cours

Le chapitre 01 déroule huit difficultés. Le travail de cette semaine en couvre
plusieurs, avec le vocabulaire du cours.

| Concept du cours | Où il est dans le projet |
|---|---|
| **Entity Extraction** | lecture des colonnes DCI, marque, code — `collect/nomenclature.py` |
| **Entity Linking** | découpage de la DCI en base / sel / associations — `normalize/substance.py` |
| **Knowledge Graph** | produit → DCI → code → équivalents — `name_index.csv` |
| **Information Retrieval** | BM25 écrit sans dépendance — `retrieve/bm25.py` |
| **Raisonnement symbolique** | règle d'équivalence, rang des sources — `catalogue.py`, `conflicts.py` |
| **Knowledge Updating** | cinq versions datées comparées — `comparer_versions.py` |
| **Grounding** | provenance et citations — `schemas.py` |

### Le processus du chapitre 01

Le cours énonce la chaîne attendue : **Retrouver → Comparer → Vérifier → Citer.**

| Étape | Implémentation |
|---|---|
| Retrouver | `bm25.py`, `catalogue.find_by_name()` |
| Comparer | `crosscheck.py`, `comparer_versions.py` |
| Vérifier | `number_guard.py` |
| Citer | `Provenance.cite()`, `Citation` |

### L'exemple du cours, vécu sur ce projet

La huitième difficulté est illustrée en cours par deux documents contradictoires
— un guide de six mois contre une note de version d'hier — et la question :
lequel vaut aujourd'hui ?

Nous l'avons rencontrée pour de bon. Le PDF du cahier des charges annonçait un
modèle Gemini ; une annonce ultérieure de l'enseignant impose un autre modèle.
Le dépôt a suivi la version périmée pendant quelques heures, jusqu'à ce que la
source la plus récente soit retrouvée.

C'est précisément le *Knowledge Updating* du cours : une source doit porter sa
date, et la plus récente l'emporte.

---

## 9. Ce qui reste à faire

### Priorité immédiate

| # | Tâche | Pour qui | Durée |
|---|---|---|---|
| 1 | Clé Groq dans `.env`, lancer `tester_llm_seul.py` | Aya | 5 min |
| 2 | Remplir la grille d'annotation des erreurs du modèle | Aya | 45 min |
| 3 | Télécharger les RCP de l'ANPP et noter leur provenance | binôme | — |

### Ensuite

| # | Tâche | Durée |
|---|---|---|
| 4 | Tableau d'évaluation sur 40 noms — **exigé** | 2 h |
| 5 | Exports dzair pour l'amoxicilline et l'amlodipine | — |
| 6 | Les 13 conditionnements encore récupérables | 30 min |

### Questions à poser à l'enseignant

1. dzair-pharma compte-t-il comme une source distincte de la nomenclature,
   sachant qu'il la republie ?
2. Le modèle à utiliser est-il `openai/gpt-oss-120b` ou le modèle de secours
   `openai/gpt-oss-20b` ?

---

## 10. Reproduire et partager

### Tout reconstruire

```bash
git clone https://github.com/KettabAya/pharmeazor.git
cd pharmeazor
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.lock.txt
pip install -e . --no-deps
```

Les fichiers bruts ne sont pas dans le dépôt — leurs conditions de
redistribution n'ont pas été vérifiées. Les placer dans
`data/raw/nomenclature/` et `data/raw/dzair/`, puis :

```bash
python scripts/build_week1.py          # table, dictionnaire, équivalents, interactions
python scripts/comparer_versions.py    # les 13 désaccords datables
python scripts/verifier_echantillon.py # échantillon à vérifier à la main
python scripts/tester_llm_seul.py      # le modèle seul sur la question-test
pytest                                 # 159 tests
```

### Documents du dépôt

| Fichier | Contenu |
|---|---|
| `docs/MISSION.md` | mission, question-test, protocole |
| `docs/JOURNAL-TRAITEMENT.md` | chaque anomalie, sa mesure, sa décision |
| `docs/ARCHITECTURE.md` | les choix techniques et leur justification |
| `docs/DATA_SOURCES.md` | registre des sources et conformité |
| `docs/SEMAINE-1.md` | répartition du travail |
| `explorations/` | notebook d'exploration |

---

## Conclusion

La couche données est en place, mesurée et testée. Cinq anomalies ont été
trouvées dans un document officiel de l'État, chacune établie par une
vérification reproductible, et **aucune n'a été corrigée en silence**.

Le choix méthodologique qui gouverne tout le reste : une base qui dit « je ne
sais pas » là où elle ne sait pas vaut mieux qu'une base lisse et fausse. C'est
aussi la dernière règle de travail du module :

> « Honnêteté : un système qui dit "je ne sais pas" vaut mieux qu'un système qui
> invente. »
