# SEO OS

Outil interne de pilotage et de production SEO assistée par IA (premier client : Phassyl).

- **Cockpit** (interface web) : stratégie de couverture EPFL / hors EPFL, bibliothèque de contenus,
  plan mensuel, relecture, fiche page, maillage interne, intégrations et coûts.
- **Pipeline** : recherche documentaire sourcée → brief → rédaction → QA (contrôles en code, fact-check,
  revue IA) → export Markdown / HTML / JSON, avec le coût de chaque appel.

## Démarrage rapide (démo locale)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # renseigner ANTHROPIC_API_KEY (facultatif pour naviguer)

seo-os seed --demo              # crée data/seo_os.db : carte, pages publiques, plan, 3 articles réels
seo-os create-user vous@exemple.ch
seo-os serve                    # → http://127.0.0.1:8000
```

`seo-os seed --demo` est idempotent : il recrée le client démo depuis zéro (vos modifications dans
l'interface sont alors perdues).

## Mode démo : ce qui est réel, ce qui ne l'est pas

Chaque donnée porte un badge selon sa provenance :

| Badge | Signification |
|---|---|
| **RÉEL** | Pages publiques relevées sur phassyl.ch, problèmes réels du site, 3 articles produits par le pipeline (profil D, Anthropic), coûts réels |
| **PROPOSITION** | Notre analyse à valider : carte EPFL / hors EPFL, sujets cibles, actions recommandées, plan, suggestions de liens |
| **VALIDÉ** | Proposition validée ou modifiée dans l'interface |
| **NON CONNECTÉ** | En attente d'une intégration : trafic, impressions, positions, volumes, backlinks |

**Aucune métrique de performance n'est simulée.** Le badge `MODE DÉMO` reste affiché tant que
Search Console, Treg et le site ne sont pas connectés (écran *Intégrations & coûts*).

## Écrans

| Écran | Rôle |
|---|---|
| Vue d'ensemble | Indicateurs, alertes (problèmes du site, contenus à relire), checklist « pour passer en données réelles » |
| Stratégie | Carte EPFL / hors EPFL → segments → clusters → sujets cibles, avec couverture, cannibalisation, valeur business ; tout est modifiable |
| Bibliothèque | Toutes les pages (existantes et nouvelles), filtres, actions groupées, **import CSV / JSON** (chemin prévu pour les 300–400 articles), problèmes du site |
| Plan mensuel | CREATE / UPDATE / MERGE / REWRITE / SKIP ; approuver, rejeter, reporter, modifier, lancer la production |
| Relecture | Contenus produits : statut, qualité, risque factuel, contrôles échoués, modèle, coût |
| Fiche page | Contenu (aperçu, édition, versions), brief, sources et fact-check, QA, métadonnées (aperçu Google), maillage, historique et coûts |
| Maillage interne | Suggestions source → destination, ancre, raison, score ; valider / rejeter (appliquer : après connexion du site) |
| Intégrations & coûts | État de chaque intégration (bouton « Tester »), routage des modèles, coûts par modèle / étape / contenu, appels API |

## Routage des modèles (multi-fournisseur)

Le choix du modèle pour chaque tâche vient uniquement de `config/models.yaml` ; aucune logique métier
n'importe un SDK.

```yaml
defaults:
  research_profile: D     # démo : 100 % Anthropic (Haiku tâches simples, Sonnet rédaction / brief / revue)
  production_profile: D
```

Après signature, avec des crédits OpenAI : passer à `B` (OpenAI pour les tâches simples, Claude pour la
rédaction) ou créer un profil dédié, puis relancer le benchmark (`seo-os run`, `seo-os compare`).
Ajouter un modèle = ajouter son prix dans `config/pricing.yaml` et le référencer dans `config/models.yaml`.

## Passer du mode démo au mode production

Rien à réécrire : seules la configuration et les données changent.

1. **Base** : `DATABASE_URL=postgresql+psycopg://…` (`pip install -e ".[postgres]"`), puis `seo-os db-upgrade`.
2. **Secrets** : `SEO_OS_SECRET_KEY`, `SEO_OS_SECURE_COOKIES=1` derrière HTTPS, clés API dans `.env`.
3. **Intégrations** (interfaces prêtes dans `seo_os/providers.py`) :
   - `SearchConsoleProvider` — implémentation réelle à écrire avec l'accès du client ;
   - `SEODataProvider` / `TregClient` — client Treg conforme à la doc (authentification, coût via
     `X-Treg-Cost-Micro`, plafond `X-Treg-Route-Max-Cost`, `Idempotency-Key`) ; endpoints à choisir ;
   - `ContentImportProvider` — import fichier déjà opérationnel ; connecteur du nouveau site à venir ;
   - `PublishingProvider` — export fichiers opérationnel ; publication selon la technologie du site ;
   - `BacklinkProvider` — module prévu après signature.
4. **Données** : importer les contenus existants, synchroniser Search Console, puis remplacer la carte
   proposée par la carte calculée.

## Pipeline et benchmark (CLI)

```bash
seo-os run --config D --search manual --topic epfl-analyse-1     # un article
seo-os run --parallel 3                                           # tous les sujets × tous les profils
seo-os review <sujet> <profil> --minutes 6 --corrections 4 --sections 0 --score 8 --deliverable oui
seo-os compare                                                    # → out/benchmark_report.md
```

- Sujets : `benchmark/topics.yaml` · bible client : `client/phassyl.md` · pages du site : `client/phassyl_pages.yaml`
- Budgets (`config/budgets.yaml`) : alerte 1,50 $, arrêt 5 $ par article, 1 réécriture automatique.
- Les sorties vont dans `out/` (non versionné). `demo/` contient les 3 articles de démonstration versionnés.
- Faits : seules les affirmations factuelles ou sensibles portent un marqueur `[S#]` ; chaque citation
  extraite est vérifiée par du code ; une information absente des sources devient `[À VÉRIFIER]`.

## Architecture

| Chemin | Rôle |
|---|---|
| `seo_os/llm.py` | `LLMProvider` (OpenAI, Anthropic, recherche web incluse) + `LLMRouter` (tâche → modèle, coûts, budget, réparation JSON) |
| `seo_os/providers.py` | Interfaces Search Console, données SEO (Treg), backlinks, import de contenus, tests d'état |
| `seo_os/research.py`, `search.py`, `fetch.py` | Recherche documentaire et vérification des citations |
| `seo_os/pipeline.py`, `qa.py`, `mathcheck.py` | Production d'un article et contrôles |
| `seo_os/export.py` | `PublishingProvider` + export |
| `seo_os/web/models.py` | Modèle de données (SQLAlchemy) ; migrations Alembic dans `seo_os/web/migrations/` |
| `seo_os/web/services.py` | Couverture, règles de maillage, import des résultats du pipeline, intégrations |
| `seo_os/web/seed.py` | Données du mode démo (réelles ou propositions explicites) |
| `seo_os/web/app.py`, `templates/`, `static/` | Cockpit (FastAPI + Jinja2 + HTMX, sans build front-end) |
| `config/templates.yaml` | Templates de contenu (sections, composants, schema.org) |

Tests : `pytest` (aucun appel API réel).

## Sécurité

Connexion mono-utilisateur (mot de passe hashé scrypt), cookie de session `HttpOnly` / `SameSite=Strict`
(`Secure` avec `SEO_OS_SECURE_COOKIES=1`), protection CSRF sur toutes les actions, aucune inscription
publique. Les clés restent dans `.env` (ignoré par Git).
