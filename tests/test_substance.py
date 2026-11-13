"""Découpage de la DCI — l'Entity Linking du projet.

Les cas testés viennent tous du registre réel, pas d'exemples inventés.
"""

import pytest

from pharmeazor.normalize.substance import (
    Substance,
    normaliser_substance,
    parse_inn,
)


class TestNormalisation:
    def test_accents_et_casse(self):
        assert normaliser_substance("Amoxicilline trihydratée") == "AMOXICILLINE TRIHYDRATEE"

    def test_asterisques_de_bas_de_page_retires(self):
        assert normaliser_substance("AMOXICILLINE**") == "AMOXICILLINE"

    def test_espaces_reduits(self):
        assert normaliser_substance("  ACIDE   CLAVULANIQUE ") == "ACIDE CLAVULANIQUE"

    def test_valeur_vide(self):
        assert normaliser_substance(None) == ""


class TestSubstanceSimple:
    def test_substance_seule(self):
        s = parse_inn("PARACETAMOL")
        assert s.base == "PARACETAMOL"
        assert s.sel == ""
        assert not s.est_association
        assert not s.incertain

    def test_le_texte_d_origine_est_conserve(self):
        assert parse_inn("  PARACETAMOL ").raw == "PARACETAMOL"

    def test_valeur_vide(self):
        assert parse_inn("").base == ""


class TestFormeSaline:
    def test_exprime_en_donne_la_base(self):
        s = parse_inn("AMOXICILLINE TRIHYDRATEE EXPRIME EN AMOXICILLINE")
        assert s.base == "AMOXICILLINE"
        assert s.sel == "TRIHYDRATEE"

    def test_le_sel_peut_preceder_la_base(self):
        # "ACETYLSALICYLATE DE DL LYSINE EXPRIME EN ACIDE ACETYLSALICYLIQUE"
        s = parse_inn("ACETYLSALICYLATE DE DL LYSINE EXPRIME EN ACIDE ACETYLSALICYLIQUE")
        assert s.base == "ACIDE ACETYLSALICYLIQUE"

    def test_sous_forme(self):
        s = parse_inn("AMOXICILLINE SOUS FORME TRIHYDRATEE")
        assert s.base == "AMOXICILLINE"
        assert "TRIHYDRATEE" in s.sel

    def test_parenthese_donne_la_base(self):
        s = parse_inn("AMLODIPINE BESILATE (AMLODIPINE)")
        assert s.base == "AMLODIPINE"
        assert s.sel == "BESILATE"

    def test_sel_accole_sans_marqueur(self):
        s = parse_inn("AMLODIPINE SOUS  FORME BESYLATE")
        assert s.base == "AMLODIPINE"


class TestAssociations:
    def test_deux_substances(self):
        s = parse_inn("PARACETAMOL/CAFEINE")
        assert s.base == "PARACETAMOL"
        assert s.associes == ("CAFEINE",)
        assert s.est_association

    def test_trois_substances(self):
        s = parse_inn("ACETYLCYSTEINE/TUAMINOHEPTANE/CHLORURE DE BENZALKONIUM")
        assert len(s.toutes_substances) == 3

    def test_association_avec_sels_des_deux_cotes(self):
        s = parse_inn(
            "AMOXICILLINE TRIHYDRATEE EXPRIME EN AMOXICILLINE"
            "/ACIDE CLAVULANIQUE POTASSIQUE EXPRIME EN ACIDE CLAVULANIQUE"
        )
        assert s.base == "AMOXICILLINE"
        assert s.associes == ("ACIDE CLAVULANIQUE",)

    def test_sous_forme_apres_slash_n_est_pas_une_association(self):
        # "ACIDE ACETYLSALICYTIQUE/SOUS FORME DE ACETYLSALICYLATE DE DL-LYSINE"
        s = parse_inn("ACIDE ACETYLSALICYLIQUE/SOUS FORME DE ACETYLSALICYLATE DE DL-LYSINE")
        assert not s.est_association
        assert s.base == "ACIDE ACETYLSALICYLIQUE"


class TestPrudence:
    def test_synonyme_entre_parentheses_est_signale(self):
        # "(OU ...)" annonce un autre nom, pas une forme saline : on ne tranche pas.
        s = parse_inn("ALFACALCIDOL (OU 1 ALPHA-HYDROXYCHOLECALCIFEROL)")
        assert s.incertain
        assert s.motif == "synonyme_entre_parentheses"

    def test_deux_presentations_dans_une_cellule_sont_signalees(self):
        s = parse_inn(
            "PARACETAMOL/PSEUDOEPHEDRINE COMP. DE JOUR "
            "ET PARACETAMOL/DIPHENHYDRAMINE COMP. DE NUIT"
        )
        assert s.incertain
        assert s.motif == "deux_presentations"

    def test_une_ecriture_incertaine_garde_son_texte(self):
        brut = "ALFACALCIDOL (OU 1 ALPHA-HYDROXYCHOLECALCIFEROL)"
        assert parse_inn(brut).raw == brut


class TestCleDeRegroupement:
    def test_deux_ecritures_de_la_meme_substance_se_rejoignent(self):
        a = parse_inn("AMOXICILLINE TRIHYDRATEE EXPRIME EN AMOXICILLINE")
        b = parse_inn("AMOXICILLINE SOUS FORME TRIHYDRATEE")
        assert a.cle() == b.cle() == "AMOXICILLINE"

    def test_la_forme_saline_ne_change_pas_la_cle(self):
        assert parse_inn("AMLODIPINE BESILATE (AMLODIPINE)").cle() == parse_inn("AMLODIPINE").cle()

    def test_une_association_ne_se_confond_JAMAIS_avec_la_substance_seule(self):
        # Le point le plus important du module : rapprocher paracetamol et
        # paracetamol+codeine ferait disparaitre un opiace d'une recherche.
        seul = parse_inn("PARACETAMOL")
        avec = parse_inn("PARACETAMOL/CODEINE PHOSPHATE HEMIHYDRATE")
        assert seul.cle() != avec.cle()

    def test_l_ordre_des_substances_est_conserve(self):
        s = parse_inn("AMLODIPINE/VALSARTAN")
        assert s.cle().startswith("AMLODIPINE")


@pytest.mark.parametrize("brut", [
    "PARACETAMOL",
    "PARACETAMOL/CAFEINE",
    "AMLODIPINE BESILATE EXPRIME EN AMLODIPINE/VALSARTAN",
    "AMOXICILLINE SODIQUE EXPRIME EN AMOXICILLINE",
])
def test_toute_dci_du_registre_produit_une_base(brut):
    assert parse_inn(brut).base
    assert isinstance(parse_inn(brut), Substance)
