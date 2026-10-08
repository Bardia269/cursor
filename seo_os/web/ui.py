"""Libellés et formats d'affichage (français) partagés par les gabarits."""

from __future__ import annotations

import re
from datetime import date, datetime

# Provenance → badge
SOURCE_BADGES = {
    "public": ("RÉEL", "real", "Donnée publique relevée sur le site"),
    "pipeline": ("RÉEL", "real", "Produit par le pipeline"),
    "import": ("RÉEL", "real", "Importé depuis un export du client"),
    "gsc": ("RÉEL", "real", "Search Console"),
    "treg": ("RÉEL", "real", "Treg"),
    "proposal": ("PROPOSITION", "proposal", "Analyse proposée, à valider"),
    "validated": ("VALIDÉ", "validated", "Validé"),
    "example": ("EXEMPLE", "example", "Exemple de démonstration"),
}

COVERAGE_LABELS = {
    "covered": "Couvert",
    "partial": "Partiel",
    "cannibalized": "Cannibalisé",
    "gap": "Manquant",
}

ACTION_LABELS = {
    "KEEP": "Conserver",
    "UPDATE": "Mettre à jour",
    "MERGE": "Fusionner",
    "REDIRECT": "Rediriger",
    "REWRITE": "Réécrire",
    "DELETE": "Supprimer / noindex",
    "REPOSITION": "Repositionner",
    "CREATE": "Créer",
    "SKIP": "Ignorer",
}

PAGE_STATUS_LABELS = {
    "published": "Publiée",
    "to_audit": "À auditer",
    "in_production": "En production",
    "ready_for_review": "Prêt pour relecture",
    "needs_attention": "Attention requise",
    "approved": "Approuvé",
    "failed": "Échec",
}

PLAN_STATUS_LABELS = {
    "proposed": "Proposé",
    "approved": "Approuvé",
    "rejected": "Rejeté",
    "postponed": "Reporté",
    "in_production": "En production",
    "done": "Terminé",
}

LINK_STATUS_LABELS = {"suggested": "Suggéré", "approved": "Approuvé", "rejected": "Rejeté", "applied": "Appliqué"}

INTEGRATION_STATUS = {
    "connected": ("Connecté", "ok"),
    "active": ("Actif", "ok"),
    "configured": ("Configuré — non vérifié", "warn"),
    "no_credits": ("Crédits épuisés", "warn"),
    "error": ("Erreur", "bad"),
    "not_configured": ("Non connecté", "off"),
}

ATTENTION_LABELS = {
    "human_review": "Jugement humain demandé par la QA",
    "rewrite_limit_reached": "Réécriture automatique déjà utilisée",
    "research_required": "Recherche insuffisante",
    "budget_exceeded": "Budget dépassé",
}

VERDICT_ORDER = {"unsupported": 0, "partial": 1, "supported": 2}

VALUE_LABELS = {"high": "Élevée", "medium": "Moyenne", "low": "Faible"}
PAGE_TYPE_LABELS = {"article": "Article", "commercial": "Commerciale", "course": "Cours", "utility": "Utilitaire"}
ROLE_LABELS = {"pillar": "Pilier", "support": "Support", "commercial": "Commerciale", "utility": "Utilitaire"}
GROUP_LABELS = {"epfl": "EPFL", "hors_epfl": "Hors EPFL"}
SEVERITY_LABELS = {"high": "Élevée", "medium": "Moyenne", "low": "Faible"}
RISK_LABELS = {"low": "Faible", "medium": "Moyen", "high": "Élevé"}
SUBJECT_LABELS = {"maths": "Maths", "physique": "Physique", "informatique": "Informatique"}
MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
          "novembre", "décembre"]


def money(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    return f"{value:,.{digits}f} $".replace(",", " ")


def month_label(month: str) -> str:
    year, m = month.split("-")
    return f"{MONTHS[int(m) - 1].capitalize()} {year}"


def short_url(url: str | None) -> str:
    if not url:
        return "—"
    return url.replace("https://", "").replace("http://", "").replace("www.", "")


def fmt_date(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return str(value)


def clean_sentence(text: str) -> str:
    """Retire les marques Markdown résiduelles d'une phrase extraite (fact-check)."""
    text = re.sub(r"[*_`]+", "", text or "")
    return re.sub(r"\s+([.,;:!?»])", r"\1", text).strip()


def strip_refs(text: str | None) -> str:
    """Retire les références internes (« benchmark:<sujet> ») des textes affichés."""
    return re.sub(r"\s*benchmark:\S+", "", text or "").strip()


def attention(reason: str) -> str:
    return ATTENTION_LABELS.get(reason, reason)


def register(env) -> None:
    env.globals.update(
        SOURCE_BADGES=SOURCE_BADGES,
        COVERAGE_LABELS=COVERAGE_LABELS,
        ACTION_LABELS=ACTION_LABELS,
        PAGE_STATUS_LABELS=PAGE_STATUS_LABELS,
        PLAN_STATUS_LABELS=PLAN_STATUS_LABELS,
        LINK_STATUS_LABELS=LINK_STATUS_LABELS,
        INTEGRATION_STATUS=INTEGRATION_STATUS,
        VALUE_LABELS=VALUE_LABELS,
        PAGE_TYPE_LABELS=PAGE_TYPE_LABELS,
        ROLE_LABELS=ROLE_LABELS,
        GROUP_LABELS=GROUP_LABELS,
        SEVERITY_LABELS=SEVERITY_LABELS,
        RISK_LABELS=RISK_LABELS,
        SUBJECT_LABELS=SUBJECT_LABELS,
        VERDICT_ORDER=VERDICT_ORDER,
    )
    env.filters.update(strip_refs=strip_refs, clean_sentence=clean_sentence, attention=attention, money=money, month_label=month_label, short_url=short_url, fmt_date=fmt_date)
