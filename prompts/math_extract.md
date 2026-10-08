---
name: math_extract
version: 1
task: math_extract
---
Tu extrais d'un article de mathématiques chaque exercice ou exemple qui calcule des valeurs propres
et/ou des vecteurs propres d'une matrice, exactement comme l'article les présente (même s'ils sont
faux : ne corrige rien).

Format :
- `matrix` : lignes de la matrice, chaque coefficient en expression simple (`3`, `-1/2`, `sqrt(2)`).
- `eigenvalues` : toutes les valeurs propres annoncées par l'article, répétées selon la multiplicité
  annoncée.
- `eigenpairs` : chaque vecteur propre annoncé avec sa valeur propre ; pour une famille comme
  « t·(1, 2) », donne le représentant (1, 2).
- `label` : le titre ou le numéro de l'exercice.
=== USER ===
<article>
{{ article }}
</article>