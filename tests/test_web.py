import re

import pytest
from sqlalchemy import select

from seo_os.web import db, migrate
from seo_os.web.auth import hash_password, verify_password
from seo_os.web.models import Client, LinkSuggestion, Page, PlanItem, TargetTopic, User
from seo_os.web.seed import seed_demo
from seo_os.web.services import Coverage

PASSWORD = "mot-de-passe-test"


@pytest.fixture
def web(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("SEO_OS_SECRET_KEY", "test-secret")
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TREG_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr("seo_os.web.app.load_dotenv", lambda: None)
    db.configure(url)
    migrate.upgrade(url)
    with db.session_scope() as session:
        seed_demo(session, out_root=tmp_path / "out", demo_root=None)  # sans résultats pipeline
        session.add(User(email="me@example.com", password_hash=hash_password(PASSWORD)))
    from seo_os.web.app import create_app

    client = TestClient(create_app())
    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
    resp = client.post("/login", data={"email": "me@example.com", "password": PASSWORD, "csrf_token": token},
                       follow_redirects=False)
    assert resp.status_code == 303
    # la connexion régénère la session (et le jeton CSRF) : on reprend celui de la page suivante
    home = client.get("/")
    client.headers["X-CSRF-Token"] = re.search(r'"X-CSRF-Token": "([^"]+)"', home.text).group(1)
    return client


def test_password_hashing():
    stored = hash_password("secret-123456")
    assert verify_password("secret-123456", stored) and not verify_password("autre", stored)


def test_login_required(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    url = f"sqlite:///{tmp_path / 'auth.db'}"
    monkeypatch.setenv("SEO_OS_SECRET_KEY", "x")
    db.configure(url)
    migrate.upgrade(url)
    from seo_os.web.app import create_app

    client = TestClient(create_app())
    assert client.get("/", follow_redirects=False).headers["location"] == "/login"
    assert client.get("/strategy", headers={"HX-Request": "true"}).headers.get("HX-Redirect") == "/login"


def test_post_without_csrf_is_rejected(web):
    del web.headers["X-CSRF-Token"]
    assert web.post("/links/regenerate").status_code == 403


@pytest.mark.parametrize("path", ["/", "/strategy", "/strategy?subject=maths", "/library", "/library?tab=review",
                                  "/library?tab=issues", "/library?action=none", "/plan", "/review", "/links", "/settings"])
def test_screens_render(web, path):
    resp = web.get(path)
    assert resp.status_code == 200, resp.text[:500]
    assert "MODE DÉMO" in resp.text


def test_no_fake_performance_numbers(web):
    html = web.get("/").text
    assert "En attente de connexion Search Console" in html
    assert "%" not in html.split("Performance organique")[1].split("Stratégie")[0]


def test_strategy_panel_and_edits(web):
    with db.session_scope() as session:
        topic = session.scalar(select(TargetTopic).where(TargetTopic.coverage_status == "gap"))
        cluster_id, topic_id = topic.cluster_id, topic.id
    panel = web.get(f"/strategy/clusters/{cluster_id}")
    assert panel.status_code == 200 and "Sujets cibles" in panel.text
    resp = web.post(f"/strategy/topics/{topic_id}", data={"coverage_status": "partial", "priority": 1, "business_value": "high"})
    assert "Sujet mis à jour" in resp.text
    resp = web.post(f"/strategy/topics/{topic_id}/plan")
    assert "ajouté au plan" in resp.text
    resp = web.post(f"/strategy/clusters/{cluster_id}/topics", data={"title": "Nouveau sujet", "primary_keyword": "kw"})
    assert "Nouveau sujet" in resp.text
    with db.session_scope() as session:
        assert session.get(TargetTopic, topic_id).source == "validated"
        assert session.scalar(select(PlanItem).where(PlanItem.target_topic_id == topic_id)) is not None


def test_plan_counter_counts_planned_items(web):
    with db.session_scope() as session:
        expected = len([i for i in session.scalars(select(PlanItem))
                        if i.status not in ("rejected", "postponed") and i.action != "SKIP"])
    assert f'font-weight:750">{expected} <span' in web.get("/plan").text


def test_plan_workflow(web):
    with db.session_scope() as session:
        item_id = session.scalar(select(PlanItem.id).where(PlanItem.status == "proposed"))
    assert "Approuvé" in web.post(f"/plan/{item_id}/status", data={"status": "approved"}).text
    assert "Reporté" in web.post(f"/plan/{item_id}/status", data={"status": "postponed"}).text
    assert web.get(f"/plan/{item_id}/edit").status_code == 200
    resp = web.post(f"/plan/{item_id}/edit", data={"title": "Titre modifié", "primary_keyword": "kw", "action": "UPDATE",
                                                   "cluster_id": "", "business_value": "low"})
    assert "Titre modifié" in resp.text
    assert web.post(f"/plan/{item_id}/status", data={"status": "bogus"}).status_code == 400


def test_production_disabled_without_llm(web):
    with db.session_scope() as session:
        item_id = session.scalar(select(PlanItem.id).where(PlanItem.action == "CREATE", PlanItem.status == "approved"))
    assert "Fournisseur LLM non disponible" in web.post(f"/plan/{item_id}/produce").text


def test_library_bulk_and_import(web):
    with db.session_scope() as session:
        ids = [p for (p,) in session.execute(select(Page.id).where(Page.recommended_action.is_not(None)).limit(2))]
    resp = web.post("/library/bulk", data={"page_ids": ids, "operation": "validate_action"}, follow_redirects=False)
    assert resp.status_code == 303
    csv_data = "url,title,word_count\nhttps://phassyl.ch/nouvel-article/,Nouvel article,850\nhttps://phassyl.ch/admission-epfl/,Admission EPFL,1200\n"
    resp = web.post("/library/import", files={"file": ("export.csv", csv_data, "text/csv")}, follow_redirects=True)
    assert "1 créée(s), 1 mise(s) à jour" in resp.text
    with db.session_scope() as session:
        assert all(session.get(Page, i).action_source == "validated" for i in ids)


def test_links_and_page_detail(web):
    with db.session_scope() as session:
        link = session.scalar(select(LinkSuggestion))
        page = session.scalar(select(Page).where(Page.recommended_action == "MERGE"))
        link_id, page_id = link.id, page.id
        # les pages vouées à être fusionnées ne reçoivent ni n'émettent de suggestions
        assert session.scalar(select(LinkSuggestion).where(
            (LinkSuggestion.source_page_id == page_id) | (LinkSuggestion.target_page_id == page_id))) is None
    assert "Approuvé" in web.post(f"/links/{link_id}/status", data={"status": "approved"}).text
    for tab in ("audit", "content", "meta", "links", "perf"):
        assert web.get(f"/pages/{page_id}?tab={tab}").status_code == 200
    resp = web.post(f"/pages/{page_id}/meta", data={"title_tag": "Titre", "meta_description": "Desc", "slug": "s", "template": ""},
                    follow_redirects=True)
    assert "Métadonnées enregistrées" in resp.text


def test_coverage_math():
    cov = Coverage(covered=2, partial=1, cannibalized=1, gap=4)
    assert cov.total == 8 and cov.pct == 38 and round(cov.share("covered")) == 25
    assert Coverage().pct is None


def test_seed_is_honest(web):
    with db.session_scope() as session:
        client = session.scalar(select(Client))
        assert client.announced_content_count == "300–400"
        pages = session.scalars(select(Page)).all()
        assert {p.source for p in pages} <= {"public", "import", "pipeline"}
        topics = session.scalars(select(TargetTopic)).all()
        assert all(t.search_volume is None for t in topics)  # aucun volume inventé


def test_versioned_demo_articles_are_imported(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'demo.db'}"
    db.configure(url)
    migrate.upgrade(url)
    from seo_os.web.seed import DEMO_DIR

    with db.session_scope() as session:
        seed_demo(session, out_root=DEMO_DIR)  # mêmes résultats dans demo/ et out/ : réimport sans erreur
    with db.session_scope() as session:
        new_pages = session.scalars(select(Page).where(Page.origin == "new")).all()
        assert len(new_pages) == 3
        assert all(p.cluster is not None and p.current_version_id for p in new_pages)
