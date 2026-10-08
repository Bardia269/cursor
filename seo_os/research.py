"""Recherche documentaire par sujet : sources → extraction d'affirmations → paquet figé.

Le paquet est calculé une seule fois par sujet et partagé par les configurations A/B/C, pour que le
benchmark compare la rédaction à données égales.
"""

from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .config import Budgets, ClientContext, Pricing, Topic
from .costs import BudgetExceeded, CostTracker, now_iso
from .fetch import FetchedPage, fetch_page
from .llm import LLMError, LLMRouter
from .prompts import load_prompt
from .schemas import Claim, ResearchPacket, Source, SourceExtraction
from .search import SearchProvider, domain_of, matches_domain, prioritize

log = logging.getLogger(__name__)

FETCH_WORKERS = 6
EXTRACT_WORKERS = 4
ELLIPSIS_RE = re.compile(r"\s*(?:\.\.\.|…|\[\.\.\.\]|\(\.\.\.\))\s*")


def _normalize_for_match(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("­", "")  # trait d'union conditionnel
    for src, dst in (("’", "'"), ("‘", "'"), ("«", '"'), ("»", '"'), ("“", '"'), ("”", '"'), ("–", "-"), ("—", "-")):
        text = text.replace(src, dst)
    text = re.sub(r"[*_`#>]", "", text)  # marques Markdown laissées par l'extraction
    return " ".join(text.split())


def quote_in_text(quote: str, text: str) -> bool:
    """Vérification déterministe : la citation existe-t-elle dans la source ? (ellipses tolérées)"""
    haystack = _normalize_for_match(text)
    parts = [p for p in ELLIPSIS_RE.split(_normalize_for_match(quote)) if len(p) >= 12]
    return bool(parts) and all(p in haystack for p in parts)


def build_research_packet(
    topic: Topic,
    client: ClientContext,
    search_provider: SearchProvider,
    router: LLMRouter,
    budgets: Budgets,
    pricing: Pricing,
    out_dir: Path,
    cost_log: Path | None = None,
) -> ResearchPacket:
    started = time.perf_counter()
    tracker = CostTracker(
        scope=f"research:{topic.id}", pricing=pricing, hard_usd=budgets.research_hard_usd, log_path=cost_log
    )
    sources_dir = out_dir / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    try:
        results = search_provider.search(topic, tracker, budgets.max_sources * 2)
    except (LLMError, BudgetExceeded) as e:
        log.error("%s: recherche impossible (%s)", topic.id, e)
        errors.append(f"search: {e}")
        results = []
    results = [r for r in results if not matches_domain(r.url, [client.domain])]
    results = prioritize(results, topic.preferred_source_domains)[: budgets.max_sources]
    log.info("%s: %d source(s) candidates", topic.id, len(results))

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        pages: list[FetchedPage] = list(pool.map(lambda r: fetch_page(r.url), results))

    sources: list[Source] = []
    for i, (result, page) in enumerate(zip(results, pages), start=1):
        source = Source(
            id=f"S{i}",
            url=result.url,
            title=page.title or result.title,
            domain=domain_of(result.url),
            origin=result.origin,
            is_preferred_domain=matches_domain(result.url, topic.preferred_source_domains),
            fetched=page.ok,
            fetch_error=page.error,
            content_type=page.content_type,
            word_count=len(page.text.split()),
            headings=page.headings,
        )
        if page.ok:
            (sources_dir / f"{source.id}.txt").write_text(page.text, encoding="utf-8")
        sources.append(source)

    prompt = load_prompt("extract_claims")

    def extract(source: Source) -> tuple[Source, SourceExtraction | None, str]:
        text = (sources_dir / f"{source.id}.txt").read_text(encoding="utf-8")
        try:
            result = router.generate(
                tracker,
                step="extract_claims",
                prompt=prompt,
                context={
                    "topic": topic,
                    "source": source,
                    "source_text": text[: budgets.max_source_chars],
                },
                schema=SourceExtraction,
            )
        except (LLMError, BudgetExceeded) as e:
            log.warning("%s %s: extraction impossible (%s)", topic.id, source.id, e)
            source.fetch_error = f"extraction: {e}"
            return source, None, text
        return source, result.parsed, text  # type: ignore[return-value]

    claims: list[Claim] = []
    fetched = [s for s in sources if s.fetched]
    with ThreadPoolExecutor(max_workers=EXTRACT_WORKERS) as pool:
        for source, extraction, text in pool.map(extract, fetched):
            if extraction is None:
                continue
            source.relevant = extraction.relevant
            source.summary = extraction.summary
            source.reader_questions = extraction.reader_questions
            for c in extraction.claims:
                claims.append(
                    Claim(
                        id="",
                        source_id=source.id,
                        statement=c.statement,
                        quote=c.quote,
                        claim_type=c.claim_type,
                        quote_verified=quote_in_text(c.quote, text),
                    )
                )

    claims.sort(key=lambda c: int(c.source_id[1:]))
    for n, claim in enumerate(claims, start=1):
        claim.id = f"C{n}"

    packet = ResearchPacket(
        topic_id=topic.id,
        created_at=now_iso(),
        search_mode=search_provider.name,
        sources=sources,
        claims=claims,
        cost_usd=tracker.total_usd,
        duration_s=round(time.perf_counter() - started, 2),
        steps=[{"step": k, **v} for k, v in tracker.by_step().items()],
        errors=errors,
    )
    (out_dir / "packet.json").write_text(
        json.dumps(packet.model_dump(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return packet


def load_packet(out_dir: Path) -> ResearchPacket:
    return ResearchPacket.model_validate_json((out_dir / "packet.json").read_text(encoding="utf-8"))


def source_text(research_dir: Path, source_id: str) -> str:
    path = research_dir / "sources" / f"{source_id}.txt"
    return path.read_text(encoding="utf-8") if path.exists() else ""
