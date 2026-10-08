import json
from datetime import date

import pytest

from seo_os import benchmark
from seo_os.config import research_profile
from seo_os.export import render_html
from seo_os.fetch import FetchedPage
from seo_os.llm import LLMRouter
from seo_os.pipeline import ArticleRun
from seo_os.prompts import load_prompt
from seo_os.research import build_research_packet, load_packet
from seo_os.search import CombinedSearchProvider, ManualUrlsProvider, WebSearchProvider

from .conftest import FakeProvider, make_brief

SOURCE_TEXT = "Les valeurs propres font partie du programme d'algèbre linéaire de première année. " * 10


@pytest.fixture
def research_dir(tmp_path, monkeypatch, topic, client, profiles, pricing, budgets):
    monkeypatch.setattr(
        "seo_os.research.fetch_page",
        lambda url: FetchedPage(url=url, ok=True, final_url=url, title="Source", text=SOURCE_TEXT, headings=["H2: Programme"]),
    )
    fake = FakeProvider()
    router = LLMRouter(research_profile(profiles), pricing, budgets, providers={"openai": fake, "anthropic": fake})
    provider = CombinedSearchProvider([ManualUrlsProvider(), WebSearchProvider(router, exclude_domains=["phassyl.ch"])])
    out = tmp_path / "research" / topic.id
    build_research_packet(topic, client, provider, router, budgets, pricing, out, cost_log=tmp_path / "costs.jsonl")
    return out


def test_research_packet_keeps_only_verifiable_quotes(research_dir):
    packet = load_packet(research_dir)
    assert [s.origin for s in packet.sources][0] == "manual"
    assert any(s.is_preferred_domain for s in packet.sources)
    assert all(s.relevant for s in packet.sources)
    assert {c.quote_verified for c in packet.claims} == {True, False}
    assert packet.cost_usd > 0
    assert (research_dir / "sources" / "S1.txt").exists()


def _run(tmp_path, research_dir, topic, client, profiles, pricing, budgets, fake, profile="B", **budget_overrides):
    budgets = budgets.__class__(**{**budgets.__dict__, **budget_overrides})
    packet = load_packet(research_dir)
    router = LLMRouter(profiles[profile], pricing, budgets, providers={"openai": fake, "anthropic": fake})
    return ArticleRun(
        topic=topic,
        profile=profiles[profile],
        client=client,
        packet=packet,
        research_dir=research_dir,
        router=router,
        budgets=budgets,
        pricing=pricing,
        out_dir=tmp_path / "articles" / topic.id / profile,
        research_share_usd=packet.cost_usd / 3,
        cost_log=tmp_path / "costs.jsonl",
    ).run()


def test_full_article_run_produces_outputs(tmp_path, research_dir, topic, client, profiles, pricing, budgets):
    fake = FakeProvider()
    result = _run(tmp_path, research_dir, topic, client, profiles, pricing, budgets, fake)
    out = tmp_path / "articles" / topic.id / "B"
    assert result["status"] == "ready_for_review", result["qa"]["deterministic"]["failed_high"]
    for name in ("article.md", "article.html", "article.json", "brief.json", "result.json", "article_v1.md"):
        assert (out / name).exists()
    assert result["config"]["models"]["write"] == "anthropic:claude-sonnet-5-5"
    assert result["metrics"]["claims_marked"] == 1 and result["metrics"]["claims_supported"] == 1
    assert result["qa"]["math"]["exercises_ok"] == 1
    assert set(result["costs"]["by_step"]) >= {"brief", "write", "metadata", "factcheck", "review", "math_extract"}
    assert result["costs"]["total_with_research_share_usd"] > result["costs"]["article_usd"] > 0
    assert result["human_review"]["review_minutes"] is None
    assert all("@v1-" in p for p in result["prompt_versions"])
    article_lines = [l for l in (tmp_path / "costs.jsonl").read_text().splitlines() if '"scope": "article:' in l]
    assert len(article_lines) == len(fake.calls)


def test_wrong_math_triggers_one_rewrite_then_attention(tmp_path, research_dir, topic, client, profiles, pricing, budgets):
    fake = FakeProvider(eigenvalues=("2", "4"))
    result = _run(tmp_path, research_dir, topic, client, profiles, pricing, budgets, fake)
    assert fake.calls.count("rewrite") == 1
    assert result["status"] == "needs_attention"
    assert result["attention_reasons"][0] == "rewrite_limit_reached"
    assert [v["version"] for v in result["versions"]] == [1, 2]


def test_budget_exceeded_stops_run(tmp_path, research_dir, topic, client, profiles, pricing, budgets):
    fake = FakeProvider()
    result = _run(tmp_path, research_dir, topic, client, profiles, pricing, budgets, fake, article_hard_usd=0.01)
    assert result["status"] == "needs_attention"
    assert result["attention_reasons"][0] == "budget_exceeded"
    assert fake.calls == []


def test_review_and_report(tmp_path, research_dir, topic, client, profiles, pricing, budgets):
    for profile in ("A", "B"):
        _run(tmp_path, research_dir, topic, client, profiles, pricing, budgets, FakeProvider(), profile=profile)
    benchmark.record_review(tmp_path, topic.id, "A", 20, 9, 2, 6, True, None)
    benchmark.record_review(tmp_path, topic.id, "B", 4, 2, 0, 9, True, "très bon")
    budgets_one = budgets.__class__(**{**budgets.__dict__, "deliverable_target": 1})
    report = benchmark.build_report(tmp_path, budgets_one)
    assert "**B**" in report
    stored = json.loads((tmp_path / "articles" / topic.id / "B" / "result.json").read_text())
    assert stored["human_review"]["review_minutes"] == 4


def test_all_prompts_render(topic, client, research_dir):
    packet = load_packet(research_dir)
    context = {
        "bible": client.bible_md,
        "topic": topic,
        "pages": client.pages,
        "sources": packet.usable_sources(),
        "claims": packet.verified_claims(),
        "today": date.today().isoformat(),
        "brief": make_brief(),
        "article": "# Titre\n\nTexte [S1].",
        "issues": ["[QA h1_unique] 0 H1"],
        "failed_checks": [{"name": "h1_unique", "severity": "high", "detail": "0 H1"}],
        "facts": {"claims_marked": 1, "supported": 1, "partial": 0, "unsupported": 0, "unverified_markers": 0},
        "units": [{"text": "Texte.", "source_ids": ["S1"], "evidence": [{"source_id": "S1", "claims": [], "passages": ["x"]}]}],
        "source": packet.sources[0],
        "source_text": SOURCE_TEXT,
        "count": 5,
        "official_only": True,
    }
    for name in ("search", "extract_claims", "brief", "write", "rewrite", "metadata", "factcheck", "review", "math_extract"):
        system, user = load_prompt(name).render(**context)
        assert system and user, name


def test_html_export_strips_markers_and_keeps_latex():
    html = render_html("# T\n\nUn fait [S1, S2]. Une formule $a_1 + a_2$. Reste [À VÉRIFIER].", "T", "D")
    assert "[S1" not in html and "$a_1 + a_2$" in html and "<mark>[À VÉRIFIER]</mark>" in html


def test_pipeline_output_renders_in_cockpit(tmp_path, research_dir, topic, client, profiles, pricing, budgets, monkeypatch):
    import re

    from fastapi.testclient import TestClient
    from sqlalchemy import select

    from seo_os.web import db, migrate
    from seo_os.web.auth import hash_password
    from seo_os.web.models import ApiCall, Page, User
    from seo_os.web.seed import seed_demo

    # le sujet du fixture devient un sujet « benchmark » connu de la carte
    _run(tmp_path, research_dir, topic, client, profiles, pricing, budgets, FakeProvider(), profile="D")
    url = f"sqlite:///{tmp_path / 'cockpit.db'}"
    monkeypatch.setenv("SEO_OS_SECRET_KEY", "t")
    monkeypatch.setattr("seo_os.web.app.load_dotenv", lambda: None)
    db.configure(url)
    migrate.upgrade(url)
    with db.session_scope() as session:
        seed_demo(session, out_root=tmp_path, demo_root=None)
        session.add(User(email="a@b.c", password_hash=hash_password("motdepasse-123")))
    with db.session_scope() as session:
        page = session.scalar(select(Page).where(Page.origin == "new"))
        assert page.cluster is not None and page.cluster.name == "Algèbre linéaire"
        assert len(page.versions) == 1 and session.scalar(select(ApiCall).where(ApiCall.page_id == page.id))
        page_id = page.id

    from seo_os.web.app import create_app

    web = TestClient(create_app())
    token = re.search(r'name="csrf_token" value="([^"]+)"', web.get("/login").text).group(1)
    web.post("/login", data={"email": "a@b.c", "password": "motdepasse-123", "csrf_token": token})
    for tab in ("content", "brief", "sources", "qa", "meta", "links", "perf", "history"):
        resp = web.get(f"/pages/{page_id}?tab={tab}")
        assert resp.status_code == 200, (tab, resp.text[:300])
    assert "Soutenue" in web.get(f"/pages/{page_id}?tab=sources").text
    assert web.get(f"/pages/{page_id}/export.json").json()["markdown"].startswith("# ")
    assert web.get("/review").status_code == 200
