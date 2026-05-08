"""Unit tests for domain_router.py."""
from __future__ import annotations

import pytest

from app.services.domain_router import (
    RouteResult,
    _keyword_in_text,
    _lexical_scores,
    get_domain_config,
    route_question,
)


class TestLexicalScores:
    def test_labor_french(self):
        scores = _lexical_scores("Quels sont les droits d'un salarié licencié ?", "fr")
        assert scores.get("labor", 0) > scores.get("corporate", 0)
        assert scores.get("labor", 0) > scores.get("investment", 0)

    def test_corporate_french(self):
        scores = _lexical_scores("Comment constituer une SARL en Tunisie ?", "fr")
        assert scores.get("corporate", 0) > scores.get("labor", 0)

    def test_data_protection_french(self):
        scores = _lexical_scores("Quelles sont les obligations INPDP pour mon entreprise ?", "fr")
        assert scores.get("data_protection", 0) > scores.get("labor", 0)

    def test_cross_domain_when_ambiguous(self):
        # Mix labor + corporate signals
        scores = _lexical_scores(
            "Un gérant de SARL peut-il licencier un salarié ?", "fr"
        )
        # Both domains should have non-zero scores
        assert scores["labor"] > 0
        assert scores["corporate"] > 0

    def test_unknown_no_match(self):
        scores = _lexical_scores("Quelle est la météo demain ?", "fr")
        assert all(v == 0 for v in scores.values())


class TestRouteQuestion:
    @pytest.mark.asyncio
    async def test_explicit_loi_code_override(self):
        result = await route_question("question", "fr", targeted_loi_code="CS")
        domain, config = result
        assert domain == "corporate"
        assert config.domain == "corporate"
        assert isinstance(result, RouteResult)
        assert result.confidence == 1.0
        assert "Explicit loi code override" in result.explanation

    @pytest.mark.asyncio
    async def test_labor_domain_routing(self):
        result = await route_question("code du travail et syndicat", "fr")
        domain, config = result
        assert domain == "labor"
        assert config.domain == "labor"
        assert result.confidence > 0
        assert "Lexical top=labor" in result.explanation

    @pytest.mark.asyncio
    async def test_company_profile_blend(self):
        result = await route_question(
            "question générique",
            "fr",
            company_profile={"sector": "investissement", "activities": "APII"},
        )
        domain, config = result
        # Profile should steer toward investment even with weak lexical signal
        assert domain == "investment"

    @pytest.mark.asyncio
    async def test_cross_domain_when_close(self):
        # Balanced labor + corporate signals trigger cross_domain (gap < 25%)
        result = await route_question(
            "Le gérant d'une SARL procède au licenciement d'un salarié ayant un contrat de travail", "fr"
        )
        domain, config = result
        # When top two scores are within 25%, cross_domain is triggered
        assert domain == "cross_domain"
        assert "Cross-domain triggered" in result.explanation

    @pytest.mark.asyncio
    async def test_unknown_returns_zero_confidence(self):
        result = await route_question("Quelle est la météo demain ?", "fr")
        # All keyword scores are 0 → below threshold → falls to LLM fallback which may fail in tests
        assert result.confidence <= 0.01 or result.domain in ("unknown", "cross_domain")

    @pytest.mark.asyncio
    async def test_route_result_tuple_compat(self):
        """RouteResult supports backward-compatible tuple unpacking."""
        domain, config = await route_question("code du travail", "fr")
        assert isinstance(domain, str)
        assert hasattr(config, "top_k")


class TestKeywordInText:
    """Word-boundary matching for short keywords."""

    def test_sa_does_not_match_savons(self):
        assert _keyword_in_text("sa", "nous ne savons pas") is False

    def test_sa_matches_standalone(self):
        assert _keyword_in_text("sa", "créer une sa en tunisie") is True

    def test_long_keyword_substring(self):
        assert _keyword_in_text("données personnelles", "des données personnelles de clients") is True

    def test_short_arabic_keyword(self):
        # Arabic "أجر" (3 chars) should use boundary matching
        assert _keyword_in_text("أجر", "دفع أجر العامل") is True


class TestDataProtectionEcommerce:
    """Regression: French e-commerce data protection request.

    The system previously cited the Code des Sociétés instead of
    the Loi 2004-63 because 'SA' matched inside 'savons' and
    data_protection keywords were too narrow.
    """

    QUESTION = (
        "Notre startup e-commerce à Tunis collecte des données personnelles "
        "de clients tunisiens et européens (nom, email, adresse, historique d'achat). "
        "Nous utilisons des serveurs hébergés en France. Nous n'avons jamais déclaré "
        "nos traitements à l'INPDP. Un client européen a demandé la suppression "
        "de ses données et nous ne savons pas comment répondre."
    )

    def test_lexical_scores_data_protection_dominates(self):
        scores = _lexical_scores(self.QUESTION, "fr")
        assert scores.get("data_protection", 0) > 0, "data_protection must score > 0"
        # data_protection must be the clear winner
        for domain in ("corporate", "labor", "investment"):
            assert scores.get("data_protection", 0) > scores.get(domain, 0), (
                f"data_protection ({scores.get('data_protection', 0):.3f}) must beat "
                f"{domain} ({scores.get(domain, 0):.3f})"
            )

    def test_corporate_sa_no_false_positive(self):
        scores = _lexical_scores(self.QUESTION, "fr")
        # 'SA' should NOT match inside 'savons'
        assert scores.get("corporate", 0) == 0, (
            f"corporate should score 0 (no real corporate keywords), got {scores.get('corporate', 0):.3f}"
        )

    @pytest.mark.asyncio
    async def test_routes_to_data_protection(self):
        result = await route_question(self.QUESTION, "fr")
        domain, config = result
        assert domain == "data_protection", (
            f"Expected data_protection, got {domain} (explanation: {result.explanation})"
        )
        assert config.domain == "data_protection"


class TestArabicLaborContracts:
    """Regression: Arabic labor law question about workers without
    written contracts and unpaid overtime.

    The system previously routed to cross_domain because Arabic labor
    keywords were too sparse (only 'عمل' matched) causing a tie with
    corporate ('شركة' matched).
    """

    QUESTION = (
        "شركتنا شركة ذات مسؤولية محدودة في تونس العاصمة، تعمل في قطاع البناء "
        "وتضم 20 عاملاً. 5 عمال يعملون منذ سنة دون عقود عمل مكتوبة. "
        "نحن لم ندفع لهم أجور إضافة على العمل الإضافي. "
        "هل نحن في وضع مخالف للقانون؟"
    )

    def test_lexical_scores_labor_dominates(self):
        scores = _lexical_scores(self.QUESTION, "ar")
        assert scores.get("labor", 0) > 0, "labor must score > 0"
        assert scores.get("labor", 0) > scores.get("corporate", 0), (
            f"labor ({scores.get('labor', 0):.3f}) must beat "
            f"corporate ({scores.get('corporate', 0):.3f})"
        )

    def test_labor_hits_multiple_arabic_keywords(self):
        scores = _lexical_scores(self.QUESTION, "ar")
        # With expanded keywords, labor should score significantly
        # higher than the old tie of 0.316
        assert scores.get("labor", 0) > 0.5, (
            f"labor score ({scores.get('labor', 0):.3f}) should be > 0.5 "
            f"with expanded Arabic keywords"
        )

    def test_no_cross_domain_tie(self):
        scores = _lexical_scores(self.QUESTION, "ar")
        labor_score = scores.get("labor", 0)
        corporate_score = scores.get("corporate", 0)
        if labor_score > 0 and corporate_score > 0:
            gap = (labor_score - corporate_score) / labor_score
            assert gap >= 0.25, (
                f"Gap between labor ({labor_score:.3f}) and corporate "
                f"({corporate_score:.3f}) is {gap:.2%}, too close — "
                f"would trigger cross_domain"
            )

    @pytest.mark.asyncio
    async def test_routes_to_labor(self):
        result = await route_question(self.QUESTION, "ar")
        domain, config = result
        assert domain == "labor", (
            f"Expected labor, got {domain} (explanation: {result.explanation})"
        )
        assert config.domain == "labor"


class TestTunisianLaborRouting:
    """Labor law questions must route to labor, never to corporate or credit_info."""

    def test_labor_scores_dominate_for_contracts_question(self):
        q = (
            "Un employeur tunisien a embauché des travailleurs sans contrat de travail "
            "écrit et ne paie pas les heures supplémentaires. Quels risques ?"
        )
        scores = _lexical_scores(q, "fr")
        assert scores.get("labor", 0) > 0.5, f"labor={scores.get('labor',0):.3f}"
        assert scores.get("corporate", 0) == 0, f"corporate should be 0, got {scores.get('corporate',0):.3f}"
        assert scores.get("credit_info", 0) == 0, f"credit_info should be 0, got {scores.get('credit_info',0):.3f}"

    @pytest.mark.asyncio
    async def test_routes_to_labor_contracts(self):
        result = await route_question(
            "Quels sont les droits d'un salarié licencié sans préavis en Tunisie ?", "fr"
        )
        assert result.domain == "labor", f"Expected labor, got {result.domain}"

    @pytest.mark.asyncio
    async def test_routes_to_labor_overtime(self):
        result = await route_question(
            "Comment calculer les heures supplémentaires selon le code du travail tunisien ?", "fr"
        )
        assert result.domain == "labor", f"Expected labor, got {result.domain}"

    @pytest.mark.asyncio
    async def test_routes_to_labor_cnss(self):
        result = await route_question(
            "Un employeur doit-il déclarer ses salariés à la CNSS dès le premier jour de travail ?", "fr"
        )
        assert result.domain == "labor", f"Expected labor, got {result.domain}"

    @pytest.mark.asyncio
    async def test_arabic_labor_never_corporate(self):
        q = (
            "عامل يعمل بدون عقد شغل ولم يتقاضى أجوره عن ساعات العمل الإضافية. "
            "ما هي حقوقه حسب مجلة الشغل ؟"
        )
        result = await route_question(q, "ar")
        assert result.domain == "labor", f"Expected labor, got {result.domain}"

    def test_labor_never_close_to_corporate(self):
        """Pure labor question must have a large gap over corporate."""
        q = "Le salarié a droit à une indemnité de licenciement et un préavis selon le code du travail."
        scores = _lexical_scores(q, "fr")
        labor = scores.get("labor", 0)
        corporate = scores.get("corporate", 0)
        assert labor > 0, "labor must score > 0"
        if corporate > 0:
            gap = (labor - corporate) / labor
            assert gap >= 0.25, (
                f"labor ({labor:.3f}) too close to corporate ({corporate:.3f}), "
                f"gap={gap:.2%} < 25%"
            )


class TestCreditInfoRouting:
    """Credit information company questions must route to credit_info,
    not to corporate or data_protection."""

    QUESTION_FR = (
        "Quelles sont les obligations d'une société de renseignement de crédit "
        "en Tunisie selon la réglementation de la Banque Centrale de Tunisie ?"
    )

    def test_lexical_scores_credit_info_dominates(self):
        scores = _lexical_scores(self.QUESTION_FR, "fr")
        assert scores.get("credit_info", 0) > 0, "credit_info must score > 0"
        for rival in ("corporate", "labor", "investment", "data_protection"):
            assert scores.get("credit_info", 0) > scores.get(rival, 0), (
                f"credit_info ({scores.get('credit_info',0):.3f}) must beat "
                f"{rival} ({scores.get(rival,0):.3f})"
            )

    @pytest.mark.asyncio
    async def test_routes_to_credit_info(self):
        result = await route_question(self.QUESTION_FR, "fr")
        assert result.domain == "credit_info", (
            f"Expected credit_info, got {result.domain} ({result.explanation})"
        )

    @pytest.mark.asyncio
    async def test_credit_scoring_question(self):
        result = await route_question(
            "Comment fonctionne le crédit scoring et la centrale des risques en Tunisie ?", "fr"
        )
        assert result.domain == "credit_info", f"Expected credit_info, got {result.domain}"

    @pytest.mark.asyncio
    async def test_loi_code_bct_override(self):
        result = await route_question("question", "fr", targeted_loi_code="BCT")
        assert result.domain == "credit_info"
        assert result.confidence == 1.0

    def test_labor_question_scores_zero_credit_info(self):
        """A pure labor question must not trigger credit_info."""
        q = "Le salarié a été licencié sans préavis. Quels sont ses droits ?"
        scores = _lexical_scores(q, "fr")
        assert scores.get("credit_info", 0) == 0, (
            f"credit_info should be 0 for labor question, got {scores.get('credit_info',0):.3f}"
        )


class TestCorporateAssocieRouting:
    """Regression: 'associé' must route to corporate, not labor.

    The sentence 'Mon associé ne vient plus travailler depuis 2 mois'
    previously routed to labor because the bare keyword 'travail'
    substring-matched 'travailler' and corporate had no 'associé' keyword.
    """

    QUESTION = "Mon associé ne vient plus travailler depuis 2 mois"

    def test_lexical_scores_corporate_dominates(self):
        scores = _lexical_scores(self.QUESTION, "fr")
        assert scores.get("corporate", 0) > 0, "corporate must score > 0"
        assert scores.get("corporate", 0) > scores.get("labor", 0), (
            f"corporate ({scores.get('corporate', 0):.3f}) must beat "
            f"labor ({scores.get('labor', 0):.3f})"
        )

    def test_labor_does_not_match_travailler(self):
        """Bare 'travail' was removed; 'travailler' must not trigger labor."""
        scores = _lexical_scores(self.QUESTION, "fr")
        assert scores.get("labor", 0) == 0, (
            f"labor should score 0, got {scores.get('labor', 0):.3f}"
        )

    @pytest.mark.asyncio
    async def test_routes_to_corporate(self):
        result = await route_question(self.QUESTION, "fr")
        assert result.domain == "corporate", (
            f"Expected corporate, got {result.domain} ({result.explanation})"
        )

    def test_corporate_keywords_present(self):
        """Verify all expected corporate keywords exist."""
        from app.services.domain_router import _DOMAIN_KEYWORDS
        fr_kws = _DOMAIN_KEYWORDS["corporate"]["fr"]
        for expected in ["associé", "actionnaire", "parts sociales",
                         "assemblée générale", "statuts", "dissolution", "capital social"]:
            assert expected in fr_kws, f"Missing corporate FR keyword: {expected}"
        ar_kws = _DOMAIN_KEYWORDS["corporate"]["ar"]
        for expected in ["شريك", "مساهم", "رأس المال"]:
            assert expected in ar_kws, f"Missing corporate AR keyword: {expected}"


class TestNumericScoresRegression:
    """Pin exact numeric score expectations for the two regression phrases."""

    def test_associe_fr_corporate_score_positive(self):
        scores = _lexical_scores("Mon associé ne vient plus travailler depuis 2 mois", "fr")
        assert scores.get("corporate", 0) > 0.2, (
            f"corporate score should be > 0.2, got {scores.get('corporate', 0):.4f}"
        )

    def test_associe_fr_labor_score_zero(self):
        scores = _lexical_scores("Mon associé ne vient plus travailler depuis 2 mois", "fr")
        assert scores.get("labor", 0) == 0, (
            f"labor score should be 0, got {scores.get('labor', 0):.4f}"
        )

    def test_associe_fr_corporate_is_sole_winner(self):
        scores = _lexical_scores("Mon associé ne vient plus travailler depuis 2 mois", "fr")
        corporate = scores.get("corporate", 0)
        for domain, score in scores.items():
            if domain != "corporate":
                assert corporate > score, (
                    f"corporate ({corporate:.4f}) must beat {domain} ({score:.4f})"
                )

    def test_sharika_ar_corporate_score_positive(self):
        scores = _lexical_scores("أريد أن أفتح شركة مع شريك", "ar")
        assert scores.get("corporate", 0) > 0.5, (
            f"corporate score should be > 0.5 (two hits), got {scores.get('corporate', 0):.4f}"
        )

    def test_sharika_ar_labor_score_zero(self):
        scores = _lexical_scores("أريد أن أفتح شركة مع شريك", "ar")
        assert scores.get("labor", 0) == 0, (
            f"labor score should be 0, got {scores.get('labor', 0):.4f}"
        )

    @pytest.mark.asyncio
    async def test_sharika_ar_routes_to_corporate(self):
        result = await route_question("أريد أن أفتح شركة مع شريك", "ar")
        assert result.domain == "corporate", (
            f"Expected corporate, got {result.domain} ({result.explanation})"
        )


class TestGetDomainConfig:
    def test_known_domain(self):
        cfg = get_domain_config("labor")
        assert cfg.domain == "labor"
        assert cfg.top_k == 12

    def test_unknown_fallback(self):
        cfg = get_domain_config("nonexistent")
        assert cfg.domain == "unknown"
