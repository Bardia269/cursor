"""Chargement de la configuration (YAML) et des entrées du benchmark."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
CLIENT_DIR = ROOT / "client"
PROMPTS_DIR = ROOT / "prompts"
DEFAULT_TOPICS = ROOT / "benchmark" / "topics.yaml"
DEFAULT_OUT = ROOT / "out"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass(frozen=True)
class TaskSpec:
    task: str
    provider: str
    model: str
    max_output_tokens: int
    effort: str | None = None

    @property
    def label(self) -> str:
        return f"{self.provider}:{self.model}"


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    tasks: dict[str, TaskSpec]

    def spec(self, task: str) -> TaskSpec:
        if task not in self.tasks:
            raise KeyError(f"Tâche '{task}' absente du profil {self.name} (config/models.yaml)")
        return self.tasks[task]

    def models_summary(self) -> dict[str, str]:
        return {task: spec.label for task, spec in sorted(self.tasks.items())}


def _task_spec(task: str, raw: dict[str, Any]) -> TaskSpec:
    return TaskSpec(
        task=task,
        provider=raw["provider"],
        model=raw["model"],
        max_output_tokens=int(raw.get("max_output_tokens", 4000)),
        effort=raw.get("effort"),
    )


def load_profiles(path: Path = CONFIG_DIR / "models.yaml") -> dict[str, Profile]:
    raw = _load_yaml(path)
    shared = {name: _task_spec(name, spec) for name, spec in raw.get("shared_tasks", {}).items()}
    profiles: dict[str, Profile] = {}
    for name, body in raw["profiles"].items():
        tasks = dict(shared)
        tasks.update({task: _task_spec(task, spec) for task, spec in body["tasks"].items()})
        profiles[name] = Profile(name=name, description=body.get("description", ""), tasks=tasks)
    return profiles


def research_profile(profiles: dict[str, Profile]) -> Profile:
    """Profil utilisé pour la recherche partagée : les tâches communes suffisent."""
    first = next(iter(profiles.values()))
    return Profile(name="research", description="Recherche partagée", tasks=first.tasks)


@dataclass(frozen=True)
class ModelPrice:
    input: float
    cached_input: float
    output: float


@dataclass(frozen=True)
class Pricing:
    models: dict[tuple[str, str], ModelPrice]
    openai_web_search_call_usd: float
    anthropic_cache_write_multiplier: float

    def price(self, provider: str, model: str) -> ModelPrice:
        try:
            return self.models[(provider, model)]
        except KeyError:
            raise KeyError(
                f"Prix inconnu pour {provider}:{model} — ajoutez-le dans config/pricing.yaml"
            ) from None


def load_pricing(path: Path = CONFIG_DIR / "pricing.yaml") -> Pricing:
    raw = _load_yaml(path)
    models: dict[tuple[str, str], ModelPrice] = {}
    for provider in ("openai", "anthropic"):
        for model, p in raw.get(provider, {}).get("models", {}).items():
            models[(provider, model)] = ModelPrice(
                input=float(p["input"]), cached_input=float(p["cached_input"]), output=float(p["output"])
            )
    return Pricing(
        models=models,
        openai_web_search_call_usd=float(raw.get("openai", {}).get("web_search_call_usd", 0.0)),
        anthropic_cache_write_multiplier=float(
            raw.get("anthropic", {}).get("cache_write_multiplier", 1.25)
        ),
    )


@dataclass(frozen=True)
class Budgets:
    article_alert_usd: float
    article_hard_usd: float
    max_auto_rewrites: int
    research_hard_usd: float
    max_sources: int
    max_source_chars: int
    llm_max_retries: int
    llm_timeout_seconds: float
    json_repair_attempts: int
    deliverable_max_minutes: float
    deliverable_target: int
    human_rate_usd_per_hour: float


def load_budgets(path: Path = CONFIG_DIR / "budgets.yaml") -> Budgets:
    raw = _load_yaml(path)
    return Budgets(
        article_alert_usd=float(raw["article"]["alert_usd"]),
        article_hard_usd=float(raw["article"]["hard_usd"]),
        max_auto_rewrites=int(raw["article"]["max_auto_rewrites"]),
        research_hard_usd=float(raw["research"]["hard_usd"]),
        max_sources=int(raw["research"]["max_sources"]),
        max_source_chars=int(raw["research"]["max_source_chars"]),
        llm_max_retries=int(raw["llm"]["max_retries"]),
        llm_timeout_seconds=float(raw["llm"]["timeout_seconds"]),
        json_repair_attempts=int(raw["llm"]["json_repair_attempts"]),
        deliverable_max_minutes=float(raw["benchmark"]["deliverable_max_minutes"]),
        deliverable_target=int(raw["benchmark"]["deliverable_target"]),
        human_rate_usd_per_hour=float(raw["benchmark"]["human_rate_usd_per_hour"]),
    )


@dataclass(frozen=True)
class ConversionTarget:
    primary: str
    action: str
    secondary: str | None = None


@dataclass(frozen=True)
class Topic:
    id: str
    type: str
    status: str
    title: str
    primary_keyword: str
    secondary_keywords: list[str]
    intent: str
    audience: str
    risk_level: str
    business_value: str
    conversion_target: ConversionTarget
    preferred_source_domains: list[str] = field(default_factory=list)
    manual_urls: list[str] = field(default_factory=list)
    cannibalization_note: str = ""
    strict_sourcing: bool = False
    checks: list[str] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return self.status == "ready"


def load_topics(path: Path = DEFAULT_TOPICS) -> tuple[str, list[Topic]]:
    raw = _load_yaml(path)
    topics = []
    for t in raw["topics"]:
        ct = t["conversion_target"]
        topics.append(
            Topic(
                id=t["id"],
                type=t["type"],
                status=t["status"],
                title=t["title"],
                primary_keyword=t.get("primary_keyword", ""),
                secondary_keywords=list(t.get("secondary_keywords", [])),
                intent=t.get("intent", "informational"),
                audience=t.get("audience", ""),
                risk_level=t.get("risk_level", "standard"),
                business_value=t["business_value"],
                conversion_target=ConversionTarget(
                    primary=ct["primary"], action=ct.get("action", ""), secondary=ct.get("secondary")
                ),
                preferred_source_domains=list(t.get("preferred_source_domains", [])),
                manual_urls=list(t.get("manual_urls", [])),
                cannibalization_note=(t.get("cannibalization_note") or "").strip(),
                strict_sourcing=bool(t.get("strict_sourcing", t.get("risk_level") == "sensitive")),
                checks=list(t.get("checks", [])),
            )
        )
    return raw["client"], topics


@dataclass(frozen=True)
class SitePage:
    url: str
    title: str
    type: str
    target_keyword: str | None = None


@dataclass(frozen=True)
class ClientContext:
    slug: str
    domain: str
    bible_md: str
    pages: list[SitePage]

    @property
    def page_urls(self) -> set[str]:
        return {p.url for p in self.pages}


def load_client(slug: str, client_dir: Path = CLIENT_DIR) -> ClientContext:
    bible = (client_dir / f"{slug}.md").read_text(encoding="utf-8")
    raw_pages = _load_yaml(client_dir / f"{slug}_pages.yaml")
    pages = [
        SitePage(url=p["url"], title=p["title"], type=p["type"], target_keyword=p.get("target_keyword"))
        for p in raw_pages["pages"]
    ]
    return ClientContext(slug=slug, domain=raw_pages["domain"], bible_md=bible, pages=pages)
