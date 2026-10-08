"""Interface en ligne de commande de la V0.

    seo-os research  [--topic ID ...] [--search manual|web|both] [--force]
    seo-os run       [--topic ID ...] [--config A,B,C] [--search ...] [--parallel N] [--force]
    seo-os review    TOPIC CONFIG --minutes M --corrections N --sections N --score S --deliverable oui|non
    seo-os compare
    seo-os seed --demo | seo-os create-user EMAIL | seo-os serve | seo-os db-upgrade
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

from . import benchmark
from .config import (
    DEFAULT_OUT,
    DEFAULT_TOPICS,
    Topic,
    load_budgets,
    load_client,
    load_pricing,
    load_profiles,
    load_topics,
    research_profile,
)
from .llm import LLMRouter
from .pipeline import ArticleRun
from .research import build_research_packet, load_packet
from .search import CombinedSearchProvider, ManualUrlsProvider, SearchProvider, WebSearchProvider

log = logging.getLogger("seo_os")


def _select_topics(topics: list[Topic], ids: list[str] | None) -> list[Topic]:
    if ids:
        unknown = set(ids) - {t.id for t in topics}
        if unknown:
            sys.exit(f"Sujet(s) inconnu(s) : {', '.join(sorted(unknown))}")
        selected = [t for t in topics if t.id in ids]
    else:
        selected = [t for t in topics if t.is_ready]
    pending = [t.id for t in selected if not t.is_ready]
    if pending:
        sys.exit(f"Sujet(s) non prêts (status != ready) : {', '.join(pending)}")
    return selected


PROVIDER_CREDENTIALS = {
    "openai": ("OPENAI_API_KEY",),
    "anthropic": ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE"),
}


def _preflight(profiles) -> None:
    """Échoue avant toute dépense si un fournisseur utilisé n'a pas d'identifiants."""
    used = {spec.provider for p in profiles for spec in p.tasks.values()}
    missing = [
        f"{provider} ({' ou '.join(names)})"
        for provider, names in PROVIDER_CREDENTIALS.items()
        if provider in used and not any(os.environ.get(n) for n in names)
    ]
    if missing:
        sys.exit("Identifiants manquants : " + ", ".join(missing) + " — voir .env.example")


def _search_provider(mode: str, router: LLMRouter, exclude_domain: str) -> SearchProvider:
    manual = ManualUrlsProvider()
    if mode == "manual":
        return manual
    web = WebSearchProvider(router, exclude_domains=[exclude_domain])
    return web if mode == "web" else CombinedSearchProvider([manual, web])


def _ensure_research(args, topics: list[Topic]) -> None:
    profiles, pricing, budgets = load_profiles(), load_pricing(), load_budgets()
    client_slug = load_topics(args.topics)[0]
    client = load_client(client_slug)
    router = LLMRouter(research_profile(profiles), pricing, budgets)
    provider = _search_provider(args.search, router, client.domain)
    for topic in topics:
        research_dir = args.out / "research" / topic.id
        if (research_dir / "packet.json").exists() and not args.force_research:
            existing = load_packet(research_dir)
            if existing.usable_sources() and not existing.errors:
                log.info("%s : recherche existante réutilisée (%s)", topic.id, research_dir)
                continue
            log.warning("%s : paquet existant inutilisable (aucune source exploitable ou erreurs), recherche relancée", topic.id)
        log.info("%s : recherche (%s)…", topic.id, args.search)
        packet = build_research_packet(
            topic, client, provider, router, budgets, pricing, research_dir, cost_log=args.out / "costs.jsonl"
        )
        log.info(
            "%s : %d source(s) exploitable(s), %d affirmation(s) vérifiée(s), %.4f $",
            topic.id,
            len(packet.usable_sources()),
            len(packet.verified_claims()),
            packet.cost_usd,
        )


def cmd_research(args) -> None:
    _, topics = load_topics(args.topics)
    args.force_research = args.force
    _preflight([research_profile(load_profiles())])
    _ensure_research(args, _select_topics(topics, args.topic))


def cmd_run(args) -> None:
    client_slug, topics = load_topics(args.topics)
    selected = _select_topics(topics, args.topic)
    profiles, pricing, budgets = load_profiles(), load_pricing(), load_budgets()
    names = [n.strip() for n in args.config.split(",")] if args.config else list(profiles)
    missing = set(names) - set(profiles)
    if missing:
        sys.exit(f"Configuration(s) inconnue(s) : {', '.join(sorted(missing))}")
    _preflight([profiles[n] for n in names])
    _ensure_research(args, selected)
    client = load_client(client_slug)

    jobs = []
    for topic in selected:
        research_dir = args.out / "research" / topic.id
        packet = load_packet(research_dir)
        for name in names:
            out_dir = benchmark.article_dir(args.out, topic.id, name)
            if (out_dir / "result.json").exists() and not args.force:
                log.info("%s/%s : déjà généré (utiliser --force pour régénérer)", topic.id, name)
                continue
            jobs.append(
                ArticleRun(
                    topic=topic,
                    profile=profiles[name],
                    client=client,
                    packet=packet,
                    research_dir=research_dir,
                    router=LLMRouter(profiles[name], pricing, budgets),
                    budgets=budgets,
                    pricing=pricing,
                    out_dir=out_dir,
                    research_share_usd=packet.cost_usd / len(names),
                    cost_log=args.out / "costs.jsonl",
                )
            )

    def run(job: ArticleRun) -> dict:
        log.info("%s/%s : génération…", job.topic.id, job.profile.name)
        return job.run()

    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
        futures = [pool.submit(run, job) for job in jobs]
        for future in as_completed(futures):
            r = future.result()
            log.info(
                "%s/%s : %s — %.4f $ (avec part de recherche) — %s s",
                r["topic"]["id"],
                r["config"]["profile"],
                r["status"],
                r["costs"]["total_with_research_share_usd"],
                r["durations_s"]["total"],
            )
    print(benchmark.build_report(args.out, budgets))


def _yes_no(value: str) -> bool:
    v = value.strip().lower()
    if v in ("oui", "o", "yes", "y", "true", "1"):
        return True
    if v in ("non", "n", "no", "false", "0"):
        return False
    raise argparse.ArgumentTypeError("attendu : oui / non")


def cmd_review(args) -> None:
    benchmark.record_review(
        args.out,
        args.topic_id,
        args.config_name,
        minutes=args.minutes,
        corrections=args.corrections,
        sections_rewritten=args.sections,
        score=args.score,
        deliverable=args.deliverable,
        notes=args.notes,
    )
    print(f"Relecture enregistrée pour {args.topic_id}/{args.config_name}.")


def cmd_compare(args) -> None:
    budgets = load_budgets()
    report = benchmark.build_report(args.out, budgets)
    (args.out / "benchmark_report.md").write_text(report, encoding="utf-8")
    benchmark.write_csv(args.out, args.out / "benchmark.csv")
    print(report)
    print(f"Écrit : {args.out / 'benchmark_report.md'} et {args.out / 'benchmark.csv'}")


def cmd_db_upgrade(args) -> None:
    from .web import migrate

    migrate.upgrade()
    print("Base de données à jour.")


def cmd_seed(args) -> None:
    from .web import db, migrate
    from .web.seed import seed_demo

    migrate.upgrade()
    with db.session_scope() as session:
        client = seed_demo(session, out_root=args.out)
        print(f"Client « {client.name} » initialisé (mode démo).")


def cmd_create_user(args) -> None:
    import getpass

    from sqlalchemy import select

    from .web import db, migrate
    from .web.auth import hash_password
    from .web.models import User

    migrate.upgrade()
    password = args.password or getpass.getpass("Mot de passe : ")
    if len(password) < 10:
        sys.exit("Mot de passe trop court (10 caractères minimum).")
    email = args.email.strip().lower()
    with db.session_scope() as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            session.add(User(email=email, password_hash=hash_password(password)))
            print(f"Utilisateur {email} créé.")
        else:
            user.password_hash = hash_password(password)
            print(f"Mot de passe de {email} mis à jour.")


def cmd_serve(args) -> None:
    import uvicorn

    from .web import db, migrate
    from .web.app import create_app
    from .web.models import Client
    from .web.production import recover_interrupted_runs

    migrate.upgrade()
    with db.session_scope() as session:
        if session.query(Client).count() == 0:
            sys.exit("Aucun client : lancez d'abord `seo-os seed --demo`.")
    recover_interrupted_runs()
    print(f"Cockpit : http://{args.host}:{args.port}")
    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="warning")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seo-os", description="SEO OS — V0 (pipeline + benchmark)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="dossier de sortie (défaut : out/)")
    parser.add_argument("--topics", type=Path, default=DEFAULT_TOPICS, help="fichier des sujets")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    search_help = "manual : URL de topics.yaml ; web : recherche web ; both : les deux (défaut)"

    p = sub.add_parser("research", help="construire (ou reconstruire) les paquets de recherche")
    p.add_argument("--topic", action="append", help="identifiant de sujet (répétable)")
    p.add_argument("--search", choices=["manual", "web", "both"], default="both", help=search_help)
    p.add_argument("--force", action="store_true", help="refaire la recherche même si elle existe")
    p.set_defaults(func=cmd_research)

    p = sub.add_parser("run", help="générer les articles (recherche incluse si absente)")
    p.add_argument("--topic", action="append", help="identifiant de sujet (répétable)")
    p.add_argument("--config", help="profils à exécuter, ex. A,B,C (défaut : tous)")
    p.add_argument("--search", choices=["manual", "web", "both"], default="both", help=search_help)
    p.add_argument("--parallel", type=int, default=1, help="articles générés en parallèle")
    p.add_argument("--force", action="store_true", help="régénérer les articles existants")
    p.add_argument("--force-research", action="store_true", help="refaire aussi la recherche")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("review", help="saisir la relecture humaine d'un article")
    p.add_argument("topic_id")
    p.add_argument("config_name")
    p.add_argument("--minutes", type=float, required=True, help="temps de relecture et correction")
    p.add_argument("--corrections", type=int, required=True, help="nombre de corrections")
    p.add_argument("--sections", type=int, required=True, help="nombre de sections réécrites")
    p.add_argument("--score", type=float, required=True, help="note finale humaine /10")
    p.add_argument("--deliverable", type=_yes_no, required=True, help="livrable au client : oui / non")
    p.add_argument("--notes")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("compare", help="rapport comparatif des configurations")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("serve", help="lancer le cockpit web")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("db-upgrade", help="appliquer les migrations de la base")
    p.set_defaults(func=cmd_db_upgrade)

    p = sub.add_parser("seed", help="initialiser le client démo (carte, pages publiques, plan, articles produits)")
    p.add_argument("--demo", action="store_true", required=True)
    p.set_defaults(func=cmd_seed)

    p = sub.add_parser("create-user", help="créer l'utilisateur du cockpit")
    p.add_argument("email")
    p.add_argument("--password", help="(sinon demandé de façon masquée)")
    p.set_defaults(func=cmd_create_user)
    return parser


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    for noisy in ("httpx", "httpx2", "openai", "anthropic", "trafilatura", "pypdf", "alembic"):
        logging.getLogger(noisy).setLevel(logging.ERROR)
    args.func(args)


if __name__ == "__main__":
    main()
