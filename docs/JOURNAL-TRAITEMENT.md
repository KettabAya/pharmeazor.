# Journal du traitement des données

Ce que nous avons trouvé en examinant les sources, avec la mesure qui l'établit
et la décision prise. Chaque entrée est reproductible : la commande figure à
côté du résultat.

Ce document se remplit au fur et à mesure. Il sert de matière première au
rapport : le cahier des charges demande des chiffres, pas des impressions.

**Source principale examinée** : `data/reference/drugs_semaine1.csv` — 284
produits, 18 colonnes, extraits de la nomenclature nationale de juin 2026 pour
le paracétamol, l'amoxicilline et l'amlodipine.

---

## Résumé des anomalies

| # | Ce qui a été trouvé | Mesure | Décision | État |
|---|---|---|---|---|
| 1 | Deux graphies pour la même valeur réglementaire | `LISTE I` × 164, `Liste I` × 1 | normalisation en majuscules | ✅ corrigé |
| 2 | Valeurs manquantes dans `list_class` | 118 / 284 (42 %) | conservées — le vide est une information | ✅ expliqué |
| 3 | Numéro d'enregistrement partagé par deux produits | 1 cas | identifiant composite, rien supprimé | ✅ documenté |
| 4 | Orthographes multiples de la même substance | 27 graphies pour 3 molécules | à traiter (Entity Linking) | ⬜ ouvert |
| 5 | Dosages illisibles | 1 / 284 | laissé vide, non deviné | ✅ documenté |
| 6 | Conditionnements non lus | 85 / 284 (30 %) | 13 récupérables, 72 réellement ambigus | ⬜ partiel |
| 7 | Date de fin antérieure à la date de début | 1 cas | signalé, non corrigé | ✅ documenté |
| 8 | Source secondaire non indépendante | 99,9 % d'accord sur 865 comparaisons | réconciliation déplacée | ✅ documenté |

---

## 1. Deux graphies pour la même valeur réglementaire

```python
df["list_class"].value_counts(dropna=False)
```

```
LISTE I     164
NaN         118
LISTE II      1
Liste I       1      <-- même valeur, autre casse
```

Pour un humain, `Liste I` et `LISTE I` sont identiques. Pour un programme, ce
sont deux catégories distinctes : un regroupement en aurait produit trois au
lieu de deux.

**Décision — corrigé.** Normalisation en majuscules, espaces de bord retirés.

```python
df["list_class"] = df["list_class"].str.strip().str.upper()
```

Résultat : `LISTE I` passe à 165. L'opération ne touche pas au sens, seulement à
la forme : les deux graphies désignent la même catégorie réglementaire.

---

## 2. Valeurs manquantes dans `list_class`

```python
df.isna().sum()
```

118 cases vides sur 284, soit 42 %. Toutes les autres colonnes sont pleines.

Avant de décider quoi en faire, il fallait savoir **pourquoi** elles sont vides.
Trois causes possibles : information non collectée (erreur), information non
applicable (le vide signifie quelque chose), ou perte au traitement (notre bug).

```python
df[df["list_class"].isna()]["inn"].value_counts()
df[df["list_class"].notna()]["inn"].value_counts()
```

| Quand c'est vide | Quand c'est rempli |
|---|---|
| PARACETAMOL — 88 | AMLODIPINE… — 35, 15, 11 |
| PARACETAMOL/CAFEINE — 6 | AMOXICILLINE… — 15, 12, 8 |
| autres associations de paracétamol | PARACETAMOL/TRAMADOL — 12 |
| | PARACETAMOL/CODEINE — 11 |

Sur les 118 vides, **116 concernent le paracétamol** ou une association à base
de paracétamol. La répartition n'est pas aléatoire.

Le paracétamol seul se vend sans ordonnance : il n'est sur aucune liste. Les
antibiotiques et les antihypertenseurs en exigent une. Et le même paracétamol,
**associé à la codéine ou au tramadol** — des opiacés —, redevient listé.

Cette dernière observation est décisive : la colonne suit le statut
réglementaire du produit, pas la qualité de la saisie.

**Décision — rien n'est rempli.** Le vide signifie « hors liste ». Écrire
`LISTE I` dans ces 118 cases inventerait une contrainte réglementaire
inexistante.

---

## 3. Numéro d'enregistrement partagé par deux produits

```python
print(df.duplicated().sum())                      # 0
print(df["registration_no"].duplicated().sum())   # 1
df[df["registration_no"].duplicated(keep=False)]
```

Aucune ligne n'est recopiée à l'identique. Mais un numéro d'enregistrement
désigne deux produits :

| | ligne 228 | ligne 229 |
|---|---|---|
| n° d'enregistrement | `003/13 G 181/13/24` | `003/13 G 181/13/24` |
| DCI, forme, dosage, conditionnement, laboratoire | identiques | identiques |
| **nom de marque** | CLAMOXYPEN **ENFANTS** | CLAMOXYPEN **NOURRISSONS** |

Le numéro d'enregistrement est l'identifiant attribué par l'État. Il devrait
désigner un seul produit. Ici, une citation de la forme « produit
n° 003/13 G 181/13/24 » ne permet plus de savoir duquel on parle — ce qui
touche directement la règle d'or du projet, puisque toute réponse doit citer sa
source de façon vérifiable.

**Vérification — l'anomalie vient bien de la source, pas de notre traitement.**
Recherche du numéro dans le classeur d'origine :

```
feuille « Nomenclature Juin 2026 »
  ligne 3113 : n° séquentiel 3099 | 003/13 G 181/13/24 | CLAMOXYPEN ENFANTS
  ligne 3114 : n° séquentiel 3100 | 003/13 G 181/13/24 | CLAMOXYPEN NOURISSONS
```

Deux points l'établissent : le doublon est présent dans le fichier du ministère
avant toute transformation de notre part, et le ministère lui-même numérote ces
lignes 3099 et 3100 — deux enregistrements distincts dans sa propre
numérotation, portant pourtant le même numéro d'enregistrement.

**Décision — rien n'est supprimé.** Les deux produits existent réellement. Nous
utilisons le couple `numéro + nom de marque` comme identifiant, et nous
signalons l'incohérence sans la corriger : décider quel numéro aurait dû être
attribué n'est pas de notre ressort.

---

## 4. Orthographes multiples de la même substance

Relevé dans la colonne `inn` :

```
AMOXICILLINE TRIHYDRATEE EXPRIME EN AMOXICILLINE
AMOXICILLINE TRIHYDRATE  EXPRIME EN AMOXICILLINE
AMOXICILLINE TRIHYDRATE E EXPRIME EN AMOXICILLINE ANHYDRE     <-- espace en trop
AMOXICILLINE TRIHYDRAT2E/ACIDE CLAVULANIQUE POTASSIQUE        <-- « 2 » au lieu de « É »
ATROVASTATINE CALCIQUE TRIHYDRATEE                            <-- ATORVASTATINE
```

**27 graphies distinctes** pour trois molécules : fautes de frappe, espaces
surnuméraires, formulations variables.

C'est le problème que le chapitre 01 du cours nomme **Entity Linking** —
rattacher chaque désignation à la bonne entité de référence.

**État — ouvert.** Traité par `src/pharmeazor/normalize/names.py`, à évaluer
chiffres à l'appui sur un échantillon d'au moins 40 saisies.

---

## 5. Dosages illisibles

Sur 284 produits, **283 dosages ont été lus**. Le dernier vaut `n` dans la
source : ce n'est pas un dosage.

**Décision — laissé non lu.** Le parseur ne devine pas. Un dosage inventé dans
un projet sur le médicament est la seule faute irrattrapable.

---

## 6. Conditionnements non lus

```
199 / 284 lus   (70 %)
 85 / 284 non lus (30 %)
```

Les 85 ne sont pas tous des échecs. Trois catégories :

| Forme | Nombre | Lisible ? |
|---|---|---|
| `BOITE DE N`, `B/N SACHETS`, `PILULIER/N` | ~13 | ✅ le nombre est présent, la règle ne le reconnaît pas |
| `B/N ET B/N` | 21 | ❌ deux tailles de boîte — réellement ambigu |
| `FL/N ML`, `T/N G` | ~50 | ❌ un volume ou un poids, pas un nombre d'unités |

Mesuré sur l'ensemble de la nomenclature (5 379 produits), `B/N` ne couvre que
**53 %** des cas.

**Leçon de méthode.** La règle de lecture avait d'abord été écrite à partir de
cinq exemples observés au hasard, et ratait `PILULIER/10`. La bonne démarche est
inverse : mesurer la distribution des formes avant d'écrire la règle. En
remplaçant chaque nombre par `N`, les 1 304 valeurs distinctes se regroupent en
une dizaine de formes classables par fréquence.

**État — partiel.** Les formes réellement ambiguës doivent rester non lues.

---

## 7. Date de fin antérieure à la date de début

```
APAP CAFEINE BEKER : début 2023-03-29, fin 2023-03-21
```

Une validité ne peut pas se terminer avant d'avoir commencé.

**Décision — signalé, non corrigé.** Nous ne savons pas laquelle des deux dates
est fausse ; en choisir une serait inventer.

---

## 8. La source secondaire n'est pas indépendante

Jointure des deux sources sur le numéro d'enregistrement, puis comparaison champ
par champ :

```
173 produits présents dans les deux sources
865 comparaisons de champs
  1 désaccord  (FLC COMPTE GOUTTE 05ML / FL COMPTE GOUTTE 05ML)
99,9 % d'accord
```

Deux sources indépendantes ne s'accordent jamais à ce point. Vérification faite,
chaque enregistrement dzair porte `"Version source": "Aout 2026"` et
`"Année de nomenclature": "2026"` : **le site republie la nomenclature
officielle**.

**Conséquence.** dzair-pharma n'est pas une source indépendante pour les données
produit ; sa valeur ajoutée réside dans les interactions ANSM, absentes du
registre officiel. La brique « réconciliation » sera donc démontrée entre les
**cinq versions datées de la nomenclature** (décembre 2025 → août 2026), qui
fournissent de vrais désaccords datables.

**Note de provenance.** Les interactions portent `"source": "ANSM"` — contenu
d'origine institutionnelle (rang 2), obtenu via un relais non officiel (rang 1).
Les deux sont enregistrés et **la plus basse des deux autorités gouverne** : un
relais peut introduire une erreur que l'original n'avait pas.

---

## Questions encore ouvertes

- Que faire des 13 conditionnements lisibles mais non pris en charge ?
- L'évaluation de l'Entity Linking sur 40 saisies reste à produire.
- dzair-pharma compte-t-il comme une source distincte de la nomenclature,
  sachant qu'il la republie ? — à poser à l'enseignant.
