"""Interfaces des fournisseurs externes et leurs implémentations disponibles avant signature.

La logique métier ne dépend que des interfaces (Protocol). Chaque intégration a une implémentation
« non connectée » qui renvoie des listes vides et un état explicite ; la vraie implémentation se
branche après signature sans toucher aux écrans ni aux services.
"""

from __future__ import annotations

import csv
import io
import json
import os
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol
from urllib.error import HTTPError, URLError


class NotConnectedError(RuntimeError):
    """L'intégration n'est pas encore branchée (mode démo)."""


@dataclass
class ProviderStatus:
    status: str  # not_configured | configured | connected | no_credits | error | active
    detail: str


# --- Search Console --------------------------------------------------------------------------


@dataclass
class PagePerformance:
    url: str
    day: date
    clicks: int
    impressions: int
    position: float | None


class SearchConsoleProvider(Protocol):
    def status(self) -> ProviderStatus: ...

    def page_performance(self, site_url: str, start: date, end: date) -> list[PagePerformance]: ...


class NotConnectedSearchConsole:
    def status(self) -> ProviderStatus:
        return ProviderStatus("not_configured", "En attente de l'accès Search Console du client")

    def page_performance(self, site_url: str, start: date, end: date) -> list[PagePerformance]:
        raise NotConnectedError("Search Console non connectée")


# --- Données SEO (mots-clés, SERP, concurrents) -----------------------------------------------


@dataclass
class KeywordMetrics:
    keyword: str
    volume: int | None
    difficulty: float | None
    cpc: float | None = None


class SEODataProvider(Protocol):
    def status(self) -> ProviderStatus: ...

    def keyword_metrics(self, keywords: list[str], country: str, language: str) -> list[KeywordMetrics]: ...

    def keyword_ideas(self, seed: str, country: str, language: str, limit: int) -> list[KeywordMetrics]: ...

    def serp(self, keyword: str, country: str, language: str) -> list[dict]: ...

    def competitor_keywords(self, domain: str, country: str, limit: int) -> list[KeywordMetrics]: ...


@dataclass
class TregResponse:
    status_code: int
    body: object
    cost_usd: float
    call_id: str | None


class TregClient:
    """Client HTTP Treg conforme à https://treg.to/llms.txt.

    - Authentification : `X-Treg-Token` (+ `X-Treg-Org` pour un jeton d'identité).
    - Coût réel : en-tête `X-Treg-Cost-Micro` (micro-USD) → journalisé.
    - Plafond par appel : `X-Treg-Route-Max-Cost` (402 sans facturation si dépassé).
    - Retry sans double facturation : `Idempotency-Key`.
    Les identifiants d'endpoints du catalogue seront choisis après signature (`treg catalog search`).
    """

    BASE_URL = "https://treg.to"

    def __init__(self, token: str, org: str | None = None, timeout: float = 60.0):
        self.token = token
        self.org = org
        self.timeout = timeout

    def call(
        self, endpoint_id: str, params: dict[str, str], max_cost_usd: float = 0.5, idempotency_key: str | None = None
    ) -> TregResponse:
        query = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
        request = urllib.request.Request(f"{self.BASE_URL}/call/{endpoint_id}?{query}", headers=self._headers())
        request.add_header("X-Treg-Route-Max-Cost", f"{max_cost_usd:.4f}")
        if idempotency_key:
            request.add_header("Idempotency-Key", idempotency_key)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                return TregResponse(
                    status_code=resp.status,
                    body=json.loads(resp.read() or b"null"),
                    cost_usd=int(resp.headers.get("X-Treg-Cost-Micro", "0")) / 1_000_000,
                    call_id=resp.headers.get("X-Treg-Call-Id"),
                )
        except HTTPError as e:
            return TregResponse(status_code=e.code, body=_safe_json(e.read()), cost_usd=0.0, call_id=None)

    def _headers(self) -> dict[str, str]:
        headers = {"X-Treg-Token": self.token, "Accept": "application/json"}
        if self.org:
            headers["X-Treg-Org"] = self.org
        return headers


def _safe_json(raw: bytes) -> object:
    try:
        return json.loads(raw)
    except ValueError:
        return raw.decode("utf-8", errors="replace")


class TregSEODataProvider:
    """Données SEO via Treg. Le mapping des endpoints (DataForSEO, Semrush…) se fait après signature."""

    def __init__(self, client: TregClient | None):
        self.client = client

    def status(self) -> ProviderStatus:
        if self.client is None:
            return ProviderStatus("not_configured", "Jeton Treg absent (TREG_API_KEY)")
        return ProviderStatus("configured", "Jeton présent — endpoints SEO à sélectionner après signature")

    def _pending(self, *_, **__):
        raise NotConnectedError("Endpoints Treg non encore sélectionnés (mode démo)")

    keyword_metrics = keyword_ideas = serp = competitor_keywords = _pending


def treg_from_env() -> TregClient | None:
    token = os.environ.get("TREG_API_KEY")
    return TregClient(token, org=os.environ.get("TREG_ORG")) if token else None


# --- Backlinks ---------------------------------------------------------------------------------


class BacklinkProvider(Protocol):
    def status(self) -> ProviderStatus: ...

    def referring_domains(self, target: str, limit: int) -> list[dict]: ...

    def backlinks(self, target: str, limit: int) -> list[dict]: ...


class NotConnectedBacklinks:
    def status(self) -> ProviderStatus:
        return ProviderStatus("not_configured", "Module backlinks prévu après signature (via Treg)")

    def referring_domains(self, target: str, limit: int) -> list[dict]:
        raise NotConnectedError("Backlinks non connectés")

    backlinks = referring_domains


# --- Import de contenus ------------------------------------------------------------------------

IMPORT_FIELDS = ("url", "title", "h1", "slug", "page_type", "published_at", "word_count", "content")


@dataclass
class ImportedPage:
    url: str
    title: str
    h1: str | None = None
    slug: str | None = None
    page_type: str = "article"
    published_at: date | None = None
    word_count: int | None = None
    content: str | None = None
    extra: dict = field(default_factory=dict)


class ContentImportProvider(Protocol):
    def pages(self) -> list[ImportedPage]: ...


class FileImportProvider:
    """Import d'un export CSV ou JSON (liste d'objets) — le chemin prévu pour les 300–400 articles."""

    def __init__(self, filename: str, data: bytes):
        self.filename = filename
        self.data = data

    def pages(self) -> list[ImportedPage]:
        text = self.data.decode("utf-8-sig")
        if self.filename.lower().endswith(".json"):
            rows = json.loads(text)
            if isinstance(rows, dict):
                rows = rows.get("pages") or rows.get("items") or []
        else:
            rows = list(csv.DictReader(io.StringIO(text)))
        pages = []
        for row in rows:
            url, title = (row.get("url") or "").strip(), (row.get("title") or "").strip()
            if not url or not title:
                continue
            content = row.get("content") or None
            word_count = row.get("word_count")
            pages.append(
                ImportedPage(
                    url=url,
                    title=title,
                    h1=row.get("h1") or None,
                    slug=row.get("slug") or url.rstrip("/").rsplit("/", 1)[-1] or None,
                    page_type=row.get("page_type") or "article",
                    published_at=_parse_date(row.get("published_at")),
                    word_count=int(word_count) if word_count not in (None, "") else (len(content.split()) if content else None),
                    content=content,
                    extra={k: v for k, v in row.items() if k not in IMPORT_FIELDS},
                )
            )
        return pages


def _parse_date(value) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


# --- Vérification des fournisseurs LLM ---------------------------------------------------------


def check_anthropic() -> ProviderStatus:
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        return ProviderStatus("not_configured", "Clé ANTHROPIC_API_KEY absente")
    try:
        import anthropic

        models = [m.id for m in anthropic.Anthropic(max_retries=0, timeout=15).models.list(limit=20)]
        return ProviderStatus("connected", f"{len(models)} modèles accessibles")
    except Exception as e:  # réseau, clé invalide…
        return ProviderStatus("error", f"{type(e).__name__}: {str(e)[:160]}")


def check_openai(model: str = "gpt-6-luna") -> ProviderStatus:
    """Appel minimal (quelques tokens) : seul moyen de détecter un compte sans crédit."""
    if not os.environ.get("OPENAI_API_KEY"):
        return ProviderStatus("not_configured", "Clé OPENAI_API_KEY absente")
    try:
        from openai import OpenAI, RateLimitError

        try:
            OpenAI(max_retries=0, timeout=20).responses.create(model=model, input="ok", max_output_tokens=16)
        except RateLimitError as e:
            if "insufficient_quota" in str(e) or "credit" in str(e).lower():
                return ProviderStatus("no_credits", "Clé valide, crédits épuisés")
            raise
        return ProviderStatus("connected", f"Appel test réussi ({model})")
    except Exception as e:
        return ProviderStatus("error", f"{type(e).__name__}: {str(e)[:160]}")


def check_treg() -> ProviderStatus:
    client = treg_from_env()
    if client is None:
        return ProviderStatus("not_configured", "Jeton TREG_API_KEY absent")
    try:
        request = urllib.request.Request(f"{TregClient.BASE_URL}/catalog/platforms", headers=client._headers())
        with urllib.request.urlopen(request, timeout=15) as resp:
            ok = resp.status == 200
    except (HTTPError, URLError, TimeoutError) as e:
        return ProviderStatus("error", f"Treg injoignable : {e}")
    if not ok:
        return ProviderStatus("error", "Réponse inattendue du catalogue Treg")
    return ProviderStatus("configured", "Jeton présent, catalogue joignable — endpoints à choisir après signature")
