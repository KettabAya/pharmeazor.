"""Découper la colonne DCI en substance de base, forme saline et associations.

C'est l'**Entity Linking** du chapitre 01 : rattacher chaque désignation à la
bonne entité. Le registre écrit une même substance de plusieurs façons, et
mélange dans un seul champ trois informations différentes :

* la **substance de base** — ce que le pharmacien appelle le médicament
* la **forme saline** — trihydratée, bésilate, chlorhydrate : la même substance
  sous une forme chimique précise, sans effet sur l'identité du produit
* les **associations** — d'autres substances actives dans le même comprimé

Les confondre serait grave. Rapprocher ``PARACETAMOL`` et
``PARACETAMOL/CODEINE`` ferait disparaître un opiacé d'une recherche
d'équivalents.

Mesure sur les 1 414 DCI distinctes du registre d'août 2026 :

===========================  =====  ====
motif                        cas    part
===========================  =====  ====
``/`` (association ou sel)     273   19 %
``EXPRIME EN``                 181   13 %
parenthèses                    121    9 %
``SOUS FORME``                  73    5 %
``ET``                          13    1 %
===========================  =====  ====

Le reste est une substance simple, écrite telle quelle.

Règle de prudence : ce module **ne devine pas**. Une écriture qu'il ne sait pas
analyser avec certitude ressort marquée ``incertain``, avec son texte d'origine
intact, pour revue humaine.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache

__all__ = ["Substance", "parse_inn", "normaliser_substance"]

# "X <sel> EXPRIME EN Y" / "EXPRIMEE EN" / "EXPRIMES EN" : Y est la base.
_EXPRIME_EN = re.compile(r"\bEXPRIM\w*\s+EN\s+(?P<base>.+)$", re.I)

# "X SOUS FORME DE Y" / "X SOUS FORME Y" : X est la base, Y la forme saline.
_SOUS_FORME = re.compile(r"^(?P<base>.+?)\s*/?\s*\bSOUS\s+FORME\s+(?:DE\s+)?(?P<sel>.+)$", re.I)

# "X (Y)" : Y est la base, SAUF si la parenthese s'ouvre sur "OU" (synonyme).
_PARENTHESE = re.compile(r"^(?P<avant>[^(]+?)\s*\((?P<dedans>[^)]+)\)\s*$")

# Mots qui designent une forme saline ou un hydrate, jamais une substance.
_FORMES_SALINES = (
    "TRIHYDRATE", "TRIHYDRATEE", "DIHYDRATE", "MONOHYDRATE", "ANHYDRE",
    "BESILATE", "BESYLATE", "CHLORHYDRATE", "SULFATE", "MALEATE", "TARTRATE",
    "CITRATE", "ACETATE", "PHOSPHATE", "SODIQUE", "POTASSIQUE", "CALCIQUE",
    "MAGNESIQUE", "HEMIHYDRATE", "FUMARATE", "SUCCINATE", "MESILATE",
    "BROMHYDRATE", "NITRATE", "LACTATE", "GLUCONATE", "STEARATE", "ARGININE",
)


def _sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c))


def normaliser_substance(nom: str | None) -> str:
    """Forme canonique d'un nom de substance, pour comparer deux écritures.

    Majuscules, sans accents, sans astérisques de bas de page, espaces réduits.
    Ne retire aucun mot : c'est une normalisation de **forme**, pas de sens.

    >>> normaliser_substance("  Amoxicilline**  trihydratée ")
    'AMOXICILLINE TRIHYDRATEE'
    """
    texte = _sans_accents(str(nom or "")).upper()
    texte = texte.replace("*", " ")
    texte = re.sub(r"[^\w\s/()-]", " ", texte)
    return " ".join(texte.split())


@dataclass(frozen=True)
class Substance:
    """Une DCI décomposée."""

    raw: str
    base: str = ""
    sel: str = ""
    associes: tuple[str, ...] = field(default=())
    incertain: bool = False
    motif: str = ""          # pourquoi incertain, ou quelle règle a servi

    @property
    def est_association(self) -> bool:
        return bool(self.associes)

    @property
    def toutes_substances(self) -> tuple[str, ...]:
        """Base et associées, dans l'ordre où elles apparaissent."""
        return ((self.base,) if self.base else ()) + self.associes

    def cle(self) -> str:
        """Clé de regroupement : les substances, pas la forme saline.

        Deux produits de même base et mêmes associées sont la même substance,
        que l'un soit trihydraté et l'autre non.
        """
        return "+".join(normaliser_substance(s) for s in self.toutes_substances)

    def __str__(self) -> str:
        return self.cle() or self.raw


def _extraire_base_et_sel(morceau: str) -> tuple[str, str, bool, str]:
    """Analyser un morceau : renvoie (base, sel, incertain, motif)."""
    texte = " ".join(morceau.replace("*", " ").split())
    if not texte:
        return "", "", False, ""

    # "<sel> EXPRIME EN <base>" : la base est explicitement nommee apres.
    m = _EXPRIME_EN.search(texte)
    if m:
        base = m.group("base").strip()
        sel = texte[: m.start()].strip()
        # Le sel contient souvent la base : "AMOXICILLINE TRIHYDRATEE".
        sel_mots = [w for w in sel.split()
                    if _sans_accents(w).upper() in _FORMES_SALINES]
        return base, " ".join(sel_mots), False, "exprime_en"

    # "<base> SOUS FORME DE <sel>"
    m = _SOUS_FORME.match(texte)
    if m:
        return m.group("base").strip(), m.group("sel").strip(), False, "sous_forme"

    # "<avant> (<dedans>)"
    m = _PARENTHESE.match(texte)
    if m:
        dedans = m.group("dedans").strip()
        avant = m.group("avant").strip()
        # "(OU autre nom)" est un synonyme, pas la base : on ne tranche pas.
        if re.match(r"^OU\b", dedans, re.I):
            return avant, "", True, "synonyme_entre_parentheses"
        sel_mots = [w for w in avant.split()
                    if _sans_accents(w).upper() in _FORMES_SALINES]
        return dedans, " ".join(sel_mots), False, "parenthese"

    # Substance simple, eventuellement suivie d'une forme saline.
    mots = texte.split()
    sel_mots = [w for w in mots if _sans_accents(w).upper() in _FORMES_SALINES]
    if sel_mots:
        base = " ".join(w for w in mots if w not in sel_mots)
        return base.strip(), " ".join(sel_mots), False, "sel_accole"

    return texte, "", False, "simple"


@lru_cache(maxsize=4096)
def parse_inn(valeur: str | None) -> Substance:
    """Découper une DCI en base, forme saline et substances associées.

    Les associations sont séparées par ``/``. Un morceau qui commence par
    ``SOUS FORME`` n'est pas une association mais la précision saline du
    morceau précédent.

    >>> parse_inn("PARACETAMOL").base
    'PARACETAMOL'
    >>> parse_inn("AMLODIPINE BESILATE EXPRIME EN AMLODIPINE").base
    'AMLODIPINE'
    >>> parse_inn("PARACETAMOL/CAFEINE").associes
    ('CAFEINE',)
    >>> parse_inn("ALFACALCIDOL (OU 1 ALPHA-HYDROXY)").incertain
    True
    """
    brut = str(valeur or "").strip()
    if not brut:
        return Substance(raw="")

    # " ET " relie deux presentations distinctes dans une seule cellule
    # (comprime de jour / comprime de nuit) : on ne sait pas les separer
    # proprement, donc on le signale au lieu de choisir.
    if re.search(r"\sET\s", brut, re.I) and "/" in brut:
        return Substance(raw=brut, base=brut, incertain=True, motif="deux_presentations")

    morceaux = [m.strip() for m in brut.split("/") if m.strip()]
    bases: list[str] = []
    sels: list[str] = []
    incertain = False
    motifs: list[str] = []

    for i, morceau in enumerate(morceaux):
        # "SOUS FORME ..." seul : precision du morceau precedent, pas une association.
        if re.match(r"^\s*SOUS\s+FORME\b", morceau, re.I) and bases:
            sels.append(re.sub(r"^\s*SOUS\s+FORME\s+(?:DE\s+)?", "", morceau, flags=re.I).strip())
            continue
        base, sel, inc, motif = _extraire_base_et_sel(morceau)
        if base:
            bases.append(base)
        if sel and i == 0:
            sels.append(sel)
        incertain = incertain or inc
        motifs.append(motif)

    if not bases:
        return Substance(raw=brut, base=brut, incertain=True, motif="non_analysable")

    return Substance(
        raw=brut,
        base=bases[0],
        sel=" ".join(dict.fromkeys(s for s in sels if s)),
        associes=tuple(bases[1:]),
        incertain=incertain,
        motif="+".join(dict.fromkeys(motifs)),
    )
