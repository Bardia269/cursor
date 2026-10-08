<sources>
{% for s in sources -%}
[{{ s.id }}] {{ s.title or s.url }} — {{ s.domain }}{% if s.is_preferred_domain %} (source officielle / préférée){% endif %}
URL : {{ s.url }}
Résumé : {{ s.summary }}
{% endfor -%}
{% if not sources %}(aucune source exploitable){% endif %}
</sources>

<affirmations_verifiees>
Chaque affirmation a été extraite d'une source et sa citation a été retrouvée mot pour mot dans le texte source.
{% for c in claims -%}
{{ c.id }} [{{ c.source_id }}] ({{ c.claim_type }}) {{ c.statement }}
   citation : « {{ c.quote }} »
{% endfor -%}
{% if not claims %}(aucune affirmation vérifiée){% endif %}
</affirmations_verifiees>