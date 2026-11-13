# Explorations

Notebooks d'exploration : on y **comprend** les données avant d'écrire la
moindre règle de nettoyage.

| Notebook | Ce qu'il montre |
|---|---|
| `01_explorer_la_nomenclature.ipynb` | la séquence complète : complétude, cardinalité, distribution, formes, anomalies |

## Lancer

```
.venv\Scripts\activate
jupyter notebook
```

Puis ouvrir le notebook et exécuter les cellules avec Maj + Entrée.

## Règle

Un notebook sert à comprendre, pas à produire. Il ne se rejoue pas tout seul et
ne prouve rien. Ce qui est décidé ici part ensuite dans `src/pharmeazor/`, sous
forme de fonctions testées.
