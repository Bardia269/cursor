"""Pipeline d'un article pour un sujet et un profil de modèles.

brief → rédaction → métadonnées → QA déterministe → fact-check → revue IA → (réécriture) → export
"""

from __future__ import annotations

import json
import logging
import re
import time
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from . import qa
from .config import Budgets, ClientContext, Pricing, Profile, Topic
from .costs import BudgetExceeded, CostTracker, now_iso
from .export import ArticleExport, ExportProvider
from .llm import LLMError, LLMRouter
from .mathcheck import check_exercises
from .prompts import load_prompt
from .research import source_text
from .schemas import Brief, FactCheckResult, MathExtraction, Metadata, ResearchPacket, Review

log = logging.getLogger(__name__)

MAX_FACTCHECK_UNITS = 40
PASSAGES_PER_SOURCE = 2
PASSAGE_MAX_CHARS = 900
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÀ-Ý«\"(])")
ACTION_PRIORITY = {"RESEARCH_REQUIRED": 3, "REWRITE": 2, "HUMAN_REVIEW": 1, "PASS": 0}


def empty_human_review() -> dict:
    return {
        "review_minutes": None,
        "corrections_count": None,
        "sections_rewritten": None,
        "human_score": None,      # note finale /10
        "deliverable": None,      # true / false
        "notes": None,
        "reviewed_at": None,
    }


def marked_units(markdown: str) -> list[dict]:
    """Phrases (ou éléments de liste) portant au moins un marqueur [S#]."""
    units = []
    for line in markdown.splitlines():
        if not qa.SOURCE_MARKER_RE.search(line):
            continue
        for sentence in SENTENCE_SPLIT_RE.split(line.strip().lstrip("-*0123456789. ")):
            ids = qa.source_markers(sentence)
            if ids:
                units.append({"text": qa.strip_markers(sentence).strip(), "source_ids": ids})
    return units[:MAX_FACTCHECK_UNITS]


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[\wÀ-ÿ]+", text.lower()) if len(t) > 3}


def best_passages(text: str, query: str, k: int = PASSAGES_PER_SOURCE) -> list[str]:
    """Passages de la source les plus proches de la phrase (recouvrement lexical, sans IA)."""
    q = _tokens(query)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 40]
    scored = sorted(paragraphs, key=lambda p: len(q & _tokens(p)), reverse=True)
    return [p[:PASSAGE_MAX_CHARS] for p in scored[:k]]


class ArticleRun:
    def __init__(
        self,
        topic: Topic,
        profile: Profile,
        client: ClientContext,
        packet: ResearchPacket,
        research_dir: Path,
        router: LLMRouter,
        budgets: Budgets,
        pricing: Pricing,
        out_dir: Path,
        research_share_usd: float,
        cost_log: Path | None = None,
    ):
        self.topic = topic
        self.profile = profile
        self.client = client
        self.packet = packet
        self.research_dir = research_dir
        self.router = router
        self.budgets = budgets
        self.out_dir = out_dir
        self.research_share_usd = research_share_usd
        self.tracker = CostTracker(
            scope=f"article:{topic.id}:{profile.name}",
            pricing=pricing,
            hard_usd=budgets.article_hard_usd,
            alert_usd=budgets.article_alert_usd,
            log_path=cost_log,
        )
        self.durations: dict[str, float] = {}
        self.sources = packet.usable_sources()
        self.claims = [c for c in packet.verified_claims() if c.source_id in {s.id for s in self.sources}]
        self.versions: list[dict] = []

    # -- utilitaires --------------------------------------------------------------------------

    @contextmanager
    def _timed(self, step: str):
        started = time.perf_counter()
        try:
            yield
        finally:
            self.durations[step] = round(self.durations.get(step, 0.0) + time.perf_counter() - started, 2)

    def _context(self, **extra) -> dict:
        return {
            "bible": self.client.bible_md,
            "topic": self.topic,
            "pages": self.client.pages,
            "sources": self.sources,
            "claims": self.claims,
            "today": date.today().isoformat(),
            **extra,
        }

    def _save_version(self, markdown: str, change_type: str, reason: str, task: str) -> None:
        number = len(self.versions) + 1
        filename = f"article_v{number}.md"
        (self.out_dir / filename).write_text(markdown, encoding="utf-8")
        spec = self.profile.spec(task)
        cost_before = sum(v["cost_usd_cumulative"] for v in self.versions[-1:]) if self.versions else 0.0
        self.versions.append(
            {
                "version": number,
                "file": filename,
                "created_at": now_iso(),
                "change_type": change_type,
                "reason": reason,
                "model": spec.label,
                "cost_usd_cumulative": self.tracker.total_usd,
                "cost_usd_delta": round(self.tracker.total_usd - cost_before, 6),
            }
        )

    # -- étapes -------------------------------------------------------------------------------

    def brief(self) -> Brief:
        with self._timed("brief"):
            result = self.router.generate(
                self.tracker, "brief", load_prompt("brief"), self._context(), schema=Brief
            )
        brief: Brief = result.parsed  # type: ignore[assignment]
        (self.out_dir / "brief.json").write_text(
            json.dumps(brief.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return brief

    def write(self, brief: Brief) -> str:
        with self._timed("write"):
            result = self.router.generate(self.tracker, "write", load_prompt("write"), self._context(brief=brief))
        return result.text.strip()

    def metadata(self, brief: Brief, markdown: str) -> Metadata:
        with self._timed("metadata"):
            result = self.router.generate(
                self.tracker,
                "metadata",
                load_prompt("metadata"),
                self._context(brief=brief, article=markdown),
                schema=Metadata,
            )
        return result.parsed  # type: ignore[return-value]

    def factcheck(self, markdown: str) -> dict:
        units = marked_units(markdown)
        report = {
            "claims_marked": len(units),
            "supported": 0,
            "partial": 0,
            "unsupported": 0,
            "unverified_markers": markdown.count(qa.UNVERIFIED_MARKER),
            "verdicts": [],
        }
        if not units:
            return report
        claims_by_source: dict[str, list] = {}
        for c in self.claims:
            claims_by_source.setdefault(c.source_id, []).append(c)
        for unit in units:
            unit["evidence"] = [
                {
                    "source_id": sid,
                    "claims": [{"statement": c.statement, "quote": c.quote} for c in claims_by_source.get(sid, [])][:6],
                    "passages": best_passages(source_text(self.research_dir, sid), unit["text"]),
                }
                for sid in unit["source_ids"]
            ]
        with self._timed("factcheck"):
            result = self.router.generate(
                self.tracker,
                "factcheck",
                load_prompt("factcheck"),
                {"units": units, "topic": self.topic},
                schema=FactCheckResult,
            )
        parsed: FactCheckResult = result.parsed  # type: ignore[assignment]
        for v in parsed.verdicts:
            if 0 <= v.index < len(units):
                report[v.verdict] += 1
                report["verdicts"].append(
                    {"sentence": units[v.index]["text"], "sources": units[v.index]["source_ids"], **v.model_dump()}
                )
        return report

    def review(self, brief: Brief, markdown: str, checks: dict, facts: dict) -> Review:
        with self._timed("review"):
            result = self.router.generate(
                self.tracker,
                "review",
                load_prompt("review"),
                self._context(
                    brief=brief,
                    article=markdown,
                    failed_checks=[c for c in checks["checks"] if not c["passed"]],
                    facts=facts,
                ),
                schema=Review,
            )
        return result.parsed  # type: ignore[return-value]

    def math(self, markdown: str) -> dict | None:
        if "python_math_verification" not in self.topic.checks:
            return None
        with self._timed("math_check"):
            result = self.router.generate(
                self.tracker,
                "math_extract",
                load_prompt("math_extract"),
                {"article": markdown},
                schema=MathExtraction,
            )
            return check_exercises(result.parsed.exercises)  # type: ignore[union-attr]

    def rewrite(self, brief: Brief, markdown: str, issues: list[str]) -> str:
        with self._timed("rewrite"):
            result = self.router.generate(
                self.tracker,
                "rewrite",
                load_prompt("rewrite"),
                self._context(brief=brief, article=markdown, issues=issues),
            )
        return result.text.strip()

    # -- décision -----------------------------------------------------------------------------

    def decide(self, checks: dict, facts: dict, review: Review, math: dict | None) -> tuple[str, list[str], list[str]]:
        """Retourne (action, problèmes à corriger par réécriture, raisons d'attention humaine)."""
        actions = [review.recommended_action]
        fixes: list[str] = []
        attention: list[str] = []

        for c in checks["checks"]:
            if not c["passed"] and c["severity"] in ("high", "medium"):
                fixes.append(f"[QA {c['name']}] {c['detail']}")
        if checks["failed_high"]:
            actions.append("REWRITE")
        for v in facts["verdicts"]:
            if v["verdict"] == "unsupported":
                fixes.append(
                    f"[FACT non soutenu par {', '.join(v['sources'])}] « {v['sentence']} » — {v['explanation']}"
                )
        if facts["unsupported"]:
            actions.append("REWRITE")
        if facts["unverified_markers"]:
            attention.append(f"{facts['unverified_markers']} affirmation(s) [À VÉRIFIER] à compléter")
            actions.append("HUMAN_REVIEW")
        for issue in review.issues:
            if issue.severity in ("high", "medium"):
                fixes.append(f"[{issue.category}] {issue.location} : {issue.description} → {issue.suggestion}")
        if math is not None and math["exercises_ok"] < math["exercises_checked"]:
            actions.append("REWRITE")
            for ex in math["details"]:
                for err in ex["errors"]:
                    fixes.append(f"[MATH {ex['label']}] {err}")
        if self.topic.strict_sourcing and not self.sources:
            actions.append("RESEARCH_REQUIRED")
        if self.topic.risk_level == "sensitive":
            attention.append("sujet sensible : relecture humaine obligatoire")
            actions.append("HUMAN_REVIEW")
        return max(actions, key=ACTION_PRIORITY.__getitem__), fixes, attention

    # -- orchestration ------------------------------------------------------------------------

    def run(self) -> dict:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        result: dict = {
            "topic": {
                "id": self.topic.id,
                "title": self.topic.title,
                "type": self.topic.type,
                "primary_keyword": self.topic.primary_keyword,
                "risk_level": self.topic.risk_level,
                "business_value": self.topic.business_value,
                "conversion_target": self.topic.conversion_target.__dict__,
            },
            "config": {
                "profile": self.profile.name,
                "description": self.profile.description,
                "models": self.profile.models_summary(),
            },
            "started_at": now_iso(),
            "status": "running",
            "attention_reasons": [],
            "error": None,
            "human_review": empty_human_review(),
        }
        brief = metadata = None
        markdown = ""
        checks: dict = {}
        facts: dict = {}
        review: Review | None = None
        math: dict | None = None
        action = None
        rewrites = 0
        try:
            if not self.sources and self.topic.strict_sourcing:
                raise _NeedsAttention("research_required", "aucune source exploitable pour un sujet à sourcing strict")
            brief = self.brief()
            markdown = self.write(brief)
            self._save_version(markdown, "draft", "première rédaction", "write")
            metadata = self.metadata(brief, markdown)
            while True:
                with self._timed("qa_deterministic"):
                    checks = qa.summarize(
                        qa.run_checks(markdown, metadata, brief, self.topic, self.client, {s.id for s in self.sources})
                    )
                facts = self.factcheck(markdown)
                math = self.math(markdown)
                review = self.review(brief, markdown, checks, facts)
                action, fixes, attention = self.decide(checks, facts, review, math)
                if action == "REWRITE" and rewrites < self.budgets.max_auto_rewrites:
                    rewrites += 1
                    markdown = self.rewrite(brief, markdown, fixes)
                    self._save_version(markdown, "auto_rewrite", "; ".join(fixes)[:500], "rewrite")
                    metadata = self.metadata(brief, markdown)
                    continue
                break
            result["recommended_action"] = action
            result["attention_reasons"] = attention
            if action == "PASS":
                result["status"] = "ready_for_review"
            else:
                result["status"] = "needs_attention"
                result["attention_reasons"].insert(0, {
                    "REWRITE": "rewrite_limit_reached",
                    "HUMAN_REVIEW": "human_review",
                    "RESEARCH_REQUIRED": "research_required",
                }[action])
            ExportProvider(self.out_dir).create_draft(
                ArticleExport(
                    article_id=f"{self.client.slug}:{self.topic.id}:{self.profile.name}",
                    title=next((h for lvl, h in qa.headings(markdown) if lvl == 1), brief.recommended_title),
                    slug=metadata.slug,
                    title_tag=metadata.title_tag,
                    meta_description=metadata.meta_description,
                    markdown=markdown,
                )
            )
        except _NeedsAttention as e:
            result["status"] = "needs_attention"
            result["attention_reasons"] = [e.reason, str(e)]
        except BudgetExceeded as e:
            result["status"] = "needs_attention"
            result["attention_reasons"] = ["budget_exceeded", str(e)]
        except LLMError as e:
            result["status"] = "failed"
            result["error"] = str(e)
            log.error("%s/%s : échec — %s", self.topic.id, self.profile.name, e)

        article_cost = self.tracker.total_usd
        result.update(
            {
                "finished_at": now_iso(),
                "metadata": metadata.model_dump() if metadata else None,
                "metrics": {
                    "word_count": len(qa.body_words(markdown)) if markdown else 0,
                    "sources_available": len(self.sources),
                    "sources_official": sum(s.is_preferred_domain for s in self.sources),
                    "claims_verified_in_packet": len(self.claims),
                    "claims_marked": facts.get("claims_marked", 0),
                    "claims_supported": facts.get("supported", 0),
                    "claims_partial": facts.get("partial", 0),
                    "claims_unsupported": facts.get("unsupported", 0),
                    "unverified_markers": facts.get("unverified_markers", 0),
                    "unmarked_factual_claims_flagged": len(review.unmarked_factual_claims) if review else 0,
                    "internal_links": len([u for _, u in qa.links(markdown) if self.client.domain in u]),
                    "auto_rewrites": rewrites,
                },
                "costs": {
                    "article_usd": article_cost,
                    "research_share_usd": round(self.research_share_usd, 6),
                    "research_total_usd": self.packet.cost_usd,
                    "total_with_research_share_usd": round(article_cost + self.research_share_usd, 6),
                    "by_step": self.tracker.by_step(),
                    "by_model": self.tracker.by_model(),
                    "by_provider": self.tracker.by_provider(),
                    "alerts": self.tracker.alerts,
                    "budget": {"alert_usd": self.budgets.article_alert_usd, "hard_usd": self.budgets.article_hard_usd},
                },
                "durations_s": {
                    "total": round(time.perf_counter() - started, 2),
                    "research_shared": self.packet.duration_s,
                    "by_step": self.durations,
                },
                "prompt_versions": sorted({f"{r.prompt_name}@{r.prompt_version}" for r in self.tracker.records}),
                "qa": {
                    "deterministic": checks,
                    "factcheck": facts,
                    "review": review.model_dump() if review else None,
                    "math": math,
                },
                "versions": self.versions,
                "calls": len(self.tracker.records),
                "failed_calls": sum(not r.success for r in self.tracker.records),
            }
        )
        (self.out_dir / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result


class _NeedsAttention(Exception):
    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
