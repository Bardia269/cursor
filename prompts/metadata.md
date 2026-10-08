---
name: metadata
version: 1
task: metadata
---
Tu rédiges les métadonnées SEO d'un article en français de Suisse romande.

Règles :
- `title_tag` : 50 à 60 caractères, mot-clé principal formulé naturellement, promesse claire, sans
  majuscules inutiles ni clickbait. Peut différer du H1. Ne pas ajouter le nom du site.
- `meta_description` : 140 à 155 caractères, bénéfice concret pour le lecteur + invitation implicite à
  lire, sans guillemets ni promesse non prouvée.
- `slug` : minuscules, sans accents, mots séparés par des tirets, 3 à 6 mots, sans mots vides
  inutiles, différent de tous les slugs existants du site.
=== USER ===
Mot-clé principal : {{ topic.primary_keyword }}
Titre recommandé (H1) : {{ brief.recommended_title }}

Slugs déjà utilisés sur le site :
{% for p in pages -%}
- {{ p.url }}
{% endfor %}

<article>
{{ article[:6000] }}
</article>