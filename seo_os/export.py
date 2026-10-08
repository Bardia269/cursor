"""Publication : interface générique + export fichiers (seule implémentation en V0)."""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import markdown as md

from .qa import SOURCE_MARKER_RE, UNVERIFIED_MARKER

MATH_RE = re.compile(r"\$\$.+?\$\$|\$[^$\n]+\$", re.S)


@dataclass
class ArticleExport:
    article_id: str          # identifiant stable (clé d'idempotence en V1)
    title: str
    slug: str
    title_tag: str
    meta_description: str
    markdown: str            # version de relecture (marqueurs [S#] conservés)


class PublishingProvider(Protocol):
    """Contrat commun aux futures cibles (API du site client, CMS headless, export manuel…)."""

    def create_draft(self, article: ArticleExport) -> str: ...

    def update_article(self, external_id: str, article: ArticleExport) -> None: ...

    def schedule_article(self, external_id: str, publish_at: str) -> None: ...

    def publish_article(self, external_id: str) -> None: ...


def render_html(markdown_text: str, title_tag: str, meta_description: str) -> str:
    """HTML publiable : marqueurs de sources retirés, [À VÉRIFIER] surligné, LaTeX préservé."""
    clean = SOURCE_MARKER_RE.sub("", markdown_text)
    clean = re.sub(r"[ \t]+([.,;:!?])", r"\1", clean)
    formulas: list[str] = []

    def protect(match: re.Match) -> str:
        formulas.append(match.group(0))
        return f"@@MATH{len(formulas) - 1}@@"

    protected = MATH_RE.sub(protect, clean)
    body = md.markdown(protected, extensions=["extra", "sane_lists"])
    for i, formula in enumerate(formulas):
        body = body.replace(f"@@MATH{i}@@", html.escape(formula, quote=False))
    body = body.replace(UNVERIFIED_MARKER, f"<mark>{UNVERIFIED_MARKER}</mark>")
    return (
        "<!doctype html>\n<html lang=\"fr-CH\">\n<head>\n<meta charset=\"utf-8\">\n"
        f"<title>{html.escape(title_tag)}</title>\n"
        f"<meta name=\"description\" content=\"{html.escape(meta_description)}\">\n"
        "</head>\n<body>\n<article>\n"
        f"{body}\n</article>\n</body>\n</html>\n"
    )


class ExportProvider:
    """Écrit l'article en Markdown, HTML et JSON dans un dossier. Pas de publication en V0."""

    def __init__(self, out_dir: Path):
        self.out_dir = out_dir

    def create_draft(self, article: ArticleExport) -> str:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "article.md").write_text(article.markdown, encoding="utf-8")
        (self.out_dir / "article.html").write_text(
            render_html(article.markdown, article.title_tag, article.meta_description), encoding="utf-8"
        )
        (self.out_dir / "article.json").write_text(
            json.dumps(article.__dict__, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return str(self.out_dir)

    def update_article(self, external_id: str, article: ArticleExport) -> None:
        self.create_draft(article)

    def schedule_article(self, external_id: str, publish_at: str) -> None:
        raise NotImplementedError("Programmation non disponible en V0 (export fichiers uniquement)")

    def publish_article(self, external_id: str) -> None:
        raise NotImplementedError("Publication non disponible en V0 (export fichiers uniquement)")
