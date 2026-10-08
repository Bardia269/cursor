"""Fournisseurs de recherche documentaire (derrière une interface commune)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .config import Topic
from .costs import CostTracker
from .llm import LLMRouter
from .prompts import load_prompt

URL_RE = re.compile(r"https?://[^\s<>()\[\]\"'|]+")
TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}


@dataclass(frozen=True)
class SearchResult:
    url: str
    title: str
    origin: Literal["manual", "web"]


def normalize_url(url: str) -> str:
    url = url.strip().rstrip(".,;:")
    parts = urlsplit(url)
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if k not in TRACKING_PARAMS])
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, query, ""))


def domain_of(url: str) -> str:
    netloc = urlsplit(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def matches_domain(url: str, domains: list[str]) -> bool:
    host = domain_of(url)
    return any(host == d or host.endswith("." + d) for d in domains)


class SearchProvider(Protocol):
    name: str

    def search(self, topic: Topic, tracker: CostTracker, limit: int) -> list[SearchResult]: ...


class ManualUrlsProvider:
    """URL fournies à la main dans topics.yaml — pour le benchmark et le débogage."""

    name = "manual"

    def search(self, topic: Topic, tracker: CostTracker, limit: int) -> list[SearchResult]:
        return [SearchResult(url=u, title="", origin="manual") for u in topic.manual_urls[:limit]]


class WebSearchProvider:
    """Recherche web via l'outil de recherche du fournisseur LLM configuré pour la tâche `search`.

    Interroge d'abord les domaines préférés du sujet (sources officielles), puis le web ouvert.
    """

    name = "web"

    def __init__(self, router: LLMRouter, exclude_domains: list[str], country: str = "CH"):
        self.router = router
        self.exclude_domains = exclude_domains
        self.country = country

    def _run(
        self, topic: Topic, tracker: CostTracker, count: int, domains: list[str], step: str
    ) -> list[SearchResult]:
        result = self.router.web_search(
            tracker,
            step=step,
            prompt=load_prompt("search"),
            context={"topic": topic, "count": count, "official_only": bool(domains)},
            allowed_domains=domains,
            country=self.country,
        )
        found: list[SearchResult] = []
        titles = {normalize_url(u): t for u, t in result.citations if t}
        candidates = [u for u, _ in result.citations] + URL_RE.findall(result.text)
        for url in candidates:
            if not url.startswith("http") or matches_domain(url, self.exclude_domains):
                continue
            found.append(SearchResult(url=url, title=titles.get(normalize_url(url), ""), origin="web"))
        return found

    def search(self, topic: Topic, tracker: CostTracker, limit: int) -> list[SearchResult]:
        results: list[SearchResult] = []
        if topic.preferred_source_domains:
            results += self._run(
                topic, tracker, max(3, limit // 2), topic.preferred_source_domains, "search_official"
            )
        results += self._run(topic, tracker, limit, [], "search_open")
        return dedupe(results)[:limit]


class CombinedSearchProvider:
    name = "both"

    def __init__(self, providers: list[SearchProvider]):
        self.providers = providers

    def search(self, topic: Topic, tracker: CostTracker, limit: int) -> list[SearchResult]:
        results: list[SearchResult] = []
        for provider in self.providers:
            results += provider.search(topic, tracker, limit)
        return dedupe(results)[:limit]


def dedupe(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    unique = []
    for r in results:
        key = normalize_url(r.url)
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def prioritize(results: list[SearchResult], preferred_domains: list[str]) -> list[SearchResult]:
    """Manuel d'abord, puis domaines préférés, puis le reste (ordre stable)."""

    def rank(r: SearchResult) -> int:
        if r.origin == "manual":
            return 0
        return 1 if matches_domain(r.url, preferred_domains) else 2

    return sorted(results, key=rank)
