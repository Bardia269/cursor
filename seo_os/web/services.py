"""Services métier du cockpit : couverture, maillage, intégrations, import des résultats du pipeline."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import providers
from ..config import CONFIG_DIR
from .models import (
    ApiCall,
    Client,
    Cluster,
    Integration,
    LinkSuggestion,
    Page,
    PageVersion,
    PipelineRun,
    PlanItem,
    Segment,
    TargetTopic,
    utcnow,
)

# --- Intégrations -----------------------------------------------------------------------------


@dataclass(frozen=True)
class IntegrationSpec:
    kind: str
    label: str
    unlocks: str
    required_for_live: bool


INTEGRATIONS = [
    IntegrationSpec("search_console", "Search Console", "Clics, impressions, positions, requêtes par page", True),
    IntegrationSpec("treg", "Treg (données SEO)", "Volumes, difficulté, SERP, concurrents, backlinks", True),
    IntegrationSpec("site", "Nouveau site phassyl.ch", "Import des 300–400 contenus, publication, maillage appliqué", True),
    IntegrationSpec("anthropic", "Anthropic", "Rédaction, briefs, QA (profil configuré)", False),
    IntegrationSpec("openai", "OpenAI", "Tâches simples à bas coût (après signature)", False),
    IntegrationSpec("content_import", "Import de contenus (fichier)", "Import CSV / JSON d'un export du site", False),
    IntegrationSpec("export", "Export fichiers", "Markdown / HTML / JSON de chaque contenu", False),
    IntegrationSpec("backlinks", "Backlinks", "Domaines référents, link gap, prospects (après signature)", False),
]
SPEC_BY_KIND = {spec.kind: spec for spec in INTEGRATIONS}

CONNECTED_STATES = {"connected", "active"}


def _set(session: Session, client: Client, kind: str, status: providers.ProviderStatus) -> Integration:
    row = session.scalar(select(Integration).where(Integration.client_id == client.id, Integration.kind == kind))
    if row is None:
        row = Integration(client_id=client.id, kind=kind)
        session.add(row)
    row.status, row.detail, row.last_checked_at = status.status, status.detail, utcnow()
    return row


def refresh_integrations(session: Session, client: Client, live: bool = False, only: str | None = None) -> None:
    """Met à jour l'état des intégrations. `live` = tests réseau (bouton « Tester »)."""
    checks = {
        "search_console": lambda: providers.NotConnectedSearchConsole().status(),
        "treg": (providers.check_treg if live else lambda: providers.TregSEODataProvider(providers.treg_from_env()).status()),
        "site": lambda: providers.ProviderStatus("not_configured", "Technologie et accès du nouveau site à recevoir"),
        "anthropic": providers.check_anthropic if live else None,
        "openai": providers.check_openai if live else None,
        "content_import": lambda: providers.ProviderStatus("active", "Import CSV / JSON disponible (Bibliothèque)"),
        "export": lambda: providers.ProviderStatus("active", "Export Markdown / HTML / JSON actif"),
        "backlinks": lambda: providers.NotConnectedBacklinks().status(),
    }
    for kind, check in checks.items():
        if only and kind != only:
            continue
        existing = session.scalar(select(Integration).where(Integration.client_id == client.id, Integration.kind == kind))
        if check is None:  # pas de test réseau : on garde le dernier état connu, sinon on se base sur la clé
            if existing is not None:
                continue
            env_key = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}[kind]
            status = (
                providers.ProviderStatus("configured", "Clé présente — non testée")
                if os.environ.get(env_key)
                else providers.ProviderStatus("not_configured", f"{env_key} absente")
            )
        else:
            status = check()
        _set(session, client, kind, status)


def integration_states(session: Session, client: Client) -> dict[str, Integration]:
    rows = session.scalars(select(Integration).where(Integration.client_id == client.id)).all()
    return {row.kind: row for row in rows}


def is_demo_mode(states: dict[str, Integration]) -> bool:
    return not all(
        states.get(spec.kind) is not None and states[spec.kind].status in CONNECTED_STATES
        for spec in INTEGRATIONS
        if spec.required_for_live
    )


def connected_count(states: dict[str, Integration]) -> tuple[int, int]:
    live = [spec for spec in INTEGRATIONS if spec.required_for_live]
    return sum(1 for s in live if states.get(s.kind) and states[s.kind].status in CONNECTED_STATES), len(live)


# --- Couverture --------------------------------------------------------------------------------

COVERAGE_STATES = ("covered", "partial", "cannibalized", "gap")


@dataclass
class Coverage:
    covered: int = 0
    partial: int = 0
    cannibalized: int = 0
    gap: int = 0

    @property
    def total(self) -> int:
        return self.covered + self.partial + self.cannibalized + self.gap

    @property
    def pct(self) -> int | None:
        """Couvert = 1, partiel ou cannibalisé = 0,5, manquant = 0."""
        if not self.total:
            return None
        return round(100 * (self.covered + 0.5 * (self.partial + self.cannibalized)) / self.total)

    def add(self, other: Coverage) -> None:
        for state in COVERAGE_STATES:
            setattr(self, state, getattr(self, state) + getattr(other, state))

    def share(self, state: str) -> float:
        return 100 * getattr(self, state) / self.total if self.total else 0.0


def cluster_coverage(cluster: Cluster) -> Coverage:
    cov = Coverage()
    for topic in cluster.topics:
        if topic.coverage_status in COVERAGE_STATES:
            setattr(cov, topic.coverage_status, getattr(cov, topic.coverage_status) + 1)
    return cov


def segment_coverage(segment: Segment) -> Coverage:
    cov = Coverage()
    for cluster in segment.clusters:
        cov.add(cluster_coverage(cluster))
    return cov


def group_coverage(segments: list[Segment]) -> Coverage:
    cov = Coverage()
    for segment in segments:
        cov.add(segment_coverage(segment))
    return cov


# --- Maillage interne (règles structurelles) ---------------------------------------------------

LINK_EXCLUDED_ACTIONS = {"MERGE", "REDIRECT", "DELETE"}
MAX_STRUCTURAL_LINKS_PER_SOURCE = 3


def _anchor(page: Page) -> str:
    text = page.primary_keyword or page.title
    return text.split(":")[0].split("|")[0].split(" – ")[0].strip()[:80]


def suggest_structural_links(session: Session, client: Client) -> int:
    """Génère des suggestions de liens à partir de la carte (support → offre, frères, nouveaux contenus).

    Règles, sans IA :
    - un article d'un segment pointe vers la page d'offre du segment ;
    - deux articles du même cluster se citent ;
    - un nouveau contenu reçoit des liens des articles existants du même segment.
    Les pages vouées à être fusionnées, redirigées ou supprimées sont exclues.
    """
    pages = session.scalars(
        select(Page).where(Page.client_id == client.id, Page.cluster_id.is_not(None))
    ).all()
    pages = [p for p in pages if p.recommended_action not in LINK_EXCLUDED_ACTIONS]
    by_url = {p.url: p for p in pages if p.url}
    existing = {
        (s, t) for s, t in session.execute(
            select(LinkSuggestion.source_page_id, LinkSuggestion.target_page_id).where(LinkSuggestion.client_id == client.id)
        )
    }
    created = 0
    outbound: dict[int, int] = {}

    def add(source: Page, target: Page, reason: str, score: float) -> None:
        nonlocal created
        if source.id == target.id or (source.id, target.id) in existing:
            return
        if outbound.get(source.id, 0) >= MAX_STRUCTURAL_LINKS_PER_SOURCE:
            return
        session.add(
            LinkSuggestion(
                client_id=client.id,
                source_page_id=source.id,
                target_page_id=target.id,
                anchor=_anchor(target),
                reason=reason,
                score=score,
                kind="structural",
                source="proposal",
            )
        )
        existing.add((source.id, target.id))
        outbound[source.id] = outbound.get(source.id, 0) + 1
        created += 1

    articles = [p for p in pages if p.page_type == "article"]
    # 1. Nouveaux contenus : liens entrants depuis les articles existants du même segment
    for new in [p for p in articles if p.origin == "new"]:
        for src in articles:
            if src.origin == "existing" and src.cluster.segment_id == new.cluster.segment_id:
                same_cluster = src.cluster_id == new.cluster_id
                add(src, new, "Nouveau contenu : lien entrant depuis un article du même "
                    + ("cluster" if same_cluster else "segment"), 0.85 if same_cluster else 0.7)
    # 2. Article → page d'offre de son segment
    for page in articles:
        offer = by_url.get(page.cluster.segment.offer_url or "")
        if offer is not None:
            add(page, offer, f"Article du segment « {page.cluster.segment.name} » → page d'offre (conversion)", 0.8)
    # 3. Articles du même cluster
    for page in articles:
        for other in articles:
            if other.cluster_id == page.cluster_id and other.id != page.id:
                add(page, other, f"Même cluster « {page.cluster.name} »", 0.65)
    return created


# --- Import des résultats du pipeline ----------------------------------------------------------

TOPIC_STATUS_TO_PAGE_STATUS = {"ready_for_review": "ready_for_review", "needs_attention": "needs_attention", "failed": "failed"}


def import_pipeline_results(session: Session, client: Client, out_root: Path) -> int:
    """Importe out/articles/<sujet>/<profil>/ (V0) : page, versions, exécution, appels API."""
    imported = 0
    calls_by_scope = _load_cost_log(out_root / "costs.jsonl")
    for result_path in sorted((out_root / "articles").glob("*/*/result.json")):
        out_dir = result_path.parent
        result = json.loads(result_path.read_text(encoding="utf-8"))
        topic_id, profile = result["topic"]["id"], result["config"]["profile"]
        key = f"{topic_id}:{profile}"
        page = session.scalar(select(Page).where(Page.client_id == client.id, Page.external_key == f"pipeline:{key}"))
        if page is None:
            page = Page(client_id=client.id, external_key=f"pipeline:{key}", origin="new", page_type="article", source="pipeline")
            session.add(page)
        meta = result.get("metadata") or {}
        review = (result.get("qa") or {}).get("review") or {}
        page.title = result["topic"]["title"]
        page.primary_keyword = result["topic"].get("primary_keyword")
        page.title_tag = meta.get("title_tag")
        page.meta_description = meta.get("meta_description")
        page.status = TOPIC_STATUS_TO_PAGE_STATUS.get(result["status"], result["status"])
        page.attention_reasons = [r for r in result.get("attention_reasons", []) if isinstance(r, str)]
        page.quality_score = review.get("overall_quality_score")
        page.factual_risk = review.get("factual_risk")
        page.cannibalization_risk = review.get("cannibalization_risk")
        page.word_count = (result.get("metrics") or {}).get("word_count")
        page.template = page.template or _template_for(result["topic"].get("type"))
        topic = session.scalar(
            select(TargetTopic).join(Cluster).join(Segment).where(
                Segment.client_id == client.id, TargetTopic.notes.like(f"%benchmark:{topic_id}%")
            )
        )
        if topic is not None:
            page.cluster_id = topic.cluster_id
            topic.page = page
        page.slug = meta.get("slug") or page.slug
        session.flush()
        # Versions (réimport : on détache d'abord la version courante, référencée par la page)
        page.current_version_id = None
        session.flush()
        session.query(PageVersion).filter(PageVersion.page_id == page.id).delete()
        session.flush()
        last_version = None
        for v in result.get("versions", []):
            path = out_dir / v["file"]
            if not path.exists():
                continue
            last_version = PageVersion(
                page_id=page.id,
                version_no=v["version"],
                content_md=path.read_text(encoding="utf-8"),
                change_type=v["change_type"],
                reason=v.get("reason"),
                model=v.get("model"),
                cost_usd=v.get("cost_usd_delta"),
                author="pipeline",
            )
            session.add(last_version)
        session.flush()
        if last_version is not None:
            page.current_version_id = last_version.id
            h1 = next((line[2:].strip() for line in last_version.content_md.splitlines() if line.startswith("# ")), None)
            page.h1 = h1
        # Exécution
        session.query(PipelineRun).filter(PipelineRun.page_id == page.id, PipelineRun.profile == profile).delete()
        research_packet = out_root / "research" / topic_id / "packet.json"
        brief_path = out_dir / "brief.json"
        run = PipelineRun(
            page_id=page.id,
            profile=profile,
            status=result["status"],
            result=result,
            brief=json.loads(brief_path.read_text(encoding="utf-8")) if brief_path.exists() else None,
            research=json.loads(research_packet.read_text(encoding="utf-8")) if research_packet.exists() else None,
            cost_usd=result["costs"]["total_with_research_share_usd"],
            error=result.get("error"),
            output_dir=str(out_dir),
            created_at=_parse_dt(result.get("started_at")),
            finished_at=_parse_dt(result.get("finished_at")),
        )
        session.add(run)
        plan_item = session.scalar(
            select(PlanItem).where(PlanItem.client_id == client.id, PlanItem.rationale.like(f"%benchmark:{topic_id}%"))
        )
        if plan_item is not None:
            plan_item.page_id = page.id
            plan_item.status = "done" if page.status == "approved" else "in_production"
        # Appels API (article + recherche du sujet)
        session.query(ApiCall).filter(ApiCall.page_id == page.id).delete()
        for scope in (f"article:{topic_id}:{profile}", f"research:{topic_id}"):
            for rec in calls_by_scope.get(scope, []):
                session.add(_api_call(client, page, rec))
        imported += 1
    return imported


def _template_for(topic_type: str | None) -> str:
    return {
        "technical_math": "technical_tutorial",
        "epfl": "pillar_guide",
        "maturite_official": "pillar_guide",
        "local_commercial": "educational_article",
        "learning_method": "educational_article",
    }.get(topic_type or "", "educational_article")


def _load_cost_log(path: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            out.setdefault(rec["scope"], []).append(rec)
    return out


def _api_call(client: Client, page: Page, rec: dict) -> ApiCall:
    usage = rec.get("usage") or {}
    return ApiCall(
        client_id=client.id,
        page_id=page.id,
        scope=rec["scope"],
        step=rec["step"],
        task=rec["task"],
        provider=rec["provider"],
        model=rec["model"],
        prompt_version=f"{rec.get('prompt_name')}@{rec.get('prompt_version')}",
        input_tokens=usage.get("input_tokens", 0),
        cached_input_tokens=usage.get("cached_input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        cost_usd=rec.get("cost_usd", 0.0),
        duration_s=rec.get("duration_s", 0.0),
        success=rec.get("success", True),
        error=rec.get("error"),
        created_at=_parse_dt(rec.get("timestamp")) or utcnow(),
    )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# --- Import de contenus (fichier) --------------------------------------------------------------


def import_pages(session: Session, client: Client, pages: list[providers.ImportedPage]) -> tuple[int, int]:
    """Crée ou met à jour les pages importées (clé : URL). Retourne (créées, mises à jour)."""
    created = updated = 0
    for imported in pages:
        page = session.scalar(select(Page).where(Page.client_id == client.id, Page.url == imported.url))
        if page is None:
            page = Page(client_id=client.id, url=imported.url, external_key=imported.url, origin="existing",
                        status="published", source="import")
            session.add(page)
            created += 1
        else:
            updated += 1
        page.title = imported.title
        page.h1 = imported.h1 or page.h1
        page.slug = imported.slug or page.slug
        page.page_type = imported.page_type or page.page_type
        page.published_at = imported.published_at or page.published_at
        page.word_count = imported.word_count or page.word_count
        if imported.content:
            session.flush()
            last = max((v.version_no for v in page.versions), default=0)
            version = PageVersion(page_id=page.id, version_no=last + 1, content_md=imported.content,
                                  change_type="import", reason="Import fichier", author="import")
            session.add(version)
            session.flush()
            page.current_version_id = version.id
    return created, updated


# --- Indicateurs -------------------------------------------------------------------------------


def month_bounds(today: date | None = None) -> tuple[datetime, datetime]:
    today = today or date.today()
    start = datetime(today.year, today.month, 1, tzinfo=timezone.utc)
    end = datetime(today.year + (today.month == 12), today.month % 12 + 1, 1, tzinfo=timezone.utc)
    return start, end


def month_cost(session: Session, client: Client) -> float:
    start, end = month_bounds()
    total = session.scalar(
        select(func.coalesce(func.sum(ApiCall.cost_usd), 0.0)).where(
            ApiCall.client_id == client.id, ApiCall.created_at >= start, ApiCall.created_at < end
        )
    )
    return float(total or 0.0)


def load_templates() -> dict[str, dict]:
    return yaml.safe_load((CONFIG_DIR / "templates.yaml").read_text(encoding="utf-8"))["templates"]
