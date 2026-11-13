# Mission et question-test

Livrable de la **semaine 1** : fixer la mission, rédiger la question-test,
puis tester le modèle seul dessus et noter ses erreurs.

---

## La mission

Un pharmacien d'officine, au comptoir, doit vérifier une information avant de
la donner. L'information existe — mais elle est dispersée entre la nomenclature
officielle, les RCP de l'ANPP, le thésaurus des interactions, et des sites
professionnels qui ne concordent pas toujours.

**Pharmeazor retrouve cette information et la restitue en citant sa source.**

Trois règles, non négociables :

1. Rien ne s'affiche sans source.
2. Tout chiffre affiché doit se retrouver mot pour mot dans le passage cité.
3. Le système ne prescrit ni ne diagnostique : il aide à retrouver et à
   contrôler. La décision reste celle du pharmacien.

Périmètre de départ : paracétamol, amoxicilline, amlodipine — une molécule par
classe thérapeutique.

---

## La question-test

Elle est volontairement **longue et à plusieurs étapes** : une question simple
ne révélerait pas ce qui manque au modèle seul.

> « Un patient de 68 ans sous anticoagulant oral au long cours présente une
> ordonnance mentionnant **CLAMOXYPEN 1 g**. Le produit est en rupture chez moi.
>
> Quels équivalents enregistrés en Algérie puis-je délivrer à ce dosage, et de
> quels laboratoires ? Y a-t-il une interaction à signaler entre cette
> substance et son anticoagulant ? Si oui, à quel niveau de gravité selon le
> thésaurus, et quelle conduite tenir ?
>
> Indiquez pour chaque élément la source exacte et sa date. »

### Ce qu'elle exige, étape par étape

| # | Étape | Où se trouve la réponse |
|---|---|---|
| 1 | Reconnaître que CLAMOXYPEN est une marque | dictionnaire des noms |
| 2 | Remonter à la DCI : amoxicilline / acide clavulanique | nomenclature |
| 3 | Trouver les équivalents enregistrés au même dosage et à la même forme | groupes d'équivalents |
| 4 | Nommer les laboratoires | nomenclature |
| 5 | Chercher l'interaction amoxicilline × anticoagulants oraux | interactions ANSM |
| 6 | Donner le **niveau de gravité** | champ `gravite` |
| 7 | Donner la **conduite à tenir** | champ `conduite_a_tenir` |
| 8 | **Citer chaque source avec sa date** | provenance |

Huit étapes, trois sources différentes. Aucun modèle de langage ne peut y
répondre de mémoire — et c'est exactement ce qu'on veut démontrer.

### Ce qui rend une réponse fausse

- un équivalent qui **n'existe pas** dans la nomenclature algérienne
- un dosage inventé
- un niveau de gravité adouci, ou l'absence de niveau
- une source citée sans date, ou une source inventée
- une recommandation de prescription — hors périmètre

---

## Le test du modèle seul

```bash
python scripts/tester_llm_seul.py
```

Le modèle reçoit la question **sans corpus, sans recherche, sans aucun
document**. On note ensuite ce qu'il a inventé.

Résultat et annotation : [`LLM-SEUL-RESULTAT.md`](LLM-SEUL-RESULTAT.md).

### Pourquoi faire ce test

Le chapitre 01 du cours ouvre sur deux difficultés : le modèle répond avec
assurance, et il se trompe. Tout ce qui suit — recherche, embeddings, graphe,
règles, citations — existe pour corriger ça.

**On ne peut pas démontrer qu'on a résolu un problème qu'on n'a pas d'abord
mesuré.** Cette trace est le point de comparaison de tout le projet : en
semaine 6, la même question posée au système complet devra donner une réponse
sourcée là où le modèle seul improvisait.
