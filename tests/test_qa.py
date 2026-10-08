from seo_os import qa
from seo_os.schemas import Metadata

from .conftest import ARTICLE, CTA_URL, make_brief

META = Metadata(
    title_tag="Valeurs propres et vecteurs propres : méthode et exercices",
    meta_description=(
        "Comprenez ce que sont les valeurs propres et vecteurs propres, puis apprenez à les calculer pas "
        "à pas grâce à des exercices corrigés et commentés."
    ),
    slug="valeurs-propres-vecteurs-propres",
)


def _failed(markdown, topic, client, meta=META, sources=frozenset({"S1"})):
    checks = qa.run_checks(markdown, meta, make_brief(), topic, client, set(sources))
    return {c.name for c in checks if not c.passed}


def test_clean_article_passes_blocking_checks(topic, client):
    failed = _failed(ARTICLE, topic, client)
    assert not failed & {"h1_unique", "links_valid_urls", "internal_links_known", "cta_link_present",
                         "source_markers_valid", "slug_format", "slug_unique", "forbidden_terms"}


def test_detects_structural_and_link_problems(topic, client):
    bad = ARTICLE.replace("# Valeurs", "## Valeurs").replace(CTA_URL, "https://phassyl.ch/page-inconnue/")
    bad += "\nVoir [ici](notaurl) et la note de 15 sur 20 au bac [S9].\n"
    failed = _failed(bad, topic, client)
    assert {"h1_unique", "internal_links_known", "cta_link_present", "links_valid_urls",
            "source_markers_valid", "forbidden_terms"} <= failed


def test_detects_bad_metadata(topic, client):
    meta = Metadata(title_tag="Trop court", meta_description="Court.", slug="Pas Un Slug")
    failed = _failed(ARTICLE, topic, client, meta=meta)
    assert {"title_tag_length", "meta_description_length", "slug_format"} <= failed


def test_existing_slug_and_title_are_duplicates(topic, client):
    meta = META.model_copy(update={"slug": "algebre-lineaire", "title_tag": client.pages[0].title})
    failed = _failed(ARTICLE, topic, client, meta=meta)
    assert {"slug_unique", "title_unique"} <= failed


def test_unverified_marker_is_reported(topic, client):
    failed = _failed(ARTICLE + "\nLe cours compte 6 crédits [À VÉRIFIER].\n", topic, client)
    assert "no_unverified_markers" in failed


def test_forbidden_term_matching_respects_word_boundaries(topic, client):
    failed = _failed(ARTICLE + "\nLe Bachelor de l'EPFL commence en septembre.\n", topic, client)
    assert "forbidden_terms" not in failed


def test_word_count_ignores_markers_and_formulas():
    assert qa.body_words("Deux mots [S1] $x^2 + y^2$") == ["Deux", "mots", "formule"]
