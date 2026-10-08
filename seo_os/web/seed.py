"""Données de démarrage du mode démo.

Tout ce qui est ici est soit RÉEL (pages publiques et problèmes relevés sur phassyl.ch), soit une
PROPOSITION d'analyse (carte, sujets, actions, plan) à valider dans l'interface. Aucune métrique de
performance n'est créée : elles arriveront de Search Console et de Treg.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import DEFAULT_OUT, ROOT, load_client
from .models import Client, Cluster, Page, PlanItem, Segment, SiteIssue, TargetTopic
from .services import import_pipeline_results, refresh_integrations, suggest_structural_links

BASE = "https://phassyl.ch"
DEMO_DIR = ROOT / "demo"  # résultats réels du pipeline (profil D) versionnés pour la démo
PLAN_MONTH = "2026-11"

# Carte proposée : (groupe, segment, offre, valeur, priorité, description, [clusters])
# cluster : (nom, intention, matières, valeur, priorité, [sujets])
# sujet   : (titre, mot-clé, couverture, URL couvrante ou None, note)
TAXONOMY = [
    ("epfl", "Préparer l'entrée à l'EPFL", "/soutien-epfl-semestriel/", "high", 1,
     "Futurs étudiants et familles avant la rentrée : admission, CMS, prérequis.", [
        ("Admission & orientation", "Comprendre l'accès à l'EPFL et choisir sa voie", ["maths"], "high", 1, [
            ("Admission à l'EPFL", "admission EPFL", "covered", "/admission-epfl/", None),
            ("CMS de l'EPFL : pour qui, comment ?", "CMS EPFL", "gap", None, "Année préparatoire officielle : sources epfl.ch"),
            ("Prérequis en maths pour réussir à l'EPFL", "prérequis maths EPFL", "gap", None, None),
        ]),
        ("Préparer la rentrée", "S'organiser avant le premier semestre", [], "high", 2, [
            ("Ressources pour préparer la première année", "ressources étudiants EPFL", "covered", "/ressources-en-ligne-pour-etudiants-epfl/", None),
            ("Préparer sa première année pendant l'été", "préparer première année EPFL", "partial", "/ressources-en-ligne-pour-etudiants-epfl/", "Couvert indirectement par la page ressources"),
        ]),
    ]),
    ("epfl", "BA1 — Matières", "/soutien-epfl-semestriel/", "high", 1,
     "Les cours de première année qui font échouer : c'est le cœur de l'offre premium.", [
        ("Analyse I & II", "Comprendre et réussir l'analyse en BA1", ["maths"], "high", 1, [
            ("Analyse I à l'EPFL", "analyse 1 EPFL", "gap", None, "benchmark:epfl-analyse-1"),
            ("Exercices corrigés d'Analyse I", "exercices analyse 1", "gap", None, None),
            ("Analyse II : ce qui change au 2e semestre", "analyse 2 EPFL", "gap", None, None),
        ]),
        ("Algèbre linéaire", "Maîtriser l'algèbre linéaire universitaire", ["maths"], "high", 1, [
            ("Algèbre linéaire en BA1", "algèbre linéaire EPFL", "partial", "/cours/algebre-lineaire/", "Fiche cours gratuite, pas d'article"),
            ("Valeurs propres et vecteurs propres", "valeurs propres vecteurs propres", "gap", None, "benchmark:valeurs-propres"),
            ("Exercices d'algèbre pour débutants", "exercices algèbre", "partial", "/exercices-dalgebre-pour-debutants/", "Niveau débutant, pas universitaire"),
        ]),
        ("Physique générale", "Réussir la physique de première année", ["physique"], "high", 2, [
            ("Physique générale I (mécanique)", "physique générale EPFL", "partial", "/cours/physique-mecanique/", "Fiche cours gratuite, pas d'article"),
            ("Réussir ses séries de physique", "séries physique EPFL", "gap", None, None),
        ]),
        ("Programmation", "Aborder la programmation sans bagage", ["informatique"], "medium", 3, [
            ("La programmation en première année", "programmation BA1 EPFL", "gap", None, None),
        ]),
        ("Soutien EPFL (offre)", "Page d'offre et contenus qui y mènent", ["maths", "physique"], "high", 1, [
            ("Soutien EPFL semestriel", "soutien EPFL", "covered", "/soutien-epfl-semestriel/", None),
            ("Soutien scolaire EPFL en maths et physique", "soutien scolaire EPFL", "cannibalized", "/soutien-scolaire-epfl-en-physique-et-mathematiques/",
             "Concurrence la page d'offre sur la même intention"),
        ]),
    ]),
    ("epfl", "Examens & réussite", "/soutien-epfl-semestriel/", "high", 1,
     "Sessions, méthodes et gestion de l'échec : moments où l'accompagnement se vend.", [
        ("Sessions d'examens", "Préparer et réussir les examens", [], "high", 1, [
            ("Préparer les examens semestriels", "préparation examens EPFL", "covered", "/preparation-examens-semestriels-epfl/", None),
            ("Réussir ses travaux pratiques", "TP EPFL", "covered", "/reussir-ses-travaux-pratiques-a-lepfl/", None),
            ("Le format des examens de BA1", "examens BA1 EPFL", "gap", None, None),
            ("Que faire après un échec en BA1 ?", "échec BA1 EPFL", "gap", None, "Forte intention, forte valeur"),
        ]),
        ("Méthodes de travail EPFL", "S'organiser face au volume de travail", [], "medium", 2, [
            ("Gestion du temps à l'EPFL", "gestion du temps EPFL", "covered", "/gestion-du-temps-pour-etudes-epfl/", None),
            ("Méthodes de travail en BA1", "méthodes de travail EPFL", "gap", None, None),
        ]),
    ]),
    ("epfl", "Vie étudiante", None, "low", 3,
     "Contenus d'accompagnement à faible valeur commerciale directe.", [
        ("Étudiants internationaux", "S'adapter au système suisse", [], "medium", 3, [
            ("Réussir à l'EPFL en tant qu'étudiant international", "étudiant international EPFL", "covered",
             "/reussir-a-lepfl-en-tant-quetudiant-international/", None),
        ]),
        ("Étudier à Lausanne", "Logistique de la vie étudiante", [], "low", 3, [
            ("Se loger à Lausanne quand on étudie à l'EPFL", "logement étudiant Lausanne", "gap", None, "Valeur business faible"),
        ]),
    ]),
    ("hors_epfl", "Maturité fédérale", "/cours/physique-maturite-federale/", "high", 1,
     "Candidats à l'examen suisse de maturité : produit payant existant.", [
        ("Examen suisse de maturité", "Comprendre l'examen et s'inscrire", [], "high", 1, [
            ("Maturité fédérale : conditions et inscription", "maturité fédérale", "gap", None, "benchmark:maturite-federale"),
            ("Branches et profil de la maturité fédérale", "branches maturité fédérale", "gap", None, None),
            ("Critères de réussite et calcul des points", "réussir maturité fédérale", "gap", None, None),
        ]),
        ("Préparer les branches", "Réviser chaque discipline", ["maths", "physique"], "high", 1, [
            ("Physique pour la maturité fédérale", "physique maturité fédérale", "partial", "/cours/physique-maturite-federale/", "Fiche produit uniquement"),
            ("Mathématiques pour la maturité fédérale", "maths maturité fédérale", "gap", None, None),
            ("Planifier sa préparation", "préparer la maturité fédérale", "gap", None, None),
        ]),
    ]),
    ("hors_epfl", "Secondaire — Genève", "/appui-scolaire-geneve/", "high", 2,
     "Parents d'élèves du cycle d'orientation et du collège.", [
        ("Appui scolaire Genève", "Trouver un appui scolaire à Genève", [], "high", 1, [
            ("Appui scolaire à Genève", "appui scolaire Genève", "cannibalized", "/appui-scolaire-geneve/",
             "3 pages visent la même intention"),
            ("Aide aux devoirs après l'école", "aide aux devoirs Genève", "partial", "/aide-scolaire-apres-lecole-a-geneve/", "À repositionner"),
        ]),
        ("Parcours scolaire genevois", "Comprendre les étapes CO → collège", [], "medium", 2, [
            ("Passage du cycle d'orientation au collège", "passage cycle d'orientation collège Genève", "gap", None, "benchmark:geneve-co-college"),
            ("Réussir la première année du collège", "première année collège Genève", "gap", None, None),
            ("La maturité gymnasiale à Genève", "maturité gymnasiale Genève", "gap", None, None),
        ]),
    ]),
    ("hors_epfl", "Secondaire — Vaud", "/cours-de-soutien-scolaire-lausanne/", "medium", 2,
     "Parents et gymnasiens du canton de Vaud.", [
        ("Soutien scolaire Lausanne", "Trouver un soutien scolaire à Lausanne", [], "medium", 2, [
            ("Soutien scolaire à Lausanne", "soutien scolaire Lausanne", "partial", "/cours-de-soutien-scolaire-lausanne/", "Terminologie à corriger (« lycées »)"),
        ]),
        ("Gymnase vaudois", "Réussir le gymnase", [], "medium", 2, [
            ("Réussir la première année de gymnase", "première année gymnase Vaud", "gap", None, None),
            ("La maturité gymnasiale vaudoise", "maturité gymnasiale Vaud", "gap", None, None),
        ]),
    ]),
    ("hors_epfl", "Cours particuliers en ligne", "/cours-particuliers-de-maths-en-ligne/", "high", 2,
     "Offre transversale (toute la Suisse romande).", [
        ("Cours de maths en ligne", "Trouver un cours particulier de maths", ["maths"], "high", 2, [
            ("Cours particuliers de maths en ligne", "cours particuliers maths en ligne", "covered", "/cours-particuliers-de-maths-en-ligne/", None),
            ("Appui scolaire en mathématiques", "appui scolaire mathématiques", "partial", "/l-appui-scolaire-en-mathematiques/", "Chevauchement possible avec la page cours en ligne"),
            ("Soutien scolaire en Suisse", "soutien scolaire Suisse", "covered", "/soutien-scolaire-suisse/", None),
        ]),
    ]),
    ("hors_epfl", "Université hors EPFL", "/cours-particuliers-de-maths-en-ligne/", "medium", 3,
     "UNIGE, UNIL, HES et adultes en reprise d'études.", [
        ("UNIGE · UNIL · HES", "Réussir les maths à l'université", ["maths"], "medium", 3, [
            ("Les maths en première année à l'UNIL et l'UNIGE", "maths première année université", "gap", None, None),
            ("Prérequis en maths pour une HES", "prérequis maths HES", "gap", None, None),
        ]),
        ("Adultes & reprise d'études", "Reprendre les maths adulte", ["maths"], "low", 3, [
            ("Formation en mathématiques pour adultes", "formation maths adultes", "covered", "/formation-mathematiques-pour-adultes/", None),
        ]),
    ]),
    ("hors_epfl", "Méthodes d'apprentissage", "/cours/masterclass-apprendre-a-apprendre/", "medium", 2,
     "Transversal : capte des leads vers la masterclass gratuite.", [
        ("Réviser efficacement", "Apprendre mieux en moins de temps", [], "medium", 2, [
            ("Rappel actif et répétition espacée", "méthode de révision efficace", "gap", None, "benchmark:rappel-actif-repetition-espacee"),
            ("Apprendre à apprendre", "apprendre à apprendre", "partial", "/cours/masterclass-apprendre-a-apprendre/", "Fiche masterclass uniquement"),
            ("Gérer le stress des examens", "stress examens", "gap", None, "Sujet sensible : relecture humaine obligatoire"),
        ]),
    ]),
]

# Rôle, template et action proposée pour les pages publiques connues (URL relative).
PAGE_PROPOSALS: dict[str, dict] = {
    "/appui-scolaire-geneve/": dict(role="commercial", template="local_service_page", action="UPDATE",
        rationale="Page commerciale de référence pour Genève : y consolider le contenu utile des deux articles Genève et harmoniser les chiffres affichés."),
    "/soutien-scolaire-personnalise-a-geneve/": dict(role="support", template="educational_article", action="MERGE",
        target="/appui-scolaire-geneve/", rationale="Vise la même intention (« soutien scolaire Genève ») que la page commerciale : fusionner puis rediriger."),
    "/aide-scolaire-apres-lecole-a-geneve/": dict(role="support", template="educational_article", action="REPOSITION",
        rationale="Recentrer sur l'aide aux devoirs après l'école (intention distincte) et retirer les statistiques non sourcées (95 %, 80 %, 98 %)."),
    "/cours-de-soutien-scolaire-lausanne/": dict(role="commercial", template="local_service_page", action="UPDATE",
        rationale="Terminologie vaudoise (gymnase, pas lycée) et chiffres à harmoniser avec les autres pages."),
    "/soutien-scolaire-epfl-en-physique-et-mathematiques/": dict(role="support", template="pillar_guide", action="REPOSITION",
        rationale="Concurrence la page d'offre /soutien-epfl-semestriel/ sur la même intention : en faire un guide informationnel qui renvoie vers l'offre."),
    "/accompagnement-premium/": dict(role="commercial", template="offer_page", action="UPDATE",
        rationale="Le titre « Abonnement soutien EPFL » contredit la promesse « ni abonnement, ni forfait » : clarifier l'offre."),
    "/soutien-epfl-semestriel/": dict(role="commercial", template="offer_page"),
    "/cours-particuliers-de-maths-en-ligne/": dict(role="commercial", template="offer_page"),
    "/l-appui-scolaire-en-mathematiques/": dict(role="commercial", template="offer_page"),
    "/soutien-scolaire-suisse/": dict(role="commercial", template="local_service_page"),
    "/cours/physique-maturite-federale/": dict(role="commercial", template="course_page"),
    "/cours/algebre-lineaire/": dict(role="commercial", template="course_page"),
    "/cours/mathematiques-analyse/": dict(role="commercial", template="course_page"),
    "/cours/physique-mecanique/": dict(role="commercial", template="course_page"),
    "/cours/masterclass-apprendre-a-apprendre/": dict(role="commercial", template="course_page"),
}

SITE_ISSUES = [
    dict(kind="placeholder", severity="high", title="Page de test « Template » publiée",
         detail="Une page de modèle vide est accessible publiquement et listée dans le blog.", urls=["/template/"]),
    dict(kind="inconsistent_info", severity="high", title="Nombre de professeurs incohérent : 31, 50 ou 173",
         detail="Le même indicateur change selon la page. À harmoniser et à définir avant toute réutilisation.",
         urls=["/cours-de-soutien-scolaire-lausanne/", "/appui-scolaire-geneve/", "/soutien-epfl-semestriel/", "/a-propos/"]),
    dict(kind="inconsistent_info", severity="medium", title="Taux de réussite affichés sans définition (82 %, 85 %, 95 %, 100 %)",
         detail="Chiffres non sourcés, non datés et parfois contradictoires.",
         urls=["/", "/soutien-epfl-semestriel/", "/aide-scolaire-apres-lecole-a-geneve/", "/a-propos/"]),
    dict(kind="inconsistent_info", severity="medium", title="Deux numéros de téléphone en circulation",
         detail="+41 78 353 80 89 (site) et +41 77 206 98 32 (visible dans les résultats de recherche).", urls=["/", "/contact/"]),
    dict(kind="inconsistent_info", severity="medium", title="« Abonnement soutien EPFL » vs « Ni abonnement, ni forfait »",
         detail="Le titre de la page premium contredit la garantie affichée sur les pages de cours particuliers.",
         urls=["/accompagnement-premium/"]),
    dict(kind="terminology", severity="low", title="« lycées » utilisé pour Lausanne",
         detail="Dans le canton de Vaud, on parle de gymnase. Terme français à corriger.", urls=["/cours-de-soutien-scolaire-lausanne/"]),
    dict(kind="cannibalization", severity="high", title="3 pages ciblent « soutien / appui scolaire Genève »",
         detail="Elles se concurrencent sur la même intention : une seule devrait porter la requête.",
         urls=["/appui-scolaire-geneve/", "/soutien-scolaire-personnalise-a-geneve/", "/aide-scolaire-apres-lecole-a-geneve/"]),
    dict(kind="crawlability", severity="low", title="Protection anti-bot sur certains robots",
         detail="Certaines méthodes de crawl reçoivent une page d'attente. Pour l'inventaire : sitemap ou export fourni par le client.",
         urls=["/"]),
]

# Plan proposé : (action, titre, mot-clé, URL de page ou None, valeur, justification, statut)
PLAN = [
    ("CREATE", "Analyse I à l'EPFL : pourquoi le cours surprend et comment s'y préparer", "analyse 1 EPFL", None, "high",
     "Cluster BA1 sans article ; cœur de l'offre premium. benchmark:epfl-analyse-1", "approved"),
    ("CREATE", "Du cycle d'orientation au collège de Genève : conditions de passage", "passage cycle d'orientation collège Genève", None, "medium",
     "Intention informationnelle distincte des pages Genève existantes ; mène vers l'appui scolaire. benchmark:geneve-co-college", "approved"),
    ("CREATE", "Maturité fédérale : conditions, branches, sessions et préparation", "maturité fédérale", None, "high",
     "Aucune page ne couvre l'examen ; produit payant associé. benchmark:maturite-federale", "approved"),
    ("CREATE", "Rappel actif et répétition espacée : réviser efficacement", "méthode de révision efficace", None, "medium",
     "Capte des leads vers la masterclass gratuite. benchmark:rappel-actif-repetition-espacee", "proposed"),
    ("CREATE", "Valeurs propres et vecteurs propres : comprendre et calculer", "valeurs propres vecteurs propres", None, "low",
     "Tutoriel technique, appui du cours gratuit d'algèbre linéaire. benchmark:valeurs-propres", "proposed"),
    ("CREATE", "CMS de l'EPFL : pour qui et comment s'y préparer", "CMS EPFL", None, "high",
     "Sujet manquant à forte intention dans « Préparer l'entrée à l'EPFL ».", "proposed"),
    ("CREATE", "Que faire après un échec en BA1 ?", "échec BA1 EPFL", None, "high",
     "Moment de décision : forte valeur pour l'accompagnement EPFL.", "proposed"),
    ("CREATE", "Mathématiques pour la maturité fédérale", "maths maturité fédérale", None, "high",
     "Branche manquante du segment maturité fédérale.", "proposed"),
    ("UPDATE", "Appui scolaire Genève : consolider la page de référence", "appui scolaire Genève", "/appui-scolaire-geneve/", "high",
     "Absorber les articles Genève qui la concurrencent, harmoniser les chiffres.", "proposed"),
    ("MERGE", "Fusionner « Soutien scolaire personnalisé à Genève » dans la page de référence", "soutien scolaire Genève",
     "/soutien-scolaire-personnalise-a-geneve/", "medium", "Cannibalisation : même intention que /appui-scolaire-geneve/.", "proposed"),
    ("UPDATE", "Repositionner « Aide scolaire après l'école à Genève »", "aide aux devoirs Genève",
     "/aide-scolaire-apres-lecole-a-geneve/", "medium", "Recentrer l'intention ; retirer les statistiques non sourcées.", "proposed"),
    ("UPDATE", "Soutien scolaire Lausanne : terminologie et chiffres", "soutien scolaire Lausanne",
     "/cours-de-soutien-scolaire-lausanne/", "medium", "« lycées » → gymnases ; chiffres à harmoniser.", "proposed"),
    ("REWRITE", "Transformer « Soutien scolaire EPFL en physique et maths » en guide", "soutien scolaire EPFL",
     "/soutien-scolaire-epfl-en-physique-et-mathematiques/", "high", "Cannibalise la page d'offre : réécrire en guide qui y renvoie.", "proposed"),
    ("SKIP", "Se loger à Lausanne quand on étudie à l'EPFL", "logement étudiant Lausanne", None, "low",
     "Valeur business trop faible pour ce mois-ci.", "proposed"),
]


def seed_demo(session: Session, client_slug: str = "phassyl", out_root: Path = DEFAULT_OUT,
              demo_root: Path | None = DEMO_DIR) -> Client:
    """Crée (ou recrée) le client démo. Idempotent : supprime d'abord les données du client."""
    ctx = load_client(client_slug)
    existing = session.scalar(select(Client).where(Client.slug == client_slug))
    if existing is not None:
        _delete_client(session, existing)
    client = Client(slug=client_slug, name="Phassyl", domain=ctx.domain, monthly_target=60,
                    announced_content_count="300–400", settings={"plan_month": PLAN_MONTH})
    session.add(client)
    session.flush()

    pages_by_path: dict[str, Page] = {}
    for p in ctx.pages:
        path = p.url.removeprefix(BASE)
        page = Page(client_id=client.id, url=p.url, external_key=p.url, slug=path.strip("/").split("/")[-1] or None,
                    title=p.title, page_type=p.type, origin="existing", status="published",
                    primary_keyword=p.target_keyword, source="public")
        session.add(page)
        pages_by_path[path] = page
    template_page = Page(client_id=client.id, url=f"{BASE}/template/", external_key=f"{BASE}/template/", slug="template",
                         title="Template", page_type="article", origin="existing", status="published", source="public")
    session.add(template_page)
    pages_by_path["/template/"] = template_page
    session.flush()

    for path, prop in PAGE_PROPOSALS.items():
        page = pages_by_path.get(path)
        if page is None:
            continue
        page.role, page.template = prop.get("role"), prop.get("template")
        if prop.get("action"):
            page.recommended_action, page.action_rationale, page.action_source = prop["action"], prop["rationale"], "proposal"
            if prop.get("target"):
                page.action_target_page_id = pages_by_path[prop["target"]].id
    template_page.recommended_action, template_page.action_source = "DELETE", "proposal"
    template_page.action_rationale = "Page de test publiée par erreur : à dépublier (aucune valeur SEO ni business)."

    for g_pos, (group, seg_name, offer, value, prio, desc, clusters) in enumerate(TAXONOMY):
        segment = Segment(client_id=client.id, group=group, name=seg_name, description=desc,
                          offer_url=f"{BASE}{offer}" if offer else None, business_value=value, priority=prio,
                          position=g_pos, source="proposal")
        session.add(segment)
        for c_pos, (c_name, intent, subjects, c_value, c_prio, topics) in enumerate(clusters):
            cluster = Cluster(segment=segment, name=c_name, intent=intent, subjects=subjects, business_value=c_value,
                              priority=c_prio, position=c_pos, source="proposal")
            session.add(cluster)
            for t_pos, (title, keyword, coverage, url, note) in enumerate(topics):
                page = pages_by_path.get(url) if url else None
                session.add(TargetTopic(cluster=cluster, title=title, primary_keyword=keyword, coverage_status=coverage,
                                        page=page, notes=note, position=t_pos, business_value=c_value,
                                        priority=c_prio, source="proposal"))
                if page is not None and page.cluster is None:
                    page.cluster = cluster
                    if page.role is None:
                        page.role = "support" if page.page_type == "article" else page.role
                    if page.template is None and page.page_type == "article":
                        page.template = "educational_article"
    session.flush()

    for issue in SITE_ISSUES:
        urls = [f"{BASE}{u}" for u in issue["urls"]]
        page = pages_by_path.get(issue["urls"][0]) if len(issue["urls"]) == 1 else None
        session.add(SiteIssue(client_id=client.id, page_id=page.id if page else None, kind=issue["kind"],
                              severity=issue["severity"], title=issue["title"], detail=issue["detail"], urls=urls,
                              source="public"))

    topics_by_keyword = {t.primary_keyword: t for t in session.scalars(
        select(TargetTopic).join(Cluster).join(Segment).where(Segment.client_id == client.id))}
    for action, title, keyword, url, value, rationale, status in PLAN:
        page = pages_by_path.get(url) if url else None
        topic = topics_by_keyword.get(keyword)
        session.add(PlanItem(client_id=client.id, month=PLAN_MONTH, action=action, title=title, primary_keyword=keyword,
                             page=page, target_topic_id=topic.id if topic else None,
                             cluster_id=(topic.cluster_id if topic else (page.cluster_id if page else None)),
                             template=(page.template if page else None), business_value=value, rationale=rationale,
                             status=status, source="proposal"))
    session.flush()

    for root in (demo_root, out_root):  # out/ (productions locales) complète ou remplace demo/
        if root is not None and root.exists():
            import_pipeline_results(session, client, root)
    session.flush()
    suggest_structural_links(session, client)
    refresh_integrations(session, client, live=False)
    return client


def _delete_client(session: Session, client: Client) -> None:
    from .models import ApiCall, Integration, LinkSuggestion, PageMetric, PageVersion, PipelineRun

    page_ids = [p for (p,) in session.execute(select(Page.id).where(Page.client_id == client.id))]
    for model in (LinkSuggestion, PlanItem, SiteIssue, Integration, ApiCall):
        session.query(model).filter(model.client_id == client.id).delete(synchronize_session=False)
    if page_ids:
        session.query(Page).filter(Page.id.in_(page_ids)).update({Page.current_version_id: None}, synchronize_session=False)
        session.query(TargetTopic).filter(TargetTopic.page_id.in_(page_ids)).update({TargetTopic.page_id: None}, synchronize_session=False)
        for model in (PageMetric, PageVersion, PipelineRun):
            session.query(model).filter(model.page_id.in_(page_ids)).delete(synchronize_session=False)
    for segment in session.scalars(select(Segment).where(Segment.client_id == client.id)):
        session.delete(segment)
    session.flush()
    session.query(Page).filter(Page.client_id == client.id).update({Page.action_target_page_id: None}, synchronize_session=False)
    session.query(Page).filter(Page.client_id == client.id).delete(synchronize_session=False)
    session.delete(client)
    session.flush()
    session.expunge_all()  # les suppressions en masse laissent des objets périmés en mémoire
