"""Production lancée depuis l'interface : un élément CREATE approuvé → pipeline complet en arrière-plan.

Réutilise exactement le pipeline V0 (recherche, brief, rédaction, QA) avec le profil
`defaults.production_profile` de config/models.yaml, puis importe le résultat dans la base.
En V1 production, ce lancement passera par une file de jobs (Procrastinate) au lieu d'un thread.
"""

from __future__ import annotations

import logging
import threading

from sqlalchemy import select

from ..config import (
    DEFAULT_OUT,
    ConversionTarget,
    Topic,
    load_budgets,
    load_client,
    load_model_defaults,
    load_pricing,
    load_profiles,
    research_profile,
)
from ..llm import LLMRouter
from ..pipeline import ArticleRun
from ..research import build_research_packet
from ..search import WebSearchProvider
from .db import session_scope
from .models import Client, Page, PipelineRun, PlanItem, utcnow
from .services import import_pipeline_results

log = logging.getLogger(__name__)

TEMPLATE_TO_TOPIC_TYPE = {"technical_tutorial": "technical_math", "pillar_guide": "epfl", "local_service_page": "local_commercial"}


def _topic_for(item: PlanItem) -> Topic:
    segment = item.cluster.segment if item.cluster else None
    offer = (segment.offer_url if segment and segment.offer_url else None) or "https://phassyl.ch/contact/"
    return Topic(
        id=f"plan-{item.id}",
        type=TEMPLATE_TO_TOPIC_TYPE.get(item.template or "", "learning_method"),
        status="ready",
        title=item.title,
        primary_keyword=item.primary_keyword or item.title,
        secondary_keywords=[],
        intent="informational",
        audience=(segment.description if segment else "") or "",
        risk_level="standard",
        business_value=item.business_value,
        conversion_target=ConversionTarget(primary=offer, action="Prise de contact"),
        cannibalization_note=item.rationale or "",
    )


def start_production(plan_item_id: int) -> int:
    """Crée la page et l'exécution, puis lance le pipeline dans un thread. Retourne l'id de la page."""
    profile_name = load_model_defaults().production_profile
    with session_scope() as session:
        item = session.get(PlanItem, plan_item_id)
        if item is None or item.action != "CREATE" or item.status != "approved":
            raise ValueError("Seul un élément CREATE approuvé peut être produit")
        page = Page(client_id=item.client_id, external_key=f"pipeline:plan-{item.id}:{profile_name}", origin="new",
                    page_type="article", title=item.title, primary_keyword=item.primary_keyword,
                    cluster_id=item.cluster_id, template=item.template, status="in_production", source="pipeline")
        session.add(page)
        session.flush()
        session.add(PipelineRun(page_id=page.id, plan_item_id=item.id, profile=profile_name, status="running"))
        item.page_id, item.status = page.id, "in_production"
        page_id = page.id
    threading.Thread(target=_run, args=(plan_item_id, page_id, profile_name), daemon=True).start()
    return page_id


def _run(plan_item_id: int, page_id: int, profile_name: str) -> None:
    try:
        with session_scope() as session:
            item = session.get(PlanItem, plan_item_id)
            client = session.get(Client, item.client_id)
            topic = _topic_for(item)
            client_slug = client.slug
        ctx = load_client(client_slug)
        profiles, pricing, budgets = load_profiles(), load_pricing(), load_budgets()
        research_dir = DEFAULT_OUT / "research" / topic.id
        router = LLMRouter(research_profile(profiles), pricing, budgets)
        packet = build_research_packet(
            topic, ctx, WebSearchProvider(router, exclude_domains=[ctx.domain]), router, budgets, pricing,
            research_dir, cost_log=DEFAULT_OUT / "costs.jsonl",
        )
        ArticleRun(
            topic=topic, profile=profiles[profile_name], client=ctx, packet=packet, research_dir=research_dir,
            router=LLMRouter(profiles[profile_name], pricing, budgets), budgets=budgets, pricing=pricing,
            out_dir=DEFAULT_OUT / "articles" / topic.id / profile_name, research_share_usd=packet.cost_usd,
            cost_log=DEFAULT_OUT / "costs.jsonl",
        ).run()
        with session_scope() as session:
            client = session.get(Client, session.get(PlanItem, plan_item_id).client_id)
            session.query(PipelineRun).filter(PipelineRun.page_id == page_id, PipelineRun.status == "running").delete()
            import_pipeline_results(session, client, DEFAULT_OUT)
            page = session.get(Page, page_id)
            item = session.get(PlanItem, plan_item_id)
            page.cluster_id = item.cluster_id
            page.template = item.template or page.template
    except Exception as e:  # le statut d'échec doit toujours être visible dans l'interface
        log.exception("Production %s : échec", plan_item_id)
        with session_scope() as session:
            page = session.get(Page, page_id)
            page.status = "failed"
            for run in session.scalars(select(PipelineRun).where(PipelineRun.page_id == page_id, PipelineRun.status == "running")):
                run.status, run.error, run.finished_at = "failed", f"{type(e).__name__}: {e}", utcnow()


def recover_interrupted_runs() -> None:
    """Au démarrage : une exécution « running » a été interrompue par l'arrêt du serveur."""
    with session_scope() as session:
        for run in session.scalars(select(PipelineRun).where(PipelineRun.status == "running")):
            run.status, run.error, run.finished_at = "failed", "Interrompu (redémarrage du serveur)", utcnow()
            run.page.status = "failed"
