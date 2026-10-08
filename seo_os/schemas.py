"""Schémas Pydantic.

Deux familles :
- sorties structurées des LLM : tous les champs sont requis et sans valeur par défaut, pour rester
  compatibles avec les modes « strict » d'OpenAI et d'Anthropic ;
- artefacts du pipeline (paquet de recherche, rapports) : sérialisés en JSON sur disque.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ClaimType = Literal["factual", "sensitive", "general"]
Level = Literal["low", "medium", "high"]
RecommendedAction = Literal["PASS", "REWRITE", "RESEARCH_REQUIRED", "HUMAN_REVIEW"]


# --- Sorties structurées des LLM -------------------------------------------------------------


class WebSearchHit(BaseModel):
    url: str
    title: str
    why_relevant: str


class WebSearchResults(BaseModel):
    results: list[WebSearchHit]


class ExtractedClaim(BaseModel):
    statement: str = Field(description="Affirmation reformulée, autonome, en français")
    quote: str = Field(description="Citation EXACTE copiée du texte source qui appuie l'affirmation")
    claim_type: ClaimType


class SourceExtraction(BaseModel):
    relevant: bool
    summary: str
    claims: list[ExtractedClaim]
    reader_questions: list[str]


class OutlineSection(BaseModel):
    heading: str
    level: Literal[2, 3]
    purpose: str
    key_points: list[str]
    source_ids: list[str]


class InternalLinkPlan(BaseModel):
    url: str
    anchor_hint: str
    placement: str


class CallToAction(BaseModel):
    url: str
    text_hint: str
    placement: str


class Brief(BaseModel):
    primary_keyword: str
    secondary_keywords: list[str]
    search_intent: str
    target_audience: str
    content_objective: str
    angle: str
    recommended_title: str
    outline: list[OutlineSection]
    questions_to_answer: list[str]
    entities_to_cover: list[str]
    competitor_gaps: list[str]
    serp_observations: list[str]
    required_claim_ids: list[str]
    internal_links: list[InternalLinkPlan]
    cta: CallToAction
    recommended_word_count: int
    overlap_warnings: list[str]
    risk_notes: list[str]


class Metadata(BaseModel):
    title_tag: str
    meta_description: str
    slug: str


class FactVerdict(BaseModel):
    index: int
    verdict: Literal["supported", "partial", "unsupported"]
    explanation: str


class FactCheckResult(BaseModel):
    verdicts: list[FactVerdict]


class ReviewIssue(BaseModel):
    severity: Level
    category: Literal[
        "search_intent",
        "brief_compliance",
        "repetition",
        "clarity",
        "style",
        "weak_argument",
        "unsupported_claim",
        "hallucination_risk",
        "ai_filler",
        "keyword_stuffing",
        "internal_links",
        "cannibalization",
        "terminology",
        "accuracy",
        "other",
    ]
    location: str
    description: str
    suggestion: str


class Review(BaseModel):
    overall_quality_score: int = Field(description="0 à 100")
    seo_score: int = Field(description="0 à 100")
    style_score: int = Field(description="0 à 100")
    search_intent_score: int = Field(description="0 à 100")
    factual_risk: Level
    cannibalization_risk: Level
    issues: list[ReviewIssue]
    unmarked_factual_claims: list[str]
    recommended_action: RecommendedAction
    summary: str


class EigenPair(BaseModel):
    eigenvalue: str
    vector: list[str]


class MathExercise(BaseModel):
    label: str
    matrix: list[list[str]]
    eigenvalues: list[str]
    eigenpairs: list[EigenPair]


class MathExtraction(BaseModel):
    exercises: list[MathExercise]


# --- Artefacts du pipeline -------------------------------------------------------------------


class Source(BaseModel):
    id: str
    url: str
    title: str
    domain: str
    origin: Literal["manual", "web"]
    is_preferred_domain: bool
    fetched: bool
    fetch_error: str | None = None
    content_type: str | None = None
    word_count: int = 0
    headings: list[str] = Field(default_factory=list)
    relevant: bool = False
    summary: str = ""
    reader_questions: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    id: str
    source_id: str
    statement: str
    quote: str
    claim_type: ClaimType
    quote_verified: bool


class ResearchPacket(BaseModel):
    topic_id: str
    created_at: str
    search_mode: str
    sources: list[Source]
    claims: list[Claim]
    cost_usd: float
    duration_s: float
    steps: list[dict]
    errors: list[str] = Field(default_factory=list)

    def usable_sources(self) -> list[Source]:
        return [s for s in self.sources if s.fetched and s.relevant]

    def verified_claims(self) -> list[Claim]:
        return [c for c in self.claims if c.quote_verified]
