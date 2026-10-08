import pytest

from seo_os.config import TaskSpec
from seo_os.costs import BudgetExceeded, CostTracker, Usage, compute_cost
from seo_os.mathcheck import check_exercise, parse_number
from seo_os.research import quote_in_text
from seo_os.schemas import MathExercise
from seo_os.search import normalize_url


def test_openai_cost_separates_cached_tokens(pricing):
    usage = Usage(input_tokens=1_000_000, cached_input_tokens=1_000_000, output_tokens=1_000_000)
    p = pricing.price("openai", "gpt-6.1-sol")
    assert compute_cost(pricing, "openai", "gpt-6.1-sol", usage) == pytest.approx(p.input + p.cached_input + p.output)


def test_openai_web_search_calls_are_billed(pricing):
    usage = Usage(web_search_calls=3)
    assert compute_cost(pricing, "openai", "gpt-6-luna", usage) == pytest.approx(3 * pricing.openai_web_search_call_usd)


def test_anthropic_cache_write_is_billed_at_multiplier(pricing):
    usage = Usage(cache_write_tokens=1_000_000)
    p = pricing.price("anthropic", "claude-sonnet-5-5")
    expected = p.input * pricing.anthropic_cache_write_multiplier
    assert compute_cost(pricing, "anthropic", "claude-sonnet-5-5", usage) == pytest.approx(expected)


def test_unknown_model_price_raises(pricing):
    with pytest.raises(KeyError):
        pricing.price("openai", "modele-inexistant")


def test_budget_precheck_blocks_expensive_call(pricing):
    tracker = CostTracker(scope="t", pricing=pricing, hard_usd=0.01)
    spec = TaskSpec(task="write", provider="anthropic", model="claude-sonnet-5-5", max_output_tokens=16000)
    with pytest.raises(BudgetExceeded):
        tracker.check_budget(spec, prompt_chars=10_000)


def test_quote_matching_tolerates_typography_and_ellipsis():
    source = "L’examen suisse de maturité a lieu deux fois par an.\nLes candidats doivent s’inscrire en ligne."
    assert quote_in_text("L'examen suisse de maturité a lieu deux fois par an", source)
    assert quote_in_text("L'examen suisse de maturité … doivent s'inscrire en ligne", source)
    assert not quote_in_text("L'examen a lieu trois fois par an dans toute la Suisse", source)
    assert not quote_in_text("", source)


def test_normalize_url_strips_tracking_and_trailing_slash():
    assert normalize_url("https://WWW.ge.ch/page/?utm_source=x&a=1#top") == "https://www.ge.ch/page?a=1"


@pytest.mark.parametrize("raw,expected", [("3", 3), ("-1/2", -0.5), ("\\frac{1}{2}", 0.5), ("0,5", 0.5)])
def test_parse_number(raw, expected):
    assert float(parse_number(raw)) == pytest.approx(expected)


def test_parse_number_sqrt():
    assert float(parse_number("\\sqrt{2}")) == pytest.approx(2**0.5)


def test_mathcheck_accepts_correct_eigen_data():
    ex = MathExercise.model_validate(
        {
            "label": "ex",
            "matrix": [["2", "1"], ["1", "2"]],
            "eigenvalues": ["1", "3"],
            "eigenpairs": [{"eigenvalue": "3", "vector": ["1", "1"]}, {"eigenvalue": "1", "vector": ["1", "-1"]}],
        }
    )
    assert check_exercise(ex)["ok"]


def test_mathcheck_flags_wrong_eigenvalue_and_vector():
    ex = MathExercise.model_validate(
        {
            "label": "ex",
            "matrix": [["2", "1"], ["1", "2"]],
            "eigenvalues": ["1", "4"],
            "eigenpairs": [{"eigenvalue": "3", "vector": ["1", "-1"]}],
        }
    )
    report = check_exercise(ex)
    assert not report["ok"]
    assert any("4" in e for e in report["errors"])
    assert any("A·v" in e for e in report["errors"])
