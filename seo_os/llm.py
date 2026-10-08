"""Abstraction LLM : adaptateurs fournisseurs + routeur par tâche.

La logique métier n'appelle que `LLMRouter.generate()` / `LLMRouter.web_search()` avec un nom de
tâche ; le profil (config/models.yaml) décide du fournisseur et du modèle. Chaque appel est
journalisé avec son coût, sa durée et la version du prompt.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from .config import Budgets, Pricing, Profile, TaskSpec
from .costs import CallRecord, CostTracker, Usage, compute_cost, now_iso
from .prompts import Prompt

T = TypeVar("T", bound=BaseModel)

log = logging.getLogger(__name__)


class LLMError(RuntimeError):
    def __init__(self, message: str, usage: Usage | None = None):
        super().__init__(message)
        self.usage = usage or Usage()


class TruncatedOutput(LLMError):
    """La sortie a atteint max_output_tokens."""


class Refusal(LLMError):
    """Le modèle a refusé de répondre."""


@dataclass
class LLMResult:
    text: str
    usage: Usage
    parsed: BaseModel | None = None
    citations: list[tuple[str, str]] = field(default_factory=list)  # (url, titre) — recherche web


class LLMProvider(Protocol):
    def generate(
        self, spec: TaskSpec, system: str, user: str, schema: type[BaseModel] | None
    ) -> LLMResult: ...

    def web_search(
        self, spec: TaskSpec, system: str, user: str, allowed_domains: list[str], country: str
    ) -> LLMResult: ...


# --- OpenAI ----------------------------------------------------------------------------------


class OpenAIProvider:
    def __init__(self, timeout: float, max_retries: int):
        from openai import OpenAI

        if not os.environ.get("OPENAI_API_KEY"):
            raise LLMError("OPENAI_API_KEY manquante (voir .env.example)")
        self.client = OpenAI(timeout=timeout, max_retries=max_retries)
        self._no_reasoning: set[str] = set()  # modèles qui refusent le paramètre reasoning

    def _call(self, method, spec: TaskSpec, **kwargs):
        """Appelle l'API ; si le modèle refuse `reasoning`, réessaie une fois sans (et s'en souvient)."""
        from openai import BadRequestError

        if spec.model in self._no_reasoning:
            kwargs.pop("reasoning", None)
        try:
            return method(**kwargs)
        except BadRequestError as e:
            if "reasoning" not in kwargs or "reasoning" not in str(e).lower():
                raise
            log.warning("%s n'accepte pas reasoning.effort : appel relancé sans", spec.model)
            self._no_reasoning.add(spec.model)
            kwargs.pop("reasoning")
            return method(**kwargs)

    @staticmethod
    def _usage(resp) -> Usage:
        u = resp.usage
        if u is None:
            return Usage()
        cached = (u.input_tokens_details.cached_tokens or 0) if u.input_tokens_details else 0
        return Usage(
            input_tokens=u.input_tokens - cached, cached_input_tokens=cached, output_tokens=u.output_tokens
        )

    def _base_kwargs(self, spec: TaskSpec, system: str, user: str) -> dict:
        kwargs: dict = {
            "model": spec.model,
            "instructions": system,
            "input": user,
            "max_output_tokens": spec.max_output_tokens,
            "store": False,
        }
        if spec.effort:
            kwargs["reasoning"] = {"effort": spec.effort}
        return kwargs

    def _check_complete(self, resp, usage: Usage) -> None:
        if getattr(resp, "status", None) == "incomplete":
            reason = getattr(getattr(resp, "incomplete_details", None), "reason", None)
            raise TruncatedOutput(f"Réponse OpenAI incomplète ({reason})", usage)

    def generate(self, spec, system, user, schema):
        kwargs = self._base_kwargs(spec, system, user)
        if schema is not None:
            resp = self._call(self.client.responses.parse, spec, text_format=schema, **kwargs)
            usage = self._usage(resp)
            self._check_complete(resp, usage)
            return LLMResult(text=resp.output_text, usage=usage, parsed=resp.output_parsed)
        resp = self._call(self.client.responses.create, spec, **kwargs)
        usage = self._usage(resp)
        self._check_complete(resp, usage)
        return LLMResult(text=resp.output_text, usage=usage)

    def web_search(self, spec, system, user, allowed_domains, country):
        tool: dict = {"type": "web_search", "user_location": {"type": "approximate", "country": country}}
        if allowed_domains:
            tool["filters"] = {"allowed_domains": allowed_domains}
        resp = self._call(
            self.client.responses.create,
            spec,
            tools=[tool],
            include=["web_search_call.action.sources"],
            **self._base_kwargs(spec, system, user),
        )
        usage = self._usage(resp)
        citations: list[tuple[str, str]] = []
        for item in resp.output:
            if item.type == "web_search_call":
                usage.web_search_calls += 1
                for src in getattr(getattr(item, "action", None), "sources", None) or []:
                    citations.append((src.url, ""))
            elif item.type == "message":
                for part in item.content:
                    for ann in getattr(part, "annotations", None) or []:
                        if ann.type == "url_citation":
                            citations.append((ann.url, ann.title or ""))
        self._check_complete(resp, usage)
        return LLMResult(text=resp.output_text, usage=usage, citations=citations)


# --- Anthropic -------------------------------------------------------------------------------


class AnthropicProvider:
    def __init__(self, timeout: float, max_retries: int):
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.Anthropic(timeout=timeout, max_retries=max_retries)

    @staticmethod
    def _usage(msg) -> Usage:
        u = msg.usage
        return Usage(
            input_tokens=u.input_tokens,
            cached_input_tokens=u.cache_read_input_tokens or 0,
            cache_write_tokens=u.cache_creation_input_tokens or 0,
            output_tokens=u.output_tokens,
        )

    def generate(self, spec, system, user, schema):
        output_config: dict = {}
        if spec.effort:
            output_config["effort"] = spec.effort
        if schema is not None:
            output_config["format"] = {
                "type": "json_schema",
                "schema": self._anthropic.transform_schema(schema),
            }
        kwargs: dict = {
            "model": spec.model,
            "max_tokens": spec.max_output_tokens,
            # Le message système (bible client + consignes) est stable : on le met en cache.
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": user}],
        }
        if output_config:
            kwargs["output_config"] = output_config
        with self.client.messages.stream(**kwargs) as stream:
            msg = stream.get_final_message()
        usage = self._usage(msg)
        if msg.stop_reason == "refusal":
            raise Refusal(f"Refus du modèle ({getattr(msg, 'stop_details', None)})", usage)
        if msg.stop_reason == "max_tokens":
            raise TruncatedOutput("Réponse Anthropic tronquée (max_tokens)", usage)
        text = "".join(block.text for block in msg.content if block.type == "text")
        parsed = schema.model_validate_json(text) if schema is not None else None
        return LLMResult(text=text, usage=usage, parsed=parsed)

    WEB_SEARCH_TOOL = "web_search_20260209"
    MAX_PAUSE_CONTINUATIONS = 3

    def web_search(self, spec, system, user, allowed_domains, country):
        tool: dict = {
            "type": self.WEB_SEARCH_TOOL,
            "name": "web_search",
            "max_uses": 5,
            "user_location": {"type": "approximate", "country": country},
        }
        if allowed_domains:
            tool["allowed_domains"] = allowed_domains
        messages: list = [{"role": "user", "content": user}]
        usage = Usage()
        citations: list[tuple[str, str]] = []
        texts: list[str] = []
        for _ in range(self.MAX_PAUSE_CONTINUATIONS + 1):
            kwargs: dict = {
                "model": spec.model,
                "max_tokens": spec.max_output_tokens,
                "system": system,
                "messages": messages,
                "tools": [tool],
            }
            if spec.effort:
                kwargs["output_config"] = {"effort": spec.effort}
            with self.client.messages.stream(**kwargs) as stream:
                msg = stream.get_final_message()
            step_usage = self._usage(msg)
            for field_name in ("input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens"):
                setattr(usage, field_name, getattr(usage, field_name) + getattr(step_usage, field_name))
            server = getattr(msg.usage, "server_tool_use", None)
            usage.web_search_calls += getattr(server, "web_search_requests", 0) or 0
            for block in msg.content:
                if block.type == "web_search_tool_result" and isinstance(block.content, list):
                    citations += [(r.url, r.title or "") for r in block.content if getattr(r, "url", None)]
                elif block.type == "text":
                    texts.append(block.text)
                    for cit in getattr(block, "citations", None) or []:
                        if getattr(cit, "url", None):
                            citations.append((cit.url, getattr(cit, "title", "") or ""))
            if msg.stop_reason == "refusal":
                raise Refusal("Refus du modèle pendant la recherche", usage)
            if msg.stop_reason != "pause_turn":
                break
            messages = messages + [{"role": "assistant", "content": msg.content}]
        return LLMResult(text="\n".join(texts), usage=usage, citations=citations)


# --- Routeur ---------------------------------------------------------------------------------


class LLMRouter:
    """Résout tâche → fournisseur/modèle, applique budget, retries JSON et journalisation."""

    def __init__(
        self,
        profile: Profile,
        pricing: Pricing,
        budgets: Budgets,
        providers: dict[str, LLMProvider] | None = None,
    ):
        self.profile = profile
        self.pricing = pricing
        self.budgets = budgets
        self._providers: dict[str, LLMProvider] = dict(providers or {})

    def provider(self, name: str) -> LLMProvider:
        if name not in self._providers:
            factories = {"openai": OpenAIProvider, "anthropic": AnthropicProvider}
            if name not in factories:
                raise LLMError(f"Fournisseur inconnu : {name}")
            self._providers[name] = factories[name](
                timeout=self.budgets.llm_timeout_seconds, max_retries=self.budgets.llm_max_retries
            )
        return self._providers[name]

    def _record(
        self,
        tracker: CostTracker,
        step: str,
        spec: TaskSpec,
        prompt: Prompt,
        usage: Usage,
        started: float,
        error: str | None = None,
    ) -> None:
        tracker.record(
            CallRecord(
                timestamp=now_iso(),
                scope=tracker.scope,
                step=step,
                task=spec.task,
                provider=spec.provider,
                model=spec.model,
                prompt_name=prompt.name,
                prompt_version=prompt.version_label,
                usage=usage,
                cost_usd=compute_cost(self.pricing, spec.provider, spec.model, usage),
                duration_s=round(time.perf_counter() - started, 2),
                success=error is None,
                error=error,
            )
        )

    def generate(
        self,
        tracker: CostTracker,
        step: str,
        prompt: Prompt,
        context: dict,
        schema: type[T] | None = None,
    ) -> LLMResult:
        spec = self.profile.spec(prompt.task)
        system, user = prompt.render(**context)
        attempts = 1 + (self.budgets.json_repair_attempts if schema is not None else 0)
        last_error: Exception | None = None
        for attempt in range(attempts):
            message = user
            if attempt > 0 and last_error is not None:
                message += (
                    "\n\nATTENTION : ta réponse précédente ne respectait pas le format JSON demandé "
                    f"({str(last_error)[:300]}). Réponds uniquement avec un JSON valide conforme au schéma."
                )
            tracker.check_budget(spec, len(system) + len(message))
            started = time.perf_counter()
            try:
                result = self.provider(spec.provider).generate(spec, system, message, schema)
            except ValidationError as e:
                self._record(tracker, step, spec, prompt, Usage(), started, f"validation: {e}")
                last_error = e
                continue
            except LLMError as e:
                self._record(tracker, step, spec, prompt, e.usage, started, str(e))
                raise
            except Exception as e:  # erreurs SDK après épuisement des retries
                self._record(tracker, step, spec, prompt, Usage(), started, f"{type(e).__name__}: {e}")
                raise LLMError(f"{step}: {type(e).__name__}: {e}") from e
            if schema is not None and result.parsed is None:
                self._record(tracker, step, spec, prompt, result.usage, started, "sortie structurée vide")
                last_error = LLMError("sortie structurée vide")
                continue
            self._record(tracker, step, spec, prompt, result.usage, started)
            return result
        raise LLMError(f"{step}: sortie structurée invalide après {attempts} tentative(s): {last_error}")

    def web_search(
        self,
        tracker: CostTracker,
        step: str,
        prompt: Prompt,
        context: dict,
        allowed_domains: list[str],
        country: str = "CH",
    ) -> LLMResult:
        spec = self.profile.spec(prompt.task)
        system, user = prompt.render(**context)
        tracker.check_budget(spec, len(system) + len(user))
        started = time.perf_counter()
        try:
            result = self.provider(spec.provider).web_search(spec, system, user, allowed_domains, country)
        except LLMError as e:
            self._record(tracker, step, spec, prompt, e.usage, started, str(e))
            raise
        except Exception as e:
            self._record(tracker, step, spec, prompt, Usage(), started, f"{type(e).__name__}: {e}")
            raise LLMError(f"{step}: {type(e).__name__}: {e}") from e
        self._record(tracker, step, spec, prompt, result.usage, started)
        return result
