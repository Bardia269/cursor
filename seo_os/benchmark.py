"""Saisie de la relecture humaine et comparaison des configurations A/B/C."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from .config import Budgets
from .costs import now_iso


def article_dir(out_root: Path, topic_id: str, profile: str) -> Path:
    return out_root / "articles" / topic_id / profile


def record_review(
    out_root: Path,
    topic_id: str,
    profile: str,
    minutes: float,
    corrections: int,
    sections_rewritten: int,
    score: float,
    deliverable: bool,
    notes: str | None,
) -> dict:
    path = article_dir(out_root, topic_id, profile) / "result.json"
    result = json.loads(path.read_text(encoding="utf-8"))
    result["human_review"] = {
        "review_minutes": minutes,
        "corrections_count": corrections,
        "sections_rewritten": sections_rewritten,
        "human_score": score,
        "deliverable": deliverable,
        "notes": notes,
        "reviewed_at": now_iso(),
    }
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def load_results(out_root: Path) -> list[dict]:
    return [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted((out_root / "articles").glob("*/*/result.json"))
    ]


@dataclass
class Row:
    topic: str
    profile: str
    status: str
    business_value: str
    api_cost: float
    duration_s: float
    words: int
    qa_score: int | None
    unsupported: int
    unverified: int
    minutes: float | None
    corrections: int | None
    sections: int | None
    human_score: float | None
    deliverable: bool | None

    def is_deliverable(self, max_minutes: float) -> bool:
        return bool(self.deliverable) and self.minutes is not None and self.minutes < max_minutes

    def effective_cost(self, rate_per_hour: float) -> float | None:
        if self.minutes is None:
            return None
        return self.api_cost + self.minutes / 60 * rate_per_hour


def to_row(r: dict) -> Row:
    review = (r.get("qa") or {}).get("review") or {}
    metrics = r.get("metrics") or {}
    human = r.get("human_review") or {}
    return Row(
        topic=r["topic"]["id"],
        profile=r["config"]["profile"],
        status=r["status"],
        business_value=r["topic"]["business_value"],
        api_cost=r["costs"]["total_with_research_share_usd"],
        duration_s=r["durations_s"]["total"],
        words=metrics.get("word_count", 0),
        qa_score=review.get("overall_quality_score"),
        unsupported=metrics.get("claims_unsupported", 0),
        unverified=metrics.get("unverified_markers", 0),
        minutes=human.get("review_minutes"),
        corrections=human.get("corrections_count"),
        sections=human.get("sections_rewritten"),
        human_score=human.get("human_score"),
        deliverable=human.get("deliverable"),
    )


def _avg(values: list) -> float | None:
    values = [v for v in values if v is not None]
    return round(mean(values), 2) if values else None


def _fmt(value, suffix: str = "", digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}{suffix}"
    return f"{value}{suffix}"


def summarize_profiles(rows: list[Row], budgets: Budgets) -> list[dict]:
    summaries = []
    for profile in sorted({r.profile for r in rows}):
        rs = [r for r in rows if r.profile == profile]
        reviewed = [r for r in rs if r.minutes is not None]
        deliverable = sum(r.is_deliverable(budgets.deliverable_max_minutes) for r in reviewed)
        summaries.append(
            {
                "profile": profile,
                "articles": len(rs),
                "reviewed": len(reviewed),
                "deliverable": deliverable,
                "meets_target": len(reviewed) == len(rs) and deliverable >= budgets.deliverable_target,
                "api_cost": _avg([r.api_cost for r in rs]),
                "minutes": _avg([r.minutes for r in reviewed]),
                "corrections": _avg([r.corrections for r in reviewed]),
                "sections": _avg([r.sections for r in reviewed]),
                "human_score": _avg([r.human_score for r in reviewed]),
                "effective_cost": _avg([r.effective_cost(budgets.human_rate_usd_per_hour) for r in reviewed]),
                "qa_score": _avg([r.qa_score for r in rs]),
                "unsupported": sum(r.unsupported for r in rs),
                "unverified": sum(r.unverified for r in rs),
                "duration_s": _avg([r.duration_s for r in rs]),
                "failed": sum(r.status == "failed" for r in rs),
            }
        )
    return summaries


def pick_winner(summaries: list[dict]) -> dict | None:
    """Parmi les configurations entièrement relues et atteignant l'objectif : coût effectif le plus bas."""
    eligible = [s for s in summaries if s["meets_target"] and s["effective_cost"] is not None]
    if not eligible:
        return None
    return min(eligible, key=lambda s: (s["effective_cost"], -(s["human_score"] or 0)))


def build_report(out_root: Path, budgets: Budgets) -> str:
    rows = [to_row(r) for r in load_results(out_root)]
    if not rows:
        return "Aucun résultat dans " + str(out_root / "articles")
    summaries = summarize_profiles(rows, budgets)
    winner = pick_winner(summaries)
    rate = budgets.human_rate_usd_per_hour
    lines = [
        "# Benchmark V0 — comparaison des configurations",
        "",
        f"Généré le {now_iso()}. Livrable = relu en moins de {budgets.deliverable_max_minutes:g} min et jugé livrable. "
        f"Objectif : au moins {budgets.deliverable_target} articles livrables sur 5. "
        f"Coût effectif = coût API (recherche partagée incluse) + temps humain à {rate:g} $/h.",
        "",
        "## Par configuration",
        "",
        "| Config | Articles | Relus | Livrables | Objectif | Coût API moy. | Temps humain moy. | Corrections moy. "
        "| Sections réécrites moy. | Note humaine moy. | Coût effectif moy. | Score QA IA moy. | Faits non soutenus "
        "| [À VÉRIFIER] | Durée moy. | Échecs |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['profile']} | {s['articles']} | {s['reviewed']} | {s['deliverable']} | "
            f"{'✅' if s['meets_target'] else '—'} | {_fmt(s['api_cost'], ' $')} | {_fmt(s['minutes'], ' min', 1)} | "
            f"{_fmt(s['corrections'], '', 1)} | {_fmt(s['sections'], '', 1)} | {_fmt(s['human_score'], '/10', 1)} | "
            f"{_fmt(s['effective_cost'], ' $')} | {_fmt(s['qa_score'], '', 0)} | {s['unsupported']} | {s['unverified']} | "
            f"{_fmt(s['duration_s'], ' s', 0)} | {s['failed']} |"
        )
    lines += ["", "## Configuration retenue", ""]
    if winner:
        lines.append(
            f"**{winner['profile']}** — {winner['deliverable']}/{winner['reviewed']} livrables, "
            f"coût effectif moyen {winner['effective_cost']:.2f} $ "
            f"(API {winner['api_cost']:.2f} $ + {winner['minutes']:.1f} min de relecture)."
        )
    else:
        lines.append("Aucune configuration n'atteint encore l'objectif (ou les relectures ne sont pas toutes saisies).")
    lines += [
        "",
        "## Par article",
        "",
        "| Sujet | Config | Valeur | Statut | Mots | Coût API | Score QA IA | Non soutenus | Temps | Corrections "
        "| Sections | Note | Livrable |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda r: (r.topic, r.profile)):
        lines.append(
            f"| {r.topic} | {r.profile} | {r.business_value} | {r.status} | {r.words} | {r.api_cost:.2f} $ | "
            f"{_fmt(r.qa_score)} | {r.unsupported} | {_fmt(r.minutes, ' min', 1)} | {_fmt(r.corrections)} | "
            f"{_fmt(r.sections)} | {_fmt(r.human_score)} | "
            f"{'—' if r.deliverable is None else ('oui' if r.is_deliverable(budgets.deliverable_max_minutes) else 'non')} |"
        )
    return "\n".join(lines) + "\n"


def write_csv(out_root: Path, path: Path) -> None:
    rows = [to_row(r) for r in load_results(out_root)]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(list(Row.__dataclass_fields__))
        for r in rows:
            writer.writerow([getattr(r, name) for name in Row.__dataclass_fields__])
