"""Contrôles qualité déterministes (sans IA) sur l'article Markdown et ses métadonnées."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit

from .config import ClientContext, Topic
from .schemas import Brief, Metadata
from .search import matches_domain, normalize_url

TITLE_TAG_RANGE = (30, 65)
META_DESCRIPTION_RANGE = (120, 160)
SLUG_MAX_LENGTH = 75
MIN_H2 = 3
WORD_COUNT_TOLERANCE = 0.30
MIN_WORD_COUNT = 600
INTERNAL_LINKS_RANGE = (2, 6)
MAX_KEYWORD_DENSITY = 0.025
KEYWORD_INTRO_WORDS = 120

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SOURCE_MARKER_RE = re.compile(r"\[(S\d+(?:\s*,\s*S\d+)*)\]")
UNVERIFIED_MARKER = "[À VÉRIFIER]"

# Termes du système scolaire français à proscrire (bible §5), en plus de ceux de la bible.
FORBIDDEN_TERMS = [
    "bac",
    "baccalauréat",
    "lycée",
    "lycéen",
    "lycéens",
    "prépa",
    "sur 20",
    "euros",
    "€",
    "réussite garantie",
    "garanti à 100",
]

# Tournures de remplissage typiques des textes générés.
FILLER_PHRASES = [
    "dans le monde d'aujourd'hui",
    "dans le monde actuel",
    "il est important de noter",
    "il convient de noter",
    "force est de constater",
    "dans cet article, nous allons",
    "dans cet article nous allons",
    "n'hésitez pas à",
    "plongeons",
    "que vous soyez",
    "en somme",
    "en conclusion",
    "véritable atout",
    "incontournable",
    "il va sans dire",
    "au cœur de",
    "décortiquer",
]


@dataclass
class Check:
    name: str
    passed: bool
    severity: str  # "high" | "medium" | "low"
    detail: str


def _fold(text: str) -> str:
    """Minuscules sans accents, pour les comparaisons de mots-clés."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c)).replace("’", "'")


def strip_markers(markdown: str) -> str:
    return SOURCE_MARKER_RE.sub("", markdown)


def body_words(markdown: str) -> list[str]:
    text = strip_markers(markdown)
    text = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)
    text = re.sub(r"\$[^$\n]+\$", " formule ", text)
    text = LINK_RE.sub(r"\1", text)
    text = re.sub(r"[#*_>`|]", " ", text)
    return re.findall(r"[\wÀ-ÿ'’-]+", text)


def headings(markdown: str) -> list[tuple[int, str]]:
    out = []
    in_code = False
    for line in markdown.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        m = HEADING_RE.match(line)
        if m and not in_code:
            out.append((len(m.group(1)), m.group(2)))
    return out


def links(markdown: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for m in LINK_RE.finditer(markdown)]


def source_markers(markdown: str) -> list[str]:
    ids: list[str] = []
    for m in SOURCE_MARKER_RE.finditer(markdown):
        ids += [s.strip() for s in m.group(1).split(",")]
    return ids


def _contains_term(folded_text: str, term: str) -> bool:
    folded_term = _fold(term)
    if not folded_term[0].isalnum():
        return folded_term in folded_text
    return re.search(rf"(?<![\w]){re.escape(folded_term)}(?![\w])", folded_text) is not None


def run_checks(
    markdown: str,
    metadata: Metadata,
    brief: Brief,
    topic: Topic,
    client: ClientContext,
    valid_source_ids: set[str],
) -> list[Check]:
    checks: list[Check] = []

    def add(name: str, passed: bool, severity: str, detail: str) -> None:
        checks.append(Check(name, passed, severity, detail))

    # Structure
    hs = headings(markdown)
    h1 = [h for lvl, h in hs if lvl == 1]
    h2 = [h for lvl, h in hs if lvl == 2]
    add("h1_unique", len(h1) == 1, "high", f"{len(h1)} H1")
    add("h2_minimum", len(h2) >= MIN_H2, "medium", f"{len(h2)} H2 (min {MIN_H2})")
    skipped = [h for i, (lvl, h) in enumerate(hs) if i and lvl > hs[i - 1][0] + 1]
    add("heading_hierarchy", not skipped, "low", f"niveaux sautés : {skipped[:3]}" if skipped else "ok")
    empty_sections = [
        hs[i][1] for i in range(len(hs) - 1) if hs[i][0] >= 2 and hs[i + 1][0] <= hs[i][0]
        and not _section_has_text(markdown, hs[i][1], hs[i + 1][1])
    ]
    add("no_empty_section", not empty_sections, "medium", f"{empty_sections[:3]}" if empty_sections else "ok")

    # Longueur
    words = len(body_words(markdown))
    target = brief.recommended_word_count or 0
    low, high = target * (1 - WORD_COUNT_TOLERANCE), target * (1 + WORD_COUNT_TOLERANCE)
    add("word_count_min", words >= MIN_WORD_COUNT, "high", f"{words} mots")
    if target:
        add("word_count_vs_brief", low <= words <= high, "low", f"{words} mots (brief : {target} ±30 %)")

    # Métadonnées
    tl, ml = len(metadata.title_tag), len(metadata.meta_description)
    add("title_tag_length", TITLE_TAG_RANGE[0] <= tl <= TITLE_TAG_RANGE[1], "medium", f"{tl} caractères")
    add(
        "meta_description_length",
        META_DESCRIPTION_RANGE[0] <= ml <= META_DESCRIPTION_RANGE[1],
        "medium",
        f"{ml} caractères",
    )
    add(
        "slug_format",
        bool(SLUG_RE.match(metadata.slug)) and len(metadata.slug) <= SLUG_MAX_LENGTH,
        "high",
        metadata.slug,
    )
    existing_slugs = {urlsplit(p.url).path.strip("/").split("/")[-1] for p in client.pages}
    add("slug_unique", metadata.slug not in existing_slugs, "high", metadata.slug)
    existing_titles = {_fold(p.title) for p in client.pages}
    add(
        "title_unique",
        _fold(metadata.title_tag) not in existing_titles and (not h1 or _fold(h1[0]) not in existing_titles),
        "high",
        metadata.title_tag,
    )

    # Mot-clé principal
    kw = _fold(topic.primary_keyword)
    folded_body = _fold(" ".join(body_words(markdown)))
    intro = _fold(" ".join(body_words(markdown)[:KEYWORD_INTRO_WORDS]))
    kw_tokens = [t for t in kw.split() if len(t) > 2]
    add(
        "keyword_in_title_or_h1",
        all(t in _fold(metadata.title_tag) or (h1 and t in _fold(h1[0])) for t in kw_tokens),
        "low",
        topic.primary_keyword,
    )
    add("keyword_in_intro", all(t in intro for t in kw_tokens), "low", f"{KEYWORD_INTRO_WORDS} premiers mots")
    occurrences = folded_body.count(kw)
    density = occurrences * max(1, len(kw.split())) / max(1, words)
    add("keyword_density", density <= MAX_KEYWORD_DENSITY, "medium", f"{occurrences} occurrence(s), {density:.1%}")

    # Liens
    all_links = links(markdown)
    invalid = [u for _, u in all_links if not (urlsplit(u).scheme in ("http", "https") and urlsplit(u).netloc)]
    add("links_valid_urls", not invalid, "high", f"{invalid[:3]}" if invalid else "ok")
    internal = [u for _, u in all_links if matches_domain(u, [client.domain])]
    known = {normalize_url(u) for u in client.page_urls}
    unknown_internal = [u for u in internal if normalize_url(u) not in known]
    add("internal_links_known", not unknown_internal, "high", f"{unknown_internal[:3]}" if unknown_internal else "ok")
    add(
        "internal_links_count",
        INTERNAL_LINKS_RANGE[0] <= len(internal) <= INTERNAL_LINKS_RANGE[1],
        "medium",
        f"{len(internal)} lien(s) interne(s)",
    )
    dup = sorted({u for u in internal if internal.count(u) > 1})
    add("internal_links_no_duplicates", not dup, "low", f"{dup[:3]}" if dup else "ok")
    external = [u for u in all_links if not matches_domain(u[1], [client.domain])]
    add("no_external_links_in_body", not external, "low", f"{len(external)} lien(s) externe(s)")
    cta = normalize_url(topic.conversion_target.primary)
    add("cta_link_present", any(normalize_url(u) == cta for u in internal), "high", topic.conversion_target.primary)

    # Sources et vérifications
    markers = source_markers(markdown)
    unknown_markers = sorted(set(markers) - valid_source_ids)
    add("source_markers_valid", not unknown_markers, "high", f"{unknown_markers}" if unknown_markers else "ok")
    unverified = markdown.count(UNVERIFIED_MARKER)
    add("no_unverified_markers", unverified == 0, "medium", f"{unverified} × {UNVERIFIED_MARKER}")

    # Terminologie et style
    folded_md = _fold(strip_markers(markdown))
    forbidden = [t for t in FORBIDDEN_TERMS if _contains_term(folded_md, t)]
    add("forbidden_terms", not forbidden, "medium", f"{forbidden}" if forbidden else "ok")
    fillers = [p for p in FILLER_PHRASES if _fold(p) in folded_md]
    add("filler_phrases", len(fillers) <= 1, "low", f"{fillers}" if fillers else "ok")

    # Markdown bien formé
    add("code_fences_balanced", markdown.count("```") % 2 == 0, "medium", "")
    add("math_blocks_balanced", markdown.count("$$") % 2 == 0, "medium", "")
    return checks


def _section_has_text(markdown: str, heading: str, next_heading: str) -> bool:
    start = markdown.find(heading)
    end = markdown.find(next_heading, start + len(heading))
    if start == -1 or end == -1:
        return True
    return bool(markdown[start + len(heading) : end].replace("#", "").strip())


def summarize(checks: list[Check]) -> dict:
    failed = [c for c in checks if not c.passed]
    return {
        "passed": len(checks) - len(failed),
        "failed": len(failed),
        "failed_high": [c.name for c in failed if c.severity == "high"],
        "checks": [asdict(c) for c in checks],
    }
