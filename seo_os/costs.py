"""Calcul des coûts, journal des appels et plafonds de budget."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import Pricing, TaskSpec

CHARS_PER_TOKEN_ESTIMATE = 3.5  # estimation prudente pour du français (pré-contrôle budgétaire)

_LOG_LOCK = threading.Lock()  # plusieurs articles peuvent écrire dans le même costs.jsonl


class BudgetExceeded(RuntimeError):
    """Levée avant un appel qui ferait dépasser le plafond dur."""


@dataclass
class Usage:
    input_tokens: int = 0          # tokens d'entrée non mis en cache
    cached_input_tokens: int = 0   # tokens lus depuis le cache
    cache_write_tokens: int = 0    # tokens écrits en cache (Anthropic)
    output_tokens: int = 0         # y compris raisonnement
    web_search_calls: int = 0


def compute_cost(pricing: Pricing, provider: str, model: str, usage: Usage) -> float:
    p = pricing.price(provider, model)
    cost = (
        usage.input_tokens * p.input
        + usage.cached_input_tokens * p.cached_input
        + usage.output_tokens * p.output
    ) / 1_000_000
    if provider == "anthropic":
        cost += usage.cache_write_tokens * p.input * pricing.anthropic_cache_write_multiplier / 1_000_000
    if provider == "openai":
        cost += usage.web_search_calls * pricing.openai_web_search_call_usd
    return round(cost, 6)


def estimate_max_cost(pricing: Pricing, spec: TaskSpec, prompt_chars: int) -> float:
    """Borne haute d'un appel : prompt entier non caché + sortie au plafond."""
    p = pricing.price(spec.provider, spec.model)
    input_tokens = prompt_chars / CHARS_PER_TOKEN_ESTIMATE
    return (input_tokens * p.input + spec.max_output_tokens * p.output) / 1_000_000


@dataclass
class CallRecord:
    timestamp: str
    scope: str            # ex. "research:valeurs-propres" ou "article:valeurs-propres:B"
    step: str
    task: str
    provider: str
    model: str
    prompt_name: str | None
    prompt_version: str | None
    usage: Usage
    cost_usd: float
    duration_s: float
    success: bool
    error: str | None = None


@dataclass
class CostTracker:
    """Accumule les appels d'un périmètre (un sujet en recherche, ou un article) et applique le budget."""

    scope: str
    pricing: Pricing
    hard_usd: float
    alert_usd: float | None = None
    log_path: Path | None = None
    records: list[CallRecord] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)

    @property
    def total_usd(self) -> float:
        return round(sum(r.cost_usd for r in self.records), 6)

    def check_budget(self, spec: TaskSpec, prompt_chars: int) -> None:
        estimate = estimate_max_cost(self.pricing, spec, prompt_chars)
        if self.total_usd + estimate > self.hard_usd:
            raise BudgetExceeded(
                f"{self.scope}: dépensé {self.total_usd:.4f} $ + estimation {estimate:.4f} $ "
                f"pour '{spec.task}' > plafond {self.hard_usd:.2f} $"
            )

    def record(self, rec: CallRecord) -> None:
        with _LOG_LOCK:
            self.records.append(rec)
            if self.alert_usd is not None and self.total_usd >= self.alert_usd and not self.alerts:
                self.alerts.append(
                    f"Seuil d'alerte {self.alert_usd:.2f} $ atteint après l'étape '{rec.step}'"
                )
            if self.log_path:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                with self.log_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")

    def by_step(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for r in self.records:
            s = out.setdefault(
                r.step, {"cost_usd": 0.0, "duration_s": 0.0, "calls": 0, "models": set()}
            )
            s["cost_usd"] = round(s["cost_usd"] + r.cost_usd, 6)
            s["duration_s"] = round(s["duration_s"] + r.duration_s, 2)
            s["calls"] += 1
            s["models"].add(f"{r.provider}:{r.model}")
        for s in out.values():
            s["models"] = sorted(s["models"])
        return out

    def by_model(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for r in self.records:
            key = f"{r.provider}:{r.model}"
            out[key] = round(out.get(key, 0.0) + r.cost_usd, 6)
        return out

    def by_provider(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for r in self.records:
            out[r.provider] = round(out.get(r.provider, 0.0) + r.cost_usd, 6)
        return out


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
