# SEO OS — V0

Outil interne de production SEO assistée par IA. La V0 ne sert qu'à **prouver la qualité du pipeline et
mesurer son coût** : pas de base de données, pas de dashboard, pas de Docker.

```
sujet → recherche (sources + affirmations vérifiées) → brief → rédaction → métadonnées
      → QA déterministe → fact-check → revue IA → (1 réécriture auto) → Markdown / HTML / JSON + coûts
```

Le benchmark compare trois configurations de modèles sur 5 sujets Phassyl (15 articles) :

| Config | Tâches simples (recherche, extraction, métadonnées, QA) | Brief | Rédaction / réécriture |
|---|---|---|---|
| A | OpenAI `gpt-6-luna` | OpenAI `gpt-6.1-sol` | OpenAI `gpt-6.1-sol` |
| B | OpenAI `gpt-6-luna` | OpenAI `gpt-6.1-sol` | Anthropic `claude-sonnet-5-5` |
| C | OpenAI `gpt-6-luna` | Anthropic `claude-sonnet-5-5` | Anthropic `claude-sonnet-5-5` |

La recherche est faite **une seule fois par sujet** puis partagée par A, B et C : on compare la
rédaction à données égales.

## Installation

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # puis renseigner OPENAI_API_KEY et ANTHROPIC_API_KEY
pytest                 # tests sans appel API
```

Python 3.11+. Les clés ne sont jamais commitées (`.env` est ignoré par Git).

## Lancer le benchmark

```bash
# 1. Recherche documentaire des 5 sujets (URL manuelles + recherche web), puis 15 articles
seo-os run --parallel 3

# Variantes utiles
seo-os research --search manual            # recherche seule, URL de topics.yaml uniquement
seo-os run --topic valeurs-propres --config B
seo-os run --force                         # régénère les articles (la recherche est réutilisée)
seo-os run --force-research                # refait aussi la recherche
```

`--search` : `manual` (URL de `benchmark/topics.yaml`), `web` (recherche web, domaines officiels du
sujet d'abord), `both` (défaut).

## Relire et noter chaque article

Pour chaque article, ouvrir `out/articles/<sujet>/<config>/article.md`, le corriger jusqu'à ce qu'il soit
livrable en **chronométrant**, puis saisir :

```bash
seo-os review valeurs-propres B --minutes 6 --corrections 4 --sections 0 --score 8 --deliverable oui \
  --notes "intro trop longue"
```

- `--minutes` : temps de relecture et de correction
- `--corrections` : nombre de corrections ponctuelles
- `--sections` : nombre de sections réécrites
- `--score` : note finale /10
- `--deliverable` : livrable au client (oui / non)

Conseil : relire les articles **sans regarder la configuration** (dossiers mélangés) pour limiter le biais.

## Comparer

```bash
seo-os compare     # → out/benchmark_report.md + out/benchmark.csv
```

Critères (`config/budgets.yaml`) :
- un article est **livrable** s'il est jugé livrable et relu en **moins de 15 minutes** ;
- objectif : **au moins 4 articles livrables sur 5** pour la configuration retenue ;
- **coût effectif** = coût API (part de recherche incluse) + temps humain × 60 $/h. La configuration
  retenue est celle qui atteint l'objectif avec le coût effectif le plus bas.

## Sorties

```
out/
  costs.jsonl                         chaque appel API : modèle, tâche, tokens, coût, durée, version du prompt
  research/<sujet>/packet.json        sources, affirmations (citation vérifiée mot pour mot ou non)
  research/<sujet>/sources/S#.txt     texte extrait de chaque source
  articles/<sujet>/<config>/
    brief.json                        brief SEO
    article_v1.md, article_v2.md…     historique des versions
    article.md                        version finale de relecture (marqueurs [S#] conservés)
    article.html                      version publiable (marqueurs retirés, [À VÉRIFIER] surligné)
    article.json                      titre, slug, title tag, meta description, Markdown
    result.json                       statut, coûts et durées par étape / modèle / fournisseur,
                                      sources, affirmations vérifiées / non soutenues, QA, versions,
                                      champs de relecture humaine
  benchmark_report.md, benchmark.csv
```

Statuts : `ready_for_review`, `needs_attention` (motif : `human_review`, `rewrite_limit_reached`,
`research_required`, `budget_exceeded`), `failed`.

## Principes appliqués

- **Traçabilité des faits** : seules les affirmations factuelles ou sensibles portent un marqueur
  `[S#]`. Chaque citation extraite d'une source est vérifiée par du code (présente mot pour mot ou non) ;
  le fact-check compare chaque phrase marquée aux preuves. Une information absente des sources est
  marquée `[À VÉRIFIER]`, jamais inventée.
- **Pas d'IA pour le déterministe** (`seo_os/qa.py`) : H1/H2, longueur, title/meta, slug, doublons,
  liens internes connus, CTA, URL valides, marqueurs de sources, termes interdits (« bac », « lycée »…),
  tournures de remplissage. Les exercices de maths sont recalculés avec SymPy (`seo_os/mathcheck.py`).
- **Budget** (`config/budgets.yaml`) : alerte à 1,50 $, arrêt à 5 $ par article (phase de test),
  2 $ par sujet pour la recherche, 1 réécriture automatique. Chaque appel est pré-estimé avant d'être fait.
- **Retries** : retries des SDK (429, 5xx, timeouts, backoff exponentiel) + 1 tentative de réparation
  si une sortie JSON est invalide. Au-delà : statut `failed` avec l'erreur dans `result.json`.

## Configuration

| Fichier | Rôle |
|---|---|
| `config/models.yaml` | tâche → fournisseur:modèle, par configuration |
| `config/pricing.yaml` | prix par million de tokens (sources et date de vérification en tête du fichier) |
| `config/budgets.yaml` | plafonds, retries, critères du benchmark |
| `client/phassyl.md` | bible client (sections `[DÉDUIT]` à valider) |
| `client/phassyl_pages.yaml` | pages du site autorisées pour le maillage et l'anti-cannibalisation |
| `benchmark/topics.yaml` | sujets, mots-clés, valeur business, page de conversion, URL manuelles |
| `prompts/*.md` | prompts versionnés (version + hash enregistrés à chaque appel) |

**Ajouter ou changer un modèle** : ajouter son prix dans `config/pricing.yaml`, puis le référencer dans
`config/models.yaml`. Aucun code à modifier pour OpenAI ou Anthropic. Un nouveau fournisseur = une classe
qui implémente `generate()` (et `web_search()` si besoin) dans `seo_os/llm.py`.

**Modifier un prompt** : éditer `prompts/<nom>.md` et incrémenter `version` dans l'en-tête.

## Architecture (réutilisée en V1)

| Module | Rôle |
|---|---|
| `seo_os/llm.py` | `LLMProvider` (OpenAI, Anthropic) + `LLMRouter` (tâche → modèle, coûts, budget, réparation JSON) |
| `seo_os/search.py` | `SearchProvider` : `ManualUrlsProvider`, `WebSearchProvider`, combinaison |
| `seo_os/fetch.py` | téléchargement + extraction HTML (trafilatura) et PDF (pypdf) |
| `seo_os/research.py` | paquet de recherche : sources, affirmations, vérification des citations |
| `seo_os/pipeline.py` | orchestration d'un article et décision (PASS / REWRITE / HUMAN_REVIEW / RESEARCH_REQUIRED) |
| `seo_os/qa.py`, `seo_os/mathcheck.py` | contrôles déterministes |
| `seo_os/export.py` | `PublishingProvider` + `ExportProvider` (Markdown / HTML / JSON) |
| `seo_os/costs.py` | calcul des coûts, journal, plafonds |
| `seo_os/benchmark.py` | saisie de la relecture humaine, rapport comparatif |

## Limites connues de la V0

- Pas de données SEO (Treg non branché) : les sources viennent d'une recherche documentaire, ce n'est
  pas un classement Google. Les « observations SERP » du brief en sont une approximation.
- Certains sites bloquent les robots (ex. PubMed renvoie 403) : la source est ignorée et signalée dans
  `packet.json`. Les pages qui exigent JavaScript sont aussi ignorées.
- La recherche web passe par l'outil `web_search` d'OpenAI (domaines officiels du sujet d'abord).
- Pas de repli automatique vers un autre modèle en cas de refus d'Anthropic : le benchmark doit mesurer
  le modèle configuré. Un refus produit un statut `failed` explicite.
- Les identifiants et prix des modèles ont été relevés le 2026-10-08 ; vérifier `config/pricing.yaml`
  avant un usage prolongé.
