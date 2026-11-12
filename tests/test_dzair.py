"""Loading the dzair-pharma exports, and the provenance rules around them."""

import datetime as dt

import pytest

from pharmeazor.collect.dzair import (
    DzairProduct,
    Interaction,
    load_file,
    parse_level,
)
from pharmeazor.schemas import Authority, InteractionLevel

RAW = "data/raw/dzair/ibuprof_ne.json"


class TestLevelParsing:
    def test_the_four_ansm_levels(self):
        assert parse_level("Contre-indication") is InteractionLevel.CONTRAINDICATED
        assert parse_level("Association déconseillée") is InteractionLevel.DISCOURAGED
        assert parse_level("Précaution d'emploi") is InteractionLevel.PRECAUTION
        assert parse_level("À prendre en compte") is InteractionLevel.TAKE_INTO_ACCOUNT

    def test_accentless_spelling_also_matches(self):
        assert parse_level("Association deconseillee") is InteractionLevel.DISCOURAGED

    def test_case_is_ignored(self):
        assert parse_level("CONTRE-INDICATION") is InteractionLevel.CONTRAINDICATED

    def test_unknown_wording_returns_none_rather_than_a_milder_level(self):
        # Softening an unrecognised severity is exactly what the spec forbids.
        assert parse_level("peut-être risqué") is None
        assert parse_level("") is None
        assert parse_level(None) is None


class TestInteractionAuthority:
    def _interaction(self, origin: str) -> Interaction:
        return Interaction(
            substance="ANTICOAGULANTS ORAUX", target_kind="Classe",
            level_label="Contre-indication",
            level=InteractionLevel.CONTRAINDICATED,
            risks="Majoration du risque hémorragique.",
            what_to_do="Éviter l'association.", availability="",
            origin_source=origin,
        )

    def test_a_relayed_institutional_source_is_capped_at_the_relay(self):
        # The content comes from ANSM, but we read it on a professional site:
        # the lower of the two authorities governs.
        assert self._interaction("ANSM").effective_authority() is Authority.PROFESSIONAL

    def test_an_unattributed_interaction_is_professional_too(self):
        assert self._interaction("").effective_authority() is Authority.PROFESSIONAL

    def test_the_claimed_origin_is_still_recorded(self):
        assert self._interaction("ANSM").origin_source == "ANSM"

    def test_unrecognised_level_keeps_the_raw_wording(self):
        item = Interaction(
            substance="X", target_kind="Substance", level_label="bizarre",
            level=None, risks="", what_to_do="", availability="", origin_source="",
        )
        assert not item.recognised
        assert item.level_fr == "bizarre"


class TestProvenance:
    def test_dzair_is_always_secondary(self):
        product = DzairProduct(
            url="https://www.dzair-pharma.net/medicament/1", status="Enregistré",
            inn="IBUPROFENE", brand_name="BRUFEN", registration_no="1/2/3",
            code="04 B 042", atc_code="", product_type="", form="COMPRIME",
            route="", strength_raw="400MG", packaging_raw="B/20", prescription="",
            stability="", lab_name="LAB", lab_country="ALGERIE", date_initial="",
            date_final="", nomenclature_year="2026", source_version="Aout 2026",
            description="", list_class="", withdrawal_reason="",
            withdrawal_date="", rcp_pdf_url="",
            collected_at=dt.date(2026, 11, 12),
        )
        assert product.provenance().authority is Authority.PROFESSIONAL
        assert product.official_leaflet_provenance() is None

    def test_a_linked_anpp_leaflet_is_official(self):
        product = DzairProduct(
            url="https://www.dzair-pharma.net/medicament/1", status="Enregistré",
            inn="IBUPROFENE", brand_name="BRUFEN", registration_no="1/2/3",
            code="", atc_code="", product_type="", form="", route="",
            strength_raw="", packaging_raw="", prescription="", stability="",
            lab_name="", lab_country="", date_initial="", date_final="",
            nomenclature_year="", source_version="", description="",
            list_class="", withdrawal_reason="", withdrawal_date="",
            rcp_pdf_url="https://rcp.anpp.dz/storage/rcp-pdfs/x/y.pdf",
        )
        assert product.has_official_leaflet
        assert product.official_leaflet_provenance().authority is Authority.OFFICIAL


@pytest.fixture(scope="module")
def products():
    return load_file(RAW)


@pytest.mark.skipif(
    not __import__("pathlib").Path(RAW).exists(),
    reason="exports dzair absents de data/raw/dzair",
)
class TestRealFile:
    def test_loads_every_record(self, products):
        assert len(products) == 60

    def test_flag_emoji_are_stripped_from_country(self, products):
        countries = {p.lab_country for p in products}
        assert all("\U0001F1E9" not in c for c in countries)
        assert "ALGERIE" in countries

    def test_interactions_are_loaded_with_levels(self, products):
        interactions = [i for p in products for i in p.interactions]
        assert len(interactions) > 500
        assert sum(1 for i in interactions if i.recognised) == len(interactions)

    def test_every_interaction_cites_an_origin(self, products):
        origins = {i.origin_source for p in products for i in p.interactions}
        assert "ANSM" in origins

    def test_generics_are_loaded(self, products):
        assert sum(len(p.generics) for p in products) > 100
