"""Cockpit SEO — application FastAPI (gabarits Jinja2 + HTMX, sans build front-end)."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Iterator
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .. import providers, qa
from ..config import load_model_defaults, load_profiles
from ..export import render_html
from . import auth, db, services, ui
from .models import (
    ApiCall,
    Client,
    Cluster,
    LinkSuggestion,
    Page,
    PageVersion,
    PipelineRun,
    PlanItem,
    Segment,
    SiteIssue,
    TargetTopic,
    User,
)

HERE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(HERE / "templates"))
ui.register(templates.env)

PUBLIC_PATHS = {"/login", "/healthz"}
PLAN_ACTIONS = ["CREATE", "UPDATE", "MERGE", "REWRITE", "SKIP"]
PAGE_ACTIONS = ["KEEP", "UPDATE", "MERGE", "REDIRECT", "REWRITE", "DELETE", "REPOSITION"]


class LoginRequired(Exception):
    pass


def create_app() -> FastAPI:
    load_dotenv()
    app = FastAPI(title="SEO OS", docs_url=None, redoc_url=None)
    import os

    app.add_middleware(
        SessionMiddleware,
        secret_key=auth.secret_key(),
        session_cookie="seo_os_session",
        same_site="strict",
        https_only=os.environ.get("SEO_OS_SECURE_COOKIES") == "1",
        max_age=60 * 60 * 12,
    )
    app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")

    @app.exception_handler(LoginRequired)
    async def _login_redirect(request: Request, exc: LoginRequired):
        if request.headers.get("HX-Request"):
            return Response(status_code=401, headers={"HX-Redirect": "/login"})
        return RedirectResponse("/login", status_code=303)

    _register_routes(app)
    return app


# --- Dépendances -------------------------------------------------------------------------------


def get_session() -> Iterator[Session]:
    with db.session_scope() as session:
        yield session


def current_user(request: Request, session: Session = Depends(get_session)) -> User:
    user_id = request.session.get("user_id")
    user = session.get(User, user_id) if user_id else None
    if user is None:
        raise LoginRequired()
    return user


async def check_csrf(request: Request) -> None:
    if request.method != "POST":
        return
    token = request.headers.get("X-CSRF-Token")
    if token is None:
        form = await request.form()
        token = form.get("csrf_token")
    if not auth.csrf_valid(request.session, token):
        raise HTTPException(status_code=403, detail="Jeton CSRF invalide — rechargez la page")


def current_client(session: Session) -> Client:
    client = session.scalar(select(Client).order_by(Client.id))
    if client is None:
        raise HTTPException(status_code=500, detail="Aucun client : lancez `seo-os seed --demo`")
    return client


def render(request: Request, name: str, session: Session, **context) -> HTMLResponse:
    client = context.get("client") or current_client(session)
    states = services.integration_states(session, client)
    connected, required = services.connected_count(states)
    base = {
        "request": request,
        "client": client,
        "csrf": auth.csrf_token(request.session),
        "demo_mode": services.is_demo_mode(states),
        "live_connected": connected,
        "live_required": required,
        "integrations": states,
        "nav_counts": _nav_counts(session, client),
    }
    base.update(context)
    return templates.TemplateResponse(request, name, base)


def _nav_counts(session: Session, client: Client) -> dict:
    review = session.scalar(select(func.count()).select_from(Page).where(
        Page.client_id == client.id, Page.status.in_(["ready_for_review", "needs_attention", "failed", "in_production"])))
    links = session.scalar(select(func.count()).select_from(LinkSuggestion).where(
        LinkSuggestion.client_id == client.id, LinkSuggestion.status == "suggested"))
    plan = session.scalar(select(func.count()).select_from(PlanItem).where(
        PlanItem.client_id == client.id, PlanItem.status == "proposed"))
    return {"review": review, "links": links, "plan": plan}


def _llm_ready(states: dict) -> bool:
    profile = load_profiles()[load_model_defaults().production_profile]
    needed = {spec.provider for spec in profile.tasks.values()}
    return all(states.get(p) is not None and states[p].status in ("connected", "configured") for p in needed)


def _segments(session: Session, client: Client) -> list[Segment]:
    return list(session.scalars(select(Segment).where(Segment.client_id == client.id).order_by(Segment.position)))


# --- Routes ------------------------------------------------------------------------------------


def _register_routes(app: FastAPI) -> None:  # noqa: C901 — un seul endroit pour toutes les vues
    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    # Authentification
    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request):
        return templates.TemplateResponse(request, "login.html", {"error": None, "csrf": auth.csrf_token(request.session)})

    @app.post("/login", dependencies=[Depends(check_csrf)])
    def login(request: Request, email: str = Form(...), password: str = Form(...), session: Session = Depends(get_session)):
        user = session.scalar(select(User).where(User.email == email.strip().lower()))
        if user is None or not auth.verify_password(password, user.password_hash):
            return templates.TemplateResponse(
                request, "login.html", {"error": "Identifiants incorrects", "csrf": auth.csrf_token(request.session)},
                status_code=401,
            )
        request.session.clear()
        request.session["user_id"] = user.id
        return RedirectResponse("/", status_code=303)

    @app.post("/logout", dependencies=[Depends(check_csrf)])
    def logout(request: Request):
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    # Overview
    @app.get("/", response_class=HTMLResponse)
    def overview(request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
        client = current_client(session)
        segments = _segments(session, client)
        groups = {g: services.group_coverage([s for s in segments if s.group == g]) for g in ("epfl", "hors_epfl")}
        pages = session.scalars(select(Page).where(Page.client_id == client.id)).all()
        existing = [p for p in pages if p.origin == "existing"]
        review_pages = [p for p in pages if p.status in ("ready_for_review", "needs_attention", "failed", "in_production")]
        to_review = [p for p in existing if p.recommended_action and p.recommended_action != "KEEP"]
        gaps = session.scalars(
            select(TargetTopic).join(Cluster).join(Segment)
            .where(Segment.client_id == client.id, TargetTopic.coverage_status == "gap", TargetTopic.page_id.is_(None))
            .order_by(TargetTopic.priority, Segment.priority)
        ).all()
        issues = session.scalars(select(SiteIssue).where(SiteIssue.client_id == client.id, SiteIssue.status == "open")
                                 .order_by(SiteIssue.severity)).all()
        plan_month = client.settings.get("plan_month")
        plan_items = session.scalars(select(PlanItem).where(PlanItem.client_id == client.id, PlanItem.month == plan_month)).all()
        return render(
            request, "overview.html", session, client=client, groups=groups, pages=pages, existing=existing,
            review_pages=review_pages, to_review=to_review, gaps=gaps,
            issues=sorted(issues, key=lambda i: ["high", "medium", "low"].index(i.severity)),
            link_count=session.scalar(select(func.count()).select_from(LinkSuggestion).where(
                LinkSuggestion.client_id == client.id, LinkSuggestion.status.in_(["suggested", "approved"]))),
            month_cost=services.month_cost(session, client), plan_month=plan_month,
            plan_counts=Counter(i.action for i in plan_items if i.status != "rejected"),
            new_this_month=sum(1 for p in pages if p.origin == "new"),
        )

    # Stratégie
    @app.get("/strategy", response_class=HTMLResponse)
    def strategy(request: Request, subject: str | None = None, session: Session = Depends(get_session),
                 user: User = Depends(current_user)):
        client = current_client(session)
        segments = _segments(session, client)
        visible: dict[int, list[Cluster]] = {
            s.id: [c for c in s.clusters if not subject or subject in (c.subjects or [])] for s in segments
        }
        groups = {}
        for g in ("epfl", "hors_epfl"):
            segs = [s for s in segments if s.group == g and visible[s.id]]
            cov = services.Coverage()
            for s in segs:
                for c in visible[s.id]:
                    cov.add(services.cluster_coverage(c))
            pages_known = sum(len([p for p in c.pages if p.origin == "existing"]) for s in segs for c in visible[s.id])
            groups[g] = {"segments": segs, "coverage": cov, "pages": pages_known}
        subjects = sorted({sub for s in segments for c in s.clusters for sub in (c.subjects or [])})
        return render(request, "strategy.html", session, client=client, groups=groups, visible=visible,
                      subject=subject, subjects=subjects, coverage=services.cluster_coverage,
                      seg_coverage=lambda s: _cov_of(visible[s.id]))

    def _cov_of(clusters: list[Cluster]) -> services.Coverage:
        cov = services.Coverage()
        for c in clusters:
            cov.add(services.cluster_coverage(c))
        return cov

    @app.get("/strategy/clusters/{cluster_id}", response_class=HTMLResponse)
    def cluster_panel(cluster_id: int, request: Request, session: Session = Depends(get_session),
                      user: User = Depends(current_user)):
        cluster = session.get(Cluster, cluster_id) or _404()
        return _cluster_panel(request, session, cluster)

    def _cluster_panel(request: Request, session: Session, cluster: Cluster, message: str | None = None):
        plan_topic_ids = {t for (t,) in session.execute(select(PlanItem.target_topic_id).where(
            PlanItem.target_topic_id.is_not(None), PlanItem.status != "rejected"))}
        return render(request, "_cluster_panel.html", session, cluster=cluster,
                      coverage=services.cluster_coverage(cluster), plan_topic_ids=plan_topic_ids, message=message)

    @app.post("/strategy/clusters/{cluster_id}", response_class=HTMLResponse, dependencies=[Depends(check_csrf)])
    def edit_cluster(cluster_id: int, request: Request, name: str = Form(...), business_value: str = Form(...),
                     priority: int = Form(...), session: Session = Depends(get_session), user: User = Depends(current_user)):
        cluster = session.get(Cluster, cluster_id) or _404()
        cluster.name, cluster.business_value, cluster.priority = name.strip(), business_value, priority
        cluster.source = "validated"
        return _cluster_panel(request, session, cluster, "Cluster enregistré")

    @app.post("/strategy/segments/{segment_id}", dependencies=[Depends(check_csrf)])
    def edit_segment(segment_id: int, name: str = Form(...), business_value: str = Form(...), priority: int = Form(...),
                     session: Session = Depends(get_session), user: User = Depends(current_user)):
        segment = session.get(Segment, segment_id) or _404()
        segment.name, segment.business_value, segment.priority, segment.source = name.strip(), business_value, priority, "validated"
        return RedirectResponse(f"/strategy#segment-{segment.id}", status_code=303)

    @app.post("/strategy/clusters/{cluster_id}/topics", response_class=HTMLResponse, dependencies=[Depends(check_csrf)])
    def add_topic(cluster_id: int, request: Request, title: str = Form(...), primary_keyword: str = Form(""),
                  session: Session = Depends(get_session), user: User = Depends(current_user)):
        cluster = session.get(Cluster, cluster_id) or _404()
        session.add(TargetTopic(cluster=cluster, title=title.strip(), primary_keyword=primary_keyword.strip() or None,
                                coverage_status="gap", business_value=cluster.business_value, priority=cluster.priority,
                                position=len(cluster.topics), source="validated"))
        session.flush()
        session.refresh(cluster)
        return _cluster_panel(request, session, cluster, "Sujet ajouté")

    @app.post("/strategy/topics/{topic_id}", response_class=HTMLResponse, dependencies=[Depends(check_csrf)])
    def edit_topic(topic_id: int, request: Request, coverage_status: str = Form(...), priority: int = Form(...),
                   business_value: str = Form(...), session: Session = Depends(get_session), user: User = Depends(current_user)):
        topic = session.get(TargetTopic, topic_id) or _404()
        topic.coverage_status, topic.priority, topic.business_value, topic.source = coverage_status, priority, business_value, "validated"
        return _cluster_panel(request, session, topic.cluster, "Sujet mis à jour")

    @app.post("/strategy/topics/{topic_id}/plan", response_class=HTMLResponse, dependencies=[Depends(check_csrf)])
    def topic_to_plan(topic_id: int, request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
        topic = session.get(TargetTopic, topic_id) or _404()
        client = current_client(session)
        action = "UPDATE" if topic.page_id and topic.coverage_status in ("partial", "cannibalized") else "CREATE"
        session.add(PlanItem(client_id=client.id, month=client.settings.get("plan_month"), action=action, title=topic.title,
                             primary_keyword=topic.primary_keyword, cluster_id=topic.cluster_id, page_id=topic.page_id,
                             target_topic_id=topic.id, business_value=topic.business_value,
                             rationale=f"Ajouté depuis la carte ({ui.COVERAGE_LABELS[topic.coverage_status].lower()})",
                             status="proposed", source="validated"))
        return _cluster_panel(request, session, topic.cluster, f"« {topic.title} » ajouté au plan")

    # Bibliothèque
    @app.get("/library", response_class=HTMLResponse)
    def library(request: Request, q: str = "", group: str = "", segment: str = "", page_type: str = "", origin: str = "",
                action: str = "", status: str = "", tab: str = "all", session: Session = Depends(get_session),
                user: User = Depends(current_user)):
        client = current_client(session)
        query = select(Page).where(Page.client_id == client.id).outerjoin(Cluster).outerjoin(Segment)
        if q:
            query = query.where(or_(Page.title.ilike(f"%{q}%"), Page.url.ilike(f"%{q}%")))
        if group:
            query = query.where(Segment.group == group)
        if segment:
            query = query.where(Segment.id == int(segment))
        if page_type:
            query = query.where(Page.page_type == page_type)
        if origin:
            query = query.where(Page.origin == origin)
        if action == "none":
            query = query.where(Page.recommended_action.is_(None))
        elif action:
            query = query.where(Page.recommended_action == action)
        if status:
            query = query.where(Page.status == status)
        if tab == "review":
            query = query.where(or_(Page.status.in_(["ready_for_review", "needs_attention"]),
                                    Page.recommended_action.in_(PAGE_ACTIONS[1:])))
        pages = session.scalars(query.order_by(Segment.position.is_(None), Segment.position, Cluster.position,
                                               Page.title)).unique().all()
        issues = session.scalars(select(SiteIssue).where(SiteIssue.client_id == client.id)).all()
        issues_by_url: dict[str, int] = defaultdict(int)
        for issue in issues:
            for url in issue.urls:
                issues_by_url[url] += 1
        return render(request, "library.html", session, client=client, pages=pages, segments=_segments(session, client),
                      filters=dict(q=q, group=group, segment=segment, page_type=page_type, origin=origin, action=action,
                                   status=status), tab=tab, issues=issues, issues_by_url=issues_by_url,
                      page_actions=PAGE_ACTIONS, total=session.scalar(select(func.count()).select_from(Page).where(
                          Page.client_id == client.id)), message=request.query_params.get("message"))

    @app.post("/library/bulk", dependencies=[Depends(check_csrf)])
    async def library_bulk(request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
        form = await request.form()
        ids = [int(i) for i in form.getlist("page_ids")]
        operation = form.get("operation")
        client = current_client(session)
        pages = session.scalars(select(Page).where(Page.id.in_(ids), Page.client_id == client.id)).all()
        if operation == "validate_action":
            for page in pages:
                if page.recommended_action:
                    page.action_source = "validated"
            message = f"{len(pages)} action(s) validée(s)"
        elif operation == "to_plan":
            for page in pages:
                act = page.recommended_action if page.recommended_action in PLAN_ACTIONS else "UPDATE"
                session.add(PlanItem(client_id=client.id, month=client.settings.get("plan_month"), action=act,
                                     title=page.title, primary_keyword=page.primary_keyword, page_id=page.id,
                                     cluster_id=page.cluster_id, template=page.template, rationale=page.action_rationale,
                                     status="proposed", source="validated"))
            message = f"{len(pages)} page(s) ajoutée(s) au plan"
        elif operation and operation.startswith("set:"):
            new_action = operation.removeprefix("set:")
            for page in pages:
                page.recommended_action, page.action_source = new_action or None, "validated"
            message = f"Action mise à jour pour {len(pages)} page(s)"
        else:
            message = "Aucune opération"
        return RedirectResponse(f"/library?message={message}", status_code=303)

    @app.post("/library/import", dependencies=[Depends(check_csrf)])
    async def library_import(file: UploadFile, session: Session = Depends(get_session), user: User = Depends(current_user)):
        data = await file.read()
        try:
            imported = providers.FileImportProvider(file.filename or "import.csv", data).pages()
        except (ValueError, UnicodeDecodeError) as e:
            return RedirectResponse(f"/library?message=Import impossible : {e}", status_code=303)
        created, updated = services.import_pages(session, current_client(session), imported)
        return RedirectResponse(f"/library?message=Import : {created} créée(s), {updated} mise(s) à jour", status_code=303)

    # Plan mensuel
    @app.get("/plan", response_class=HTMLResponse)
    def plan(request: Request, month: str | None = None, session: Session = Depends(get_session),
             user: User = Depends(current_user)):
        client = current_client(session)
        month = month or client.settings.get("plan_month")
        items = session.scalars(select(PlanItem).where(PlanItem.client_id == client.id, PlanItem.month == month)
                                .order_by(PlanItem.id)).all()
        by_action = {a: [i for i in items if i.action == a] for a in PLAN_ACTIONS}
        active = [i for i in items if i.status not in ("rejected", "postponed") and i.action != "SKIP"]
        return render(request, "plan.html", session, client=client, month=month, by_action=by_action, items=items,
                      planned=active, llm_ready=_llm_ready(services.integration_states(session, client)),
                      plan_actions=PLAN_ACTIONS, clusters=_all_clusters(session, client))

    def _plan_row(request: Request, session: Session, item: PlanItem, editing: bool = False, message: str | None = None):
        client = current_client(session)
        return render(request, "_plan_row.html", session, item=item, editing=editing, message=message,
                      llm_ready=_llm_ready(services.integration_states(session, client)), plan_actions=PLAN_ACTIONS,
                      clusters=_all_clusters(session, client))

    @app.get("/plan/{item_id}/edit", response_class=HTMLResponse)
    def plan_edit_form(item_id: int, request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
        return _plan_row(request, session, session.get(PlanItem, item_id) or _404(), editing=True)

    @app.get("/plan/{item_id}/row", response_class=HTMLResponse)
    def plan_row(item_id: int, request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
        return _plan_row(request, session, session.get(PlanItem, item_id) or _404())

    @app.post("/plan/{item_id}/edit", response_class=HTMLResponse, dependencies=[Depends(check_csrf)])
    def plan_edit(item_id: int, request: Request, title: str = Form(...), primary_keyword: str = Form(""),
                  action: str = Form(...), cluster_id: str = Form(""), business_value: str = Form(...),
                  session: Session = Depends(get_session), user: User = Depends(current_user)):
        item = session.get(PlanItem, item_id) or _404()
        item.title, item.primary_keyword, item.action = title.strip(), primary_keyword.strip() or None, action
        item.cluster_id = int(cluster_id) if cluster_id else None
        item.business_value, item.source = business_value, "validated"
        session.flush()
        session.refresh(item)
        return _plan_row(request, session, item, message="Enregistré")

    @app.post("/plan/{item_id}/status", response_class=HTMLResponse, dependencies=[Depends(check_csrf)])
    def plan_status(item_id: int, request: Request, status: str = Form(...), session: Session = Depends(get_session),
                    user: User = Depends(current_user)):
        item = session.get(PlanItem, item_id) or _404()
        if status not in ("proposed", "approved", "rejected", "postponed"):
            raise HTTPException(status_code=400)
        item.status = status
        if status == "approved":
            item.source = "validated"
        return _plan_row(request, session, item)

    @app.post("/plan/{item_id}/produce", response_class=HTMLResponse, dependencies=[Depends(check_csrf)])
    def plan_produce(item_id: int, request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
        from .production import start_production

        item = session.get(PlanItem, item_id) or _404()
        if not _llm_ready(services.integration_states(session, current_client(session))):
            return _plan_row(request, session, item, message="Fournisseur LLM non disponible")
        session.commit()
        try:
            start_production(item_id)
        except ValueError as e:
            return _plan_row(request, session, item, message=str(e))
        session.expire_all()
        return _plan_row(request, session, session.get(PlanItem, item_id), message="Production lancée")

    # Relecture
    @app.get("/review", response_class=HTMLResponse)
    def review(request: Request, status: str = "", risk: str = "", session: Session = Depends(get_session),
               user: User = Depends(current_user)):
        client = current_client(session)
        query = select(Page).where(Page.client_id == client.id, Page.origin == "new")
        if status:
            query = query.where(Page.status == status)
        if risk:
            query = query.where(Page.factual_risk == risk)
        pages = session.scalars(query.order_by(Page.updated_at.desc())).all()
        runs = session.scalars(select(PipelineRun).join(Page).where(Page.client_id == client.id)).all()
        last_run = {}
        for run in runs:
            last_run[run.page_id] = run
        all_new = session.scalars(select(Page).where(Page.client_id == client.id, Page.origin == "new")).all()
        return render(request, "review.html", session, client=client, pages=pages, last_run=last_run,
                      counts=Counter(p.status for p in all_new), filters=dict(status=status, risk=risk),
                      budgets=_budgets())

    # Fiche page
    @app.get("/pages/{page_id}", response_class=HTMLResponse)
    def page_detail(page_id: int, request: Request, tab: str = "content", edit: int = 0,
                    session: Session = Depends(get_session), user: User = Depends(current_user)):
        page = session.get(Page, page_id) or _404()
        return _page_view(request, session, page, tab, bool(edit), request.query_params.get("message"))

    def _page_view(request: Request, session: Session, page: Page, tab: str, editing: bool, message: str | None):
        client = current_client(session)
        version = session.get(PageVersion, page.current_version_id) if page.current_version_id else None
        run = page.runs[-1] if page.runs else None
        result = (run.result if run else None) or {}
        preview = _article_body(version.content_md, page) if version else None
        inbound = session.scalars(select(LinkSuggestion).where(LinkSuggestion.target_page_id == page.id)).all()
        outbound = session.scalars(select(LinkSuggestion).where(LinkSuggestion.source_page_id == page.id)).all()
        issues = [i for i in session.scalars(select(SiteIssue).where(SiteIssue.client_id == client.id)) if page.url in i.urls]
        calls = session.scalars(select(ApiCall).where(ApiCall.page_id == page.id).order_by(ApiCall.created_at)).all()
        steps: dict[str, dict] = {}
        for call in calls:
            s = steps.setdefault(call.step, {"cost": 0.0, "calls": 0, "duration": 0.0, "models": set()})
            s["cost"] += call.cost_usd
            s["calls"] += 1
            s["duration"] += call.duration_s
            s["models"].add(f"{call.provider}:{call.model}")
        topic = session.scalar(select(TargetTopic).where(TargetTopic.page_id == page.id))
        verdicts = ((result.get("qa") or {}).get("factcheck") or {}).get("verdicts", [])
        verdicts_sorted = sorted(verdicts, key=lambda v: (ui.VERDICT_ORDER.get(v["verdict"], 3), v.get("index", 0)))
        return render(request, "page.html", session, client=client, page=page, tab=tab, editing=editing,
                      version=version, run=run, result=result, preview=preview, inbound=inbound, outbound=outbound,
                      issues=issues, calls=calls, steps=sorted(steps.items(), key=lambda kv: -kv[1]["cost"]),
                      topic=topic, message=message, verdicts_sorted=verdicts_sorted,
                      templates_catalog=services.load_templates(), llm_ready=_llm_ready(services.integration_states(session, client)),
                      page_actions=PAGE_ACTIONS, meta_limits=dict(title=qa.TITLE_TAG_RANGE, meta=qa.META_DESCRIPTION_RANGE))

    @app.post("/pages/{page_id}/meta", dependencies=[Depends(check_csrf)])
    def page_meta(page_id: int, title_tag: str = Form(""), meta_description: str = Form(""), slug: str = Form(""),
                  template: str = Form(""), session: Session = Depends(get_session), user: User = Depends(current_user)):
        page = session.get(Page, page_id) or _404()
        page.title_tag, page.meta_description = title_tag.strip() or None, meta_description.strip() or None
        page.slug, page.template = slug.strip() or page.slug, template or page.template
        return RedirectResponse(f"/pages/{page_id}?tab=meta&message=Métadonnées enregistrées", status_code=303)

    @app.post("/pages/{page_id}/content", dependencies=[Depends(check_csrf)])
    def page_content(page_id: int, content_md: str = Form(...), reason: str = Form(""),
                     session: Session = Depends(get_session), user: User = Depends(current_user)):
        page = session.get(Page, page_id) or _404()
        last = max((v.version_no for v in page.versions), default=0)
        version = PageVersion(page_id=page.id, version_no=last + 1, content_md=content_md.replace("\r\n", "\n"),
                              change_type="manual_edit", reason=reason.strip() or "Édition manuelle", author=user.email)
        session.add(version)
        session.flush()
        page.current_version_id = version.id
        page.word_count = len(qa.body_words(version.content_md))
        return RedirectResponse(f"/pages/{page_id}?tab=content&message=Version {version.version_no} enregistrée", status_code=303)

    @app.post("/pages/{page_id}/status", dependencies=[Depends(check_csrf)])
    def page_status(page_id: int, status: str = Form(...), session: Session = Depends(get_session),
                    user: User = Depends(current_user)):
        page = session.get(Page, page_id) or _404()
        if status not in ("approved", "needs_attention", "ready_for_review"):
            raise HTTPException(status_code=400)
        page.status = status
        for item in session.scalars(select(PlanItem).where(PlanItem.page_id == page.id)):
            item.status = "done" if status == "approved" else "in_production"
        label = ui.PAGE_STATUS_LABELS[status]
        return RedirectResponse(f"/pages/{page_id}?message=Statut : {label}", status_code=303)

    @app.post("/pages/{page_id}/action", dependencies=[Depends(check_csrf)])
    def page_action(page_id: int, action: str = Form(""), session: Session = Depends(get_session),
                    user: User = Depends(current_user)):
        page = session.get(Page, page_id) or _404()
        page.recommended_action, page.action_source = action or None, "validated"
        return RedirectResponse(f"/pages/{page_id}?tab=audit&message=Action enregistrée", status_code=303)

    @app.get("/pages/{page_id}/export.{fmt}")
    def page_export(page_id: int, fmt: str, session: Session = Depends(get_session), user: User = Depends(current_user)):
        page = session.get(Page, page_id) or _404()
        version = session.get(PageVersion, page.current_version_id) if page.current_version_id else None
        if version is None:
            raise HTTPException(status_code=404, detail="Aucun contenu")
        name = page.slug or f"page-{page.id}"
        if fmt == "md":
            return PlainTextResponse(version.content_md, headers={"Content-Disposition": f'attachment; filename="{name}.md"'})
        if fmt == "html":
            return HTMLResponse(render_html(version.content_md, page.title_tag or page.title, page.meta_description or ""),
                                headers={"Content-Disposition": f'attachment; filename="{name}.html"'})
        if fmt == "json":
            payload = {"title": page.h1 or page.title, "slug": page.slug, "title_tag": page.title_tag,
                       "meta_description": page.meta_description, "template": page.template,
                       "cluster": page.cluster.name if page.cluster else None, "markdown": version.content_md,
                       "version": version.version_no}
            return Response(json.dumps(payload, ensure_ascii=False, indent=2), media_type="application/json",
                            headers={"Content-Disposition": f'attachment; filename="{name}.json"'})
        raise HTTPException(status_code=404)

    # Maillage
    @app.get("/links", response_class=HTMLResponse)
    def links(request: Request, status: str = "", session: Session = Depends(get_session), user: User = Depends(current_user)):
        client = current_client(session)
        query = select(LinkSuggestion).where(LinkSuggestion.client_id == client.id)
        if status:
            query = query.where(LinkSuggestion.status == status)
        rows = session.scalars(query.order_by(LinkSuggestion.score.desc())).all()
        all_rows = session.scalars(select(LinkSuggestion).where(LinkSuggestion.client_id == client.id)).all()
        return render(request, "links.html", session, client=client, rows=rows, counts=Counter(r.status for r in all_rows),
                      status=status, new_inbound=sum(1 for r in all_rows if r.target_page.origin == "new"))

    @app.post("/links/{link_id}/status", response_class=HTMLResponse, dependencies=[Depends(check_csrf)])
    def link_status(link_id: int, request: Request, status: str = Form(...), session: Session = Depends(get_session),
                    user: User = Depends(current_user)):
        link = session.get(LinkSuggestion, link_id) or _404()
        if status not in ("suggested", "approved", "rejected"):
            raise HTTPException(status_code=400)
        link.status = status
        return render(request, "_link_row.html", session, row=link)

    @app.post("/links/regenerate", dependencies=[Depends(check_csrf)])
    def links_regenerate(session: Session = Depends(get_session), user: User = Depends(current_user)):
        created = services.suggest_structural_links(session, current_client(session))
        return RedirectResponse(f"/links?created={created}", status_code=303)

    # Intégrations & coûts
    @app.get("/settings", response_class=HTMLResponse)
    def settings(request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
        client = current_client(session)
        calls = session.scalars(select(ApiCall).where(ApiCall.client_id == client.id).order_by(ApiCall.created_at.desc())).all()
        by_model, by_step, by_page, by_day = defaultdict(float), defaultdict(float), defaultdict(float), defaultdict(float)
        for call in calls:
            by_model[f"{call.provider}:{call.model}"] += call.cost_usd
            by_step[call.step] += call.cost_usd
            by_day[call.created_at.date().isoformat()] += call.cost_usd
            if call.page_id:
                by_page[call.page_id] += call.cost_usd
        page_titles = {p.id: p.title for p in session.scalars(select(Page).where(Page.id.in_(list(by_page) or [0])))}
        runs = session.scalars(select(PipelineRun).join(Page).where(Page.client_id == client.id)
                               .order_by(PipelineRun.created_at.desc())).all()
        defaults = load_model_defaults()
        profile = load_profiles()[defaults.production_profile]
        return render(request, "settings.html", session, client=client, specs=services.INTEGRATIONS, calls=calls[:30],
                      total=sum(c.cost_usd for c in calls), month_cost=services.month_cost(session, client),
                      by_model=sorted(by_model.items(), key=lambda x: -x[1]),
                      by_step=sorted(by_step.items(), key=lambda x: -x[1]),
                      by_page=sorted(((page_titles.get(k, k), v, k) for k, v in by_page.items()), key=lambda x: -x[1]),
                      by_day=sorted(by_day.items()), runs=runs, defaults=defaults,
                      profile_tasks=sorted(profile.tasks.items()), failed_calls=sum(1 for c in calls if not c.success))

    @app.post("/settings/integrations/{kind}/test", response_class=HTMLResponse, dependencies=[Depends(check_csrf)])
    def integration_test(kind: str, request: Request, session: Session = Depends(get_session), user: User = Depends(current_user)):
        if kind not in services.SPEC_BY_KIND:
            raise HTTPException(status_code=404)
        client = current_client(session)
        services.refresh_integrations(session, client, live=True, only=kind)
        session.flush()
        states = services.integration_states(session, client)
        return render(request, "_integration_card.html", session, spec=services.SPEC_BY_KIND[kind], state=states.get(kind))


def _all_clusters(session: Session, client: Client) -> list[Cluster]:
    return list(session.scalars(select(Cluster).join(Segment).where(Segment.client_id == client.id)
                                .order_by(Segment.position, Cluster.position)))


def _article_body(markdown_text: str, page: Page) -> str:
    html = render_html(markdown_text, page.title_tag or page.title, page.meta_description or "")
    start, end = html.find("<article>"), html.find("</article>")
    return html[start + len("<article>"):end] if start != -1 else html


def _budgets():
    from ..config import load_budgets

    return load_budgets()


def _404():
    raise HTTPException(status_code=404, detail="Introuvable")
