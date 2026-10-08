from __future__ import annotations

import re

import pytest

from seo_os.config import ClientContext, ConversionTarget, SitePage, Topic, load_budgets, load_pricing, load_profiles
from seo_os.costs import Usage
from seo_os.llm import LLMResult
from seo_os.schemas import (
    Brief,
    CallToAction,
    ExtractedClaim,
    FactCheckResult,
    FactVerdict,
    InternalLinkPlan,
    MathExtraction,
    Metadata,
    OutlineSection,
    Review,
    SourceExtraction,
)

CTA_URL = "https://phassyl.ch/cours/algebre-lineaire/"
OTHER_URL = "https://phassyl.ch/cours-particuliers-de-maths-en-ligne/"

ARTICLE = f"""# Valeurs propres et vecteurs propres : comprendre et calculer

Une matrice transforme des vecteurs ; certains gardent leur direction. Ce sont les vecteurs propres,
et le facteur d'étirement est la valeur propre associée. Cette idée revient dans tout le cursus
d'algèbre linéaire [S1].

## L'idée géométrique

{"Une phrase explicative sur les directions invariantes et leur rôle concret. " * 40}

## Calculer les valeurs propres

{"On écrit le polynôme caractéristique puis on cherche ses racines, étape par étape. " * 40}

## Exercice corrigé

Soit $A = \\begin{{pmatrix}} 2 & 0 \\\\ 0 & 3 \\end{{pmatrix}}$. Ses valeurs propres sont $2$ et $3$.

{"On vérifie chaque calcul en remplaçant dans l'équation de départ, sans sauter d'étape. " * 30}

## Aller plus loin

Pour consolider ces bases, suivez le [cours gratuit d'algèbre linéaire]({CTA_URL}) ou réservez des
[cours particuliers de maths en ligne]({OTHER_URL}).
"""


@pytest.fixture
def topic() -> Topic:
    return Topic(
        id="valeurs-propres",
        type="technical_math",
        status="ready",
        title="Valeurs propres et vecteurs propres",
        primary_keyword="valeurs propres vecteurs propres",
        secondary_keywords=["calculer valeurs propres"],
        intent="informational",
        audience="Étudiants BA1",
        risk_level="low",
        business_value="low",
        conversion_target=ConversionTarget(primary=CTA_URL, action="Inscription"),
        preferred_source_domains=["epfl.ch"],
        manual_urls=["https://example.org/cours"],
        checks=["python_math_verification"],
    )


@pytest.fixture
def client() -> ClientContext:
    return ClientContext(
        slug="phassyl",
        domain="phassyl.ch",
        bible_md="# Bible de test\nTon : vouvoiement.",
        pages=[
            SitePage(url=CTA_URL, title="Algèbre linéaire – Être prêt pour l'université", type="course"),
            SitePage(url=OTHER_URL, title="Cours particuliers de maths en ligne", type="commercial"),
        ],
    )


@pytest.fixture
def budgets():
    return load_budgets()


@pytest.fixture
def pricing():
    return load_pricing()


@pytest.fixture
def profiles():
    return load_profiles()


def make_brief() -> Brief:
    return Brief(
        primary_keyword="valeurs propres vecteurs propres",
        secondary_keywords=["calculer valeurs propres"],
        search_intent="comprendre et calculer",
        target_audience="Étudiants BA1",
        content_objective="savoir calculer",
        angle="géométrique puis calculatoire",
        recommended_title="Valeurs propres et vecteurs propres : comprendre et calculer",
        outline=[OutlineSection(heading="L'idée", level=2, purpose="intuition", key_points=["direction"], source_ids=["S1"])],
        questions_to_answer=["Qu'est-ce qu'une valeur propre ?"],
        entities_to_cover=["polynôme caractéristique"],
        competitor_gaps=[],
        serp_observations=[],
        required_claim_ids=["C1"],
        internal_links=[InternalLinkPlan(url=OTHER_URL, anchor_hint="cours de maths", placement="fin")],
        cta=CallToAction(url=CTA_URL, text_hint="cours gratuit", placement="fin"),
        recommended_word_count=1200,
        overlap_warnings=[],
        risk_notes=[],
    )


class FakeProvider:
    """Fournisseur LLM factice : réponses déterministes par tâche, usage fixe."""

    def __init__(self, review_action: str = "PASS", article: str = ARTICLE, eigenvalues=("2", "3")):
        self.review_action = review_action
        self.article = article
        self.eigenvalues = list(eigenvalues)
        self.calls: list[str] = []

    def generate(self, spec, system, user, schema):
        self.calls.append(spec.task)
        usage = Usage(input_tokens=1000, output_tokens=500)
        task = spec.task
        if task == "extract_claims":
            parsed = SourceExtraction(
                relevant=True,
                summary="Cours d'algèbre linéaire.",
                claims=[
                    ExtractedClaim(
                        statement="Les valeurs propres sont au programme d'algèbre linéaire.",
                        quote="Les valeurs propres font partie du programme",
                        claim_type="factual",
                    ),
                    ExtractedClaim(statement="Inventée", quote="cette phrase n'existe pas dans la source", claim_type="factual"),
                ],
                reader_questions=["Comment calculer une valeur propre ?"],
            )
        elif task == "brief":
            parsed = make_brief()
        elif task in ("write", "rewrite"):
            return LLMResult(text=self.article, usage=usage)
        elif task == "metadata":
            parsed = Metadata(
                title_tag="Valeurs propres et vecteurs propres : méthode et exercices",
                meta_description=(
                    "Comprenez ce que sont les valeurs propres et vecteurs propres, puis apprenez à les "
                    "calculer pas à pas grâce à des exercices corrigés et commentés."
                ),
                slug="valeurs-propres-vecteurs-propres",
            )
        elif task == "factcheck":
            n = len(re.findall(r"### Index \d+", user))
            parsed = FactCheckResult(
                verdicts=[FactVerdict(index=i, verdict="supported", explanation="ok") for i in range(n)]
            )
        elif task == "review":
            parsed = Review(
                overall_quality_score=85,
                seo_score=80,
                style_score=82,
                search_intent_score=88,
                factual_risk="low",
                cannibalization_risk="low",
                issues=[],
                unmarked_factual_claims=[],
                recommended_action=self.review_action,
                summary="Bon article.",
            )
        elif task == "math_extract":
            parsed = MathExtraction.model_validate(
                {
                    "exercises": [
                        {
                            "label": "Exercice 1",
                            "matrix": [["2", "0"], ["0", "3"]],
                            "eigenvalues": self.eigenvalues,
                            "eigenpairs": [{"eigenvalue": "2", "vector": ["1", "0"]}],
                        }
                    ]
                }
            )
        else:
            raise AssertionError(f"tâche inattendue : {task}")
        return LLMResult(text=parsed.model_dump_json(), usage=usage, parsed=parsed)

    def web_search(self, spec, system, user, allowed_domains, country):
        self.calls.append("search")
        usage = Usage(input_tokens=500, output_tokens=200, web_search_calls=1)
        url = "https://www.epfl.ch/education/" if allowed_domains else "https://example.org/autre"
        return LLMResult(text=f"{url} | Titre | utile", usage=usage, citations=[(url, "Titre")])
