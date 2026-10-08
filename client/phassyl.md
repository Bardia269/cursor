# Bible client — Phassyl

> **Statut : v0.2 — sections manquantes déduites, en attente de validation par Phassyl.**
> Rédigé à partir des pages publiques de phassyl.ch (consultées entre le 2026-09-30 et le 2026-10-08).
> Les extraits marqués « relevé » ont été lus via un outil automatisé : à revérifier mot pour mot
> avant d'être cités tels quels.
>
> **Marqueur `[DÉDUIT]`** : contenu inféré (connaissance du domaine, cohérence avec le site), pas
> encore validé par Phassyl. Règle de rédaction : un contenu `[DÉDUIT]` peut orienter l'angle, les
> exemples et les conseils, mais ne doit **jamais** être attribué à Phassyl (pas de « nos professeurs
> constatent que… », « chez Phassyl, nous utilisons… ») tant qu'il n'est pas validé.

---

## 0. Fiche d'identité

| Champ | Valeur |
|---|---|
| Nom | Phassyl |
| Site | https://phassyl.ch |
| Langue | Français (Suisse romande) |
| Pays cible | Suisse |
| Zones prioritaires | Genève, Lausanne, Suisse romande ; Suisse entière pour l'offre en ligne |
| Secteur | Soutien scolaire, cours particuliers, accompagnement universitaire (EPFL), formations en ligne |
| Fondateurs | Guillaume et Florent (Huber) — cofondateurs, liés par des liens familiaux. Guillaume : directeur pédagogique. Florent : expert méthodologie. |
| Contact affiché | contact@phassyl.ch — +41 78 353 80 89 (numéro affiché sur l'accueil). Un second numéro (+41 77 206 98 32) apparaît dans certains résultats de recherche → ne jamais l'utiliser. |
| Horaires affichés | Lun–ven 09:00–20:00, sam 09:00–19:00 (relevé) |
| CMS | Site sur mesure — pas de WordPress. Mode de publication à définir en V1. |

---

## 1. Positionnement

Phassyl est une structure romande de soutien scolaire et d'accompagnement académique, du secondaire
jusqu'à l'EPFL, qui se distingue par :

- **Une pédagogie centrée sur l'élève** : « le professeur est celui qui écoute […] et cherche à comprendre
  l'élève et non l'inverse » (relevé, page À propos).
- **Une méthode revendiquée comme fondée sur la recherche** : « Une pédagogie humaine fondée sur des
  recherches scientifiques et l'étude du cerveau » (relevé, accueil).
- **Une spécialisation haut de gamme sur l'EPFL (BA1)**, avec un programme semestriel/annuel en petits groupes.
- **Une offre de préparation à la maturité fédérale** (cours de physique payant).
- **Une offre hybride** : cours particuliers (en ligne et présentiel à Genève), formations vidéo en ligne
  (dont plusieurs gratuites), accompagnement EPFL.
- **Pas d'engagement** : « Ni abonnement, ni forfait » pour les cours particuliers ; cours d'essai offert.

**Différenciation en une phrase `[DÉDUIT]`** : un accompagnement exigeant mené par des enseignants qui
connaissent de l'intérieur les attentes du système suisse (du cycle d'orientation à l'EPFL), avec une
méthode de travail explicite, pas seulement de la répétition d'exercices.

**Promesse éditoriale pour les articles :** aider concrètement l'élève (ou le parent) à comprendre et à
progresser, avec la même posture qu'un bon prof Phassyl : bienveillante, claire, exigeante sur le fond.

---

## 2. Services et pages de destination

| Service | Public | Format | Prix | Page de conversion |
|---|---|---|---|---|
| Cours particuliers / appui scolaire | Secondaire, collège/gymnase, université, adultes | En ligne ; présentiel à Genève | Sur devis ; cours d'essai offert | /appui-scolaire-geneve/ · /cours-de-soutien-scolaire-lausanne/ · /formulaire-demande-cours-particuliers/ · /contact/ |
| Cours particuliers de maths en ligne | Tous niveaux | En ligne | Sur devis | /cours-particuliers-de-maths-en-ligne/ |
| Soutien EPFL semestriel / annuel | Étudiants BA1 EPFL | Petits groupes (moyenne annoncée : 3 élèves), mentorat hebdo, HelpLine 7j/7 | Sur devis, dégressif selon le nombre de matières | /soutien-epfl-semestriel/ · /accompagnement-premium/ |
| Physique pour la maturité fédérale | Candidats à l'examen suisse de maturité (maturité fédérale) | Cours vidéo, 115 leçons, 16 sections, ~10 semaines, 80+ exercices corrigés | CHF 299.– (au lieu de 499.–) | /cours/physique-maturite-federale/ |
| Algèbre linéaire – Être prêt pour l'université | Futurs étudiants universitaires | Cours en ligne | Gratuit | /cours/algebre-lineaire/ |
| Analyse – Être prêt pour l'université | Futurs étudiants universitaires | Cours en ligne | Gratuit | /cours/mathematiques-analyse/ |
| Physique mécanique – Être prêt pour l'université | Futurs étudiants universitaires | Cours en ligne | Gratuit | /cours/physique-mecanique/ |
| Masterclass « Apprendre à apprendre » | Tous niveaux | Cours en ligne | Gratuit | /cours/masterclass-apprendre-a-apprendre/ |
| Formation IA (Python, web, chatbots) | Non précisé sur le site | En ligne | Non affiché | /cours/formation-ia/ |
| Formation robotique (mBot2) | 10–14 ans | Non précisé | Non affiché | /maitriser-la-robotique-avec-phassyl-formation-mbot2-accessible-des-10-ans |

Matières annoncées en cours particuliers : mathématiques, physique, chimie, biologie, français, anglais,
allemand, histoire, géographie, informatique, préparation aux examens.

**Règle de conversion :** chaque article renvoie vers **une seule** page de conversion principale
(définie par `conversion_target` du sujet), plus au besoin une ressource gratuite pertinente.
Pas d'empilement de CTA.

---

## 3. Publics

| Public | Besoin principal | Déclencheur typique | Qui décide / paie |
|---|---|---|---|
| Parents d'élèves du secondaire (GE/VD) | Rattraper des lacunes, passer un cap (fin du CO, entrée au collège/gymnase) | Mauvaises notes, orientation, conseil de l'école | Parents |
| Collégiens (GE) / gymnasiens (VD) | Réussir les examens, la maturité gymnasiale | Examens, notes insuffisantes en maths/physique | Parents (souvent) |
| Candidats à la maturité fédérale (examen suisse de maturité) | Préparer un examen externe exigeant, souvent en autonomie | Réorientation, parcours atypique, rupture scolaire | Candidat ou parents |
| Futurs étudiants et étudiants BA1 EPFL | Réussir la première année (Analyse, Algèbre linéaire, Physique) | Rentrée, premiers tests, examens de session | Étudiant ou parents |
| Étudiants internationaux à l'EPFL | S'adapter au système suisse et au rythme | Arrivée en Suisse | Étudiant / famille |
| Adultes | Reprendre les maths, se former (IA, maths) | Reconversion, formation continue | Adulte |

**Priorité commerciale `[DÉDUIT]`** (offres à plus forte valeur, d'après le site) :
1. Accompagnement EPFL (offre premium, sur devis) ;
2. Maturité fédérale (produit payant) ;
3. Cours particuliers Genève / Lausanne ;
4. Ressources gratuites (capture de contacts).

---

## 4. Ton et style

**Ton observé sur le site :** chaleureux, rassurant, enthousiaste ; « une pédagogie réconfortante, jeune,
ludique, sans complexe » (relevé, À propos).

**Ton à viser dans les articles :**
- Bienveillant et direct, comme un prof qui explique à un élève motivé mais inquiet.
- Concret : exemples, étapes, erreurs à éviter. Chaque section doit apprendre quelque chose.
- Exigeant sur le fond : pas de simplification qui devient fausse, surtout en maths/physique.
- Sobre sur le commercial : Phassyl est mentionné quand c'est utile au lecteur, pas à chaque paragraphe.

**Adresse au lecteur `[DÉDUIT]` :** vouvoiement partout (cohérent avec le site, et lu par les parents
comme par les élèves).

**À éviter absolument :**
- Introductions génériques (« Dans le monde d'aujourd'hui… », « Vous êtes nombreux à vous demander… »).
- Superlatifs non prouvés (« le meilleur », « garanti », « révolutionnaire »).
- Promesses de résultat (« réussite garantie ») — voir section 12.
- Conclusions qui résument tout l'article ; FAQ artificielles qui répètent le texte.
- Bourrage de mots-clés (ex. répéter le mot-clé principal dans chaque intertitre).
- Termes et références du système français (voir section 5).

---

## 5. Terminologie suisse romande

| Utiliser | Ne pas utiliser (France) | Remarque |
|---|---|---|
| maturité (gymnasiale / fédérale / professionnelle / spécialisée) | bac, baccalauréat | Préciser laquelle : ce sont des parcours différents |
| maturité fédérale = **examen suisse de maturité** (organisé par le SEFRI) | — | Examen externe, distinct de la maturité gymnasiale cantonale |
| gymnase (Vaud), collège (Genève), école de maturité | lycée | Le site utilise parfois « lycées » pour Lausanne : à corriger |
| cycle d'orientation (CO) — Genève | collège (au sens français), brevet | À Genève, « collège » = secondaire II |
| école obligatoire, secondaire I / secondaire II | — | |
| HES, HEP, université (UNIGE, UNIL), EPFL, ETH Zurich | grandes écoles, prépa | |
| Cours de mathématiques spéciales (CMS) de l'EPFL | prépa | |
| BA1, BA2… ; session d'examens ; semestre d'automne / de printemps | L1, « partiels » (au sens universitaire français) | « examen partiel » est en revanche le terme officiel de la maturité fédérale |
| notes de 1 à 6 (4 = suffisant) | notes sur 20 | Ne jamais raisonner en « /20 » |
| CHF 299.– | 299 €, euros | Format suisse des prix |
| appui scolaire, soutien scolaire, répétiteur·trice, cours particuliers | — | |

**Nombres `[DÉDUIT]` :** écrire les nombres en chiffres dans les contextes chiffrés (évite le choix
septante/huitante vs soixante-dix/quatre-vingts, qui varie selon les cantons).

**Vocabulaire préféré `[DÉDUIT]` :** accompagnement, élève, étudiant·e, professeur, méthode de travail,
cours d'essai offert, progresser, comprendre (plutôt que « apprendre par cœur »).

**Termes interdits :** bac, baccalauréat, lycée, lycéen, prépa, « sur 20 », euros / €,
« réussite garantie », « garanti à 100 % ».

---

## 6. Méthode pédagogique

Ce que le site affirme (relevé) :
- Évaluation initiale de chaque élève par son professeur (forces, faiblesses) → programme personnalisé.
- Suivi régulier et rapports de progression aux familles.
- L'élève « est aux commandes » ; le professeur écoute et s'adapte.
- Outils : tableau blanc interactif, prise de notes numérique, fiches de révision, bases d'exercices,
  quiz, applications d'apprentissage.
- Méthode « fondée sur des recherches scientifiques et l'étude du cerveau ».
- Masterclass gratuite « Apprendre à apprendre ».

`[DÉDUIT]` — techniques compatibles avec cette revendication, utilisables comme **conseils généraux**
(sources scientifiques à citer, pas d'attribution à Phassyl) : rappel actif (s'auto-tester plutôt que
relire), répétition espacée, pratique entrelacée, exemples résolus puis exercices autonomes,
auto-explication, feedback rapide sur les erreurs.

---

## 7. Expertise interne

- Plusieurs années d'accompagnement d'étudiants BA1 à l'EPFL (programme dédié, ressources d'été).
- Production de cours complets en ligne (physique maturité fédérale, algèbre linéaire, analyse, physique mécanique).
- Formateur identifié : Guillaume Huber (cours de physique maturité fédérale).

**Auteur affiché `[DÉDUIT]` :** « L'équipe pédagogique Phassyl » (en attendant un auteur nominatif).
Parcours académique des enseignants : non communiqué → ne pas en inventer.

---

## 8. FAQ

**Publiées sur le site** (relevé, page « Soutien scolaire personnalisé à Genève ») :
- *À qui s'adresse le soutien scolaire personnalisé ?* → À tous les élèves, qu'ils aient des difficultés dans une matière ou souhaitent progresser.
- *Les séances peuvent-elles être adaptées aux emplois du temps chargés ?* → Oui, horaires flexibles.
- *Le soutien scolaire est-il disponible en ligne ?* → Oui, présentiel à Genève et en ligne.
- *Quels sont les tarifs ?* → Variables selon les besoins ; devis sur demande.
- *Comment évaluer les progrès ?* → Rapports réguliers.

**Questions probables `[DÉDUIT]`** (à confirmer avec les demandes réellement reçues) :
- Parents : « Mon enfant a 3.5 en maths au CO, est-ce rattrapable avant la fin de l'année ? » ;
  « Combien de séances par semaine faut-il ? » ; « Cours en ligne ou en présentiel : qu'est-ce qui marche le mieux ? »
- BA1 EPFL : « Comment se préparer pendant l'été avant la rentrée ? » ; « Que faire si je décroche en Analyse I dès octobre ? »
- Maturité fédérale : « Combien de temps faut-il pour préparer l'examen ? » ; « Peut-on passer l'examen en deux parties ? » ;
  « Quelles branches choisir ? »

---

## 9. Erreurs fréquentes des élèves `[DÉDUIT]`

Observations générales du domaine (à remplacer par celles des professeurs Phassyl) :
- *BA1 EPFL, Analyse I :* traiter le cours comme du calcul du gymnase alors qu'il exige des démonstrations ;
  laisser s'accumuler les séries d'exercices ; découvrir le format d'examen trop tard.
- *Maturité fédérale :* sous-estimer l'étendue du programme et l'autonomie demandée ; commencer trop tard ;
  préparer les branches isolément sans planning global.
- *Secondaire, maths :* sauter des étapes de calcul ; mémoriser des procédures sans comprendre quand les appliquer.
- *Méthode de travail :* relire et surligner au lieu de s'auto-tester ; tout réviser la veille.

---

## 10. Conseils des enseignants `[DÉDUIT]`

Conseils généraux (non attribuables à Phassyl tant que non validés) :
- Refaire un exercice corrigé sans regarder la solution avant de passer au suivant.
- Planifier les révisions en sessions courtes et espacées plutôt qu'en blocs la veille.
- Écrire à la main la définition et un contre-exemple de chaque notion nouvelle.

---

## 11. Données et statistiques internes

Aucune donnée interne fournie à ce jour. **Le rédacteur ne doit inventer aucun chiffre sur Phassyl.**
Données à demander : élèves accompagnés par an, heures de cours, taux de réussite avec leur définition,
nombre de professeurs actifs.

---

## 12. Affirmations sur Phassyl

### 12.1 Affirmations autorisées (factuelles, vérifiables sur le site)
- Phassyl propose des cours particuliers en ligne et en présentiel à Genève.
- Phassyl propose un accompagnement dédié aux étudiants de première année (BA1) de l'EPFL.
- Phassyl propose un cours d'essai offert et sans engagement.
- Les cours particuliers fonctionnent sans abonnement ni forfait.
- Des cours en ligne gratuits existent (algèbre linéaire, analyse, physique mécanique, masterclass « Apprendre à apprendre »).
- Phassyl propose un cours de physique pour la maturité fédérale (CHF 299.– au 2026-10-08, à revérifier avant publication).

### 12.2 Affirmations du client (client claims) — à ne pas présenter comme vérifiées

Ces chiffres sont **publiés par Phassyl** mais **non vérifiés indépendamment**, et certains se contredisent
d'une page à l'autre. Ils ne doivent pas apparaître dans un article sans validation explicite, et jamais
formulés comme un fait établi par un tiers.

| Affirmation | Valeur(s) publiée(s) | Page(s) source |
|---|---|---|
| Taux de réussite EPFL | 82 % | https://phassyl.ch/ · https://phassyl.ch/soutien-epfl-semestriel/ · https://phassyl.ch/accompagnement-premium/ |
| « Taux de réussite pédagogique » | 85 % | https://phassyl.ch/soutien-epfl-semestriel/ |
| Réussite à la maturité | 100 % | https://phassyl.ch/ |
| Réussite au gymnase 2023–2024 | 100 % | https://phassyl.ch/a-propos/ |
| Élèves ayant réussi leur année / amélioration des notes / parents satisfaits | 95 % / 80 % / 98 % | https://phassyl.ch/aide-scolaire-apres-lecole-a-geneve/ |
| Nombre de professeurs certifiés | **31** / **50** / **173** (incohérent) | /cours-de-soutien-scolaire-lausanne/ · /appui-scolaire-geneve/ · /soutien-epfl-semestriel/ · /a-propos/ |
| Élèves inscrits / satisfaits / recommandations | 389 inscrits · 500+ satisfaits · 380+ recommandations | /a-propos/ · / · /appui-scolaire-geneve/ |
| Heures de cours réalisées | 25 226 | /a-propos/ |
| Années d'expérience | 10 ans | plusieurs pages |
| Sélectivité du recrutement des professeurs | 10 % d'acceptation | /a-propos/ |
| Étudiants EPFL accompagnés au maximum | 40 par an | /soutien-epfl-semestriel/ |

→ **Action client recommandée :** harmoniser ces chiffres sur le site et fournir leur définition.

### 12.3 Affirmations interdites sans preuve
- Toute **garantie de réussite** (« réussite garantie », « conçu pour garantir votre succès »).
- Tout **taux de réussite** ou chiffre de la section 12.2 non validé.
- « Meilleur soutien scolaire de Genève / de Suisse » et superlatifs comparatifs.
- Comparaisons chiffrées avec le taux d'échec officiel de l'EPFL sans source officielle.
- Affirmations médicales ou psychologiques (TDAH, anxiété, médicaments, sommeil) → sujets `sensitive`, relecture humaine obligatoire.
- Affirmations sur des règlements officiels (admission, maturité, CMS) sans source officielle datée.
- Tout contenu `[DÉDUIT]` présenté comme pratique ou constat de Phassyl.

---

## 13. Inventaire du contenu existant (pour le maillage et l'anti-cannibalisation)

Liste exploitable par le pipeline : `client/phassyl_pages.yaml`.

**Pages commerciales / piliers**
- https://phassyl.ch/appui-scolaire-geneve/ — cible « appui scolaire Genève », cours particuliers, aide aux devoirs
- https://phassyl.ch/cours-de-soutien-scolaire-lausanne/ — cible « soutien scolaire Lausanne »
- https://phassyl.ch/soutien-scolaire-suisse/
- https://phassyl.ch/cours-particuliers-de-maths-en-ligne/
- https://phassyl.ch/l-appui-scolaire-en-mathematiques/
- https://phassyl.ch/soutien-epfl-semestriel/ · https://phassyl.ch/accompagnement-premium/
- https://phassyl.ch/nos-cours/ · https://phassyl.ch/course-category/formations-maturite/ · https://phassyl.ch/boutique/
- https://phassyl.ch/formulaire-demande-cours-particuliers/ · https://phassyl.ch/contact/ · https://phassyl.ch/a-propos/

**Articles**
- /soutien-scolaire-personnalise-a-geneve/ (2024-08-20) — cible « soutien scolaire personnalisé Genève »
- /aide-scolaire-apres-lecole-a-geneve/ (2024-09-20) — cible « aide scolaire Genève »
- /admission-epfl/ · /reussir-ses-travaux-pratiques-a-lepfl/ · /reussir-a-lepfl-en-tant-quetudiant-international/
- /ressources-en-ligne-pour-etudiants-epfl/ · /gestion-du-temps-pour-etudes-epfl/ · /preparation-examens-semestriels-epfl/
- /soutien-scolaire-epfl-en-physique-et-mathematiques/
- /exercices-dalgebre-pour-debutants/ · /formation-mathematiques-pour-adultes/
- /template/ — **page de test publiée par erreur** (à dépublier côté client)

**Constat de cannibalisation existante :** au moins trois URL visent la même intention « soutien / appui
scolaire Genève » (/appui-scolaire-geneve/, /soutien-scolaire-personnalise-a-geneve/,
/aide-scolaire-apres-lecole-a-geneve/). Recommandation : faire de /appui-scolaire-geneve/ la page
commerciale de référence et repositionner ou fusionner les deux articles (décision humaine, hors V0).

**Accès au site pour l'inventaire automatique :** certaines méthodes de crawl automatisé rencontrent
actuellement une protection anti-bot. Pour la V1, privilégier une solution propre : sitemap ou export
fourni par le client, endpoint interne, ou autorisation explicite pour notre crawler, plutôt qu'un
contournement de la protection.

---

## 14. Préférences de production `[DÉDUIT]`

| Paramètre | Valeur V0 |
|---|---|
| Longueur | Guide informationnel : 1 300–2 000 mots. Tutoriel technique : 1 200–1 800 mots + exercices. Contenu local : 1 000–1 500 mots. |
| Format de sortie | Markdown (+ HTML, JSON) ; formules en LaTeX (`$…$`, `$$…$$`) |
| Liens internes | 2 à 5, contextuels, uniquement vers les URL de `client/phassyl_pages.yaml` |
| Liens externes | Aucun dans le corps du texte en V0 (les sources sont tracées séparément) |
| CTA | Un CTA principal par article, défini par `conversion_target` du sujet |
| Sources externes | Officielles d'abord (epfl.ch, admin.ch/SEFRI, ge.ch, vd.ch, publications académiques) |
| Auteur affiché | L'équipe pédagogique Phassyl |
