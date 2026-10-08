"""Modèle de données du cockpit.

Chaque donnée porte sa provenance (`source`) : c'est elle qui détermine le badge affiché.
- public   : donnée publique réelle relevée sur le site du client
- pipeline : produite par le pipeline (articles, coûts, QA)
- import   : importée depuis un export du client
- gsc/treg : données Search Console / Treg (après connexion)
- proposal : analyse proposée, non validée
- validated: validée par l'utilisateur
- example  : exemple de démonstration (jamais pour une métrique de performance)
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class Client(Base, TimestampMixin):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(16), default="fr")
    country: Mapped[str] = mapped_column(String(8), default="CH")
    monthly_target: Mapped[int] = mapped_column(Integer, default=60)
    announced_content_count: Mapped[str | None] = mapped_column(String(64))  # ex. "300–400" (déclaratif)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)


class Integration(Base, TimestampMixin):
    """État d'une intégration externe : affiché dans l'en-tête et l'écran Intégrations."""

    __tablename__ = "integrations"
    __table_args__ = (UniqueConstraint("client_id", "kind"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    kind: Mapped[str] = mapped_column(String(32))
    # not_configured | configured | connected | no_credits | error | active (fonction locale)
    status: Mapped[str] = mapped_column(String(32), default="not_configured")
    detail: Mapped[str | None] = mapped_column(Text)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Segment(Base, TimestampMixin):
    __tablename__ = "segments"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    group: Mapped[str] = mapped_column(String(32))  # "epfl" | "hors_epfl"
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    offer_url: Mapped[str | None] = mapped_column(String(512))
    business_value: Mapped[str] = mapped_column(String(16), default="medium")  # low | medium | high
    priority: Mapped[int] = mapped_column(Integer, default=2)  # 1 = haute
    position: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(16), default="proposal")
    clusters: Mapped[list[Cluster]] = relationship(
        back_populates="segment", order_by="Cluster.position", cascade="all, delete-orphan"
    )


class Cluster(Base, TimestampMixin):
    __tablename__ = "clusters"
    id: Mapped[int] = mapped_column(primary_key=True)
    segment_id: Mapped[int] = mapped_column(ForeignKey("segments.id"))
    name: Mapped[str] = mapped_column(String(255))
    intent: Mapped[str | None] = mapped_column(Text)
    subjects: Mapped[list] = mapped_column(JSON, default=list)  # facette matière : ["maths", "physique"]
    business_value: Mapped[str] = mapped_column(String(16), default="medium")
    priority: Mapped[int] = mapped_column(Integer, default=2)
    position: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(16), default="proposal")
    segment: Mapped[Segment] = relationship(back_populates="clusters")
    topics: Mapped[list[TargetTopic]] = relationship(
        back_populates="cluster", order_by="TargetTopic.position", cascade="all, delete-orphan"
    )
    pages: Mapped[list[Page]] = relationship(back_populates="cluster")


class TargetTopic(Base, TimestampMixin):
    """Sujet que le client devrait couvrir ; la couverture se calcule sur ces sujets."""

    __tablename__ = "target_topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id"))
    title: Mapped[str] = mapped_column(String(255))
    primary_keyword: Mapped[str | None] = mapped_column(String(255))
    intent: Mapped[str | None] = mapped_column(String(32))
    business_value: Mapped[str] = mapped_column(String(16), default="medium")
    priority: Mapped[int] = mapped_column(Integer, default=2)
    # covered | partial | gap | cannibalized
    coverage_status: Mapped[str] = mapped_column(String(16), default="gap")
    page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"))
    notes: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)
    # Métriques de demande (Treg) : vides tant que non connecté
    search_volume: Mapped[int | None] = mapped_column(Integer)
    difficulty: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(16), default="proposal")
    cluster: Mapped[Cluster] = relationship(back_populates="topics")
    page: Mapped[Page | None] = relationship(foreign_keys=[page_id])


class Page(Base, TimestampMixin):
    """Toute page du patrimoine : existante (importée) ou nouvelle (produite)."""

    __tablename__ = "pages"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    # Clé d'idempotence des imports : URL pour une page existante, "pipeline:<sujet>:<profil>" sinon
    external_key: Mapped[str | None] = mapped_column(String(512), index=True)
    url: Mapped[str | None] = mapped_column(String(512))
    slug: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(512))
    h1: Mapped[str | None] = mapped_column(String(512))
    page_type: Mapped[str] = mapped_column(String(32), default="article")  # article | commercial | course | utility
    origin: Mapped[str] = mapped_column(String(16), default="existing")  # existing | new
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("clusters.id"))
    role: Mapped[str | None] = mapped_column(String(16))  # pillar | support | commercial | utility
    template: Mapped[str | None] = mapped_column(String(64))
    primary_keyword: Mapped[str | None] = mapped_column(String(255))
    # KEEP | UPDATE | MERGE | REDIRECT | REWRITE | DELETE | REPOSITION ; vide = à auditer
    recommended_action: Mapped[str | None] = mapped_column(String(16))
    action_rationale: Mapped[str | None] = mapped_column(Text)
    action_target_page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"))
    action_source: Mapped[str | None] = mapped_column(String(16))  # proposal | validated
    # published | to_audit | in_production | ready_for_review | needs_attention | approved | failed
    status: Mapped[str] = mapped_column(String(32), default="published")
    attention_reasons: Mapped[list] = mapped_column(JSON, default=list)
    quality_score: Mapped[int | None] = mapped_column(Integer)
    factual_risk: Mapped[str | None] = mapped_column(String(16))
    cannibalization_risk: Mapped[str | None] = mapped_column(String(16))
    word_count: Mapped[int | None] = mapped_column(Integer)
    title_tag: Mapped[str | None] = mapped_column(String(255))
    meta_description: Mapped[str | None] = mapped_column(String(512))
    published_at: Mapped[date | None] = mapped_column(Date)
    current_version_id: Mapped[int | None] = mapped_column(ForeignKey("page_versions.id", use_alter=True))
    source: Mapped[str] = mapped_column(String(16), default="public")
    cluster: Mapped[Cluster | None] = relationship(back_populates="pages")
    versions: Mapped[list[PageVersion]] = relationship(
        back_populates="page", foreign_keys="PageVersion.page_id", order_by="PageVersion.version_no"
    )
    runs: Mapped[list[PipelineRun]] = relationship(back_populates="page", order_by="PipelineRun.created_at")


class PageVersion(Base):
    __tablename__ = "page_versions"
    __table_args__ = (UniqueConstraint("page_id", "version_no"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))
    version_no: Mapped[int] = mapped_column(Integer)
    content_md: Mapped[str] = mapped_column(Text)
    change_type: Mapped[str] = mapped_column(String(32))  # draft | auto_rewrite | manual_edit | import
    reason: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(String(128))
    cost_usd: Mapped[float | None] = mapped_column(Float)
    author: Mapped[str] = mapped_column(String(64), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    page: Mapped[Page] = relationship(back_populates="versions", foreign_keys=[page_id])


class PageMetric(Base):
    """Performance journalière d'une page (Search Console). Vide tant que non connecté."""

    __tablename__ = "page_metrics"
    __table_args__ = (UniqueConstraint("page_id", "day"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))
    day: Mapped[date] = mapped_column(Date)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    position: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(16), default="gsc")


class PipelineRun(Base):
    """Exécution du pipeline de production pour une page (résultat complet en JSON)."""

    __tablename__ = "pipeline_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))
    plan_item_id: Mapped[int | None] = mapped_column(ForeignKey("plan_items.id"))
    profile: Mapped[str] = mapped_column(String(16))
    # queued | running | ready_for_review | needs_attention | failed
    status: Mapped[str] = mapped_column(String(32), default="queued")
    result: Mapped[dict | None] = mapped_column(JSON)
    brief: Mapped[dict | None] = mapped_column(JSON)
    research: Mapped[dict | None] = mapped_column(JSON)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str | None] = mapped_column(Text)
    output_dir: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    page: Mapped[Page] = relationship(back_populates="runs")


class PlanItem(Base, TimestampMixin):
    __tablename__ = "plan_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    month: Mapped[str] = mapped_column(String(7))  # "2026-11"
    action: Mapped[str] = mapped_column(String(16))  # CREATE | UPDATE | MERGE | REWRITE | SKIP
    title: Mapped[str] = mapped_column(String(512))
    primary_keyword: Mapped[str | None] = mapped_column(String(255))
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("clusters.id"))
    page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"))
    target_topic_id: Mapped[int | None] = mapped_column(ForeignKey("target_topics.id"))
    template: Mapped[str | None] = mapped_column(String(64))
    business_value: Mapped[str] = mapped_column(String(16), default="medium")
    rationale: Mapped[str | None] = mapped_column(Text)
    # proposed | approved | rejected | postponed | in_production | done
    status: Mapped[str] = mapped_column(String(16), default="proposed")
    source: Mapped[str] = mapped_column(String(16), default="proposal")
    cluster: Mapped[Cluster | None] = relationship()
    page: Mapped[Page | None] = relationship()


class LinkSuggestion(Base, TimestampMixin):
    __tablename__ = "link_suggestions"
    __table_args__ = (UniqueConstraint("source_page_id", "target_page_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    source_page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))
    target_page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))
    anchor: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float)
    kind: Mapped[str] = mapped_column(String(16), default="structural")  # structural | contextual
    # suggested | approved | rejected | applied
    status: Mapped[str] = mapped_column(String(16), default="suggested")
    source: Mapped[str] = mapped_column(String(16), default="proposal")
    source_page: Mapped[Page] = relationship(foreign_keys=[source_page_id])
    target_page: Mapped[Page] = relationship(foreign_keys=[target_page_id])


class SiteIssue(Base, TimestampMixin):
    __tablename__ = "site_issues"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"))
    kind: Mapped[str] = mapped_column(String(32))  # placeholder | inconsistent_info | terminology | cannibalization…
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    title: Mapped[str] = mapped_column(String(255))
    detail: Mapped[str | None] = mapped_column(Text)
    urls: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="open")  # open | resolved | ignored
    source: Mapped[str] = mapped_column(String(16), default="public")
    page: Mapped[Page | None] = relationship()


class ApiCall(Base):
    """Chaque appel API facturable (LLM, Treg…) : base des écrans de coûts."""

    __tablename__ = "api_calls"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"))
    scope: Mapped[str] = mapped_column(String(255))
    step: Mapped[str] = mapped_column(String(64))
    task: Mapped[str] = mapped_column(String(64))
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(64))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cached_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    success: Mapped[bool] = mapped_column(default=True)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
