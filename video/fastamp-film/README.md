# Fastamp — film motion design

Le film de présentation de Fastamp est codé avec [Remotion](https://www.remotion.dev) (React → MP4). Il fait 78,8 s et existe en deux formats : 1920×1080 (16:9) et 1080×1920 (9:16). Le format vertical est recomposé scène par scène, pas recadré.

## Concept : un espace 3D immersif, éclairé par l'anneau du logo

- **Moteur 3D** (`src/components/Space.tsx`) : une vraie caméra animée par images clés (dolly, orbite, travelling), des objets placés en x/y/z, une profondeur de champ calculée selon la distance au plan net, et un sol brillant qui reflète la scène.
- **Lumière** : l'anneau lavande du logo devient la source lumineuse du film (`RingLight`), avec un halo doux et sans particules.
- **Ouverture** : les sept anneaux du symbole arrivent de la profondeur et se posent sur la géométrie exacte du logo officiel. La caméra plonge ensuite dans l'anneau lavande.
- **Transitions** : la caméra traverse un anneau de lumière qui fonce vers elle (`flyThrough`).
- **Mises en scène** :
  - comptoir en orbite, avec une poussée sur l'écran pendant le scan ;
  - carte en vue éclatée (logo, couleur, bannière, tampons sur des couches séparées en profondeur) ;
  - faisceau de lecture entre la tablette et le téléphone ;
  - annonce qui traverse l'espace jusqu'à la carte ;
  - panneaux Signals empilés et balayés par une barre de lumière ;
  - travelling le long d'une piste de visites posée au sol (Autopilot) ;
  - panneaux Impact en V ;
  - offres qui se retournent au-dessus du sol.
- **Lisibilité** : les titres sont sur un calque à parallaxe réduite (`Hud`), avec un voile sombre derrière eux. Ils suivent la caméra sans jamais sortir du cadre. Le QR final reste à plat et la caméra est immobile pendant les 5 dernières secondes.
- **Son** : la musique (120 BPM, Fmaj9 – Am7 – Dm9 – B♭maj9) et les bruitages (tampon, clic, souffle, notification) sont synthétisés par `scripts/make-audio.py`. Ce sont des créations originales, donc sans droits à acheter.

Écart assumé avec la DA d'origine (« 2,5D modérée », alternance de fonds clairs et sombres) : à la demande du client, le film passe en 3D immersive sur fond nuit. La palette, le logo, la typographie et toutes les règles d'exactitude produit restent respectés.

## Exactitude produit (checklist de la DA)

- Le logo n'est jamais redessiné. Les anneaux animés reprennent la géométrie exacte du SVG officiel, puis le PNG officiel est révélé par balayage. À la fin, seul le PNG reste à l'écran.
- Les QR sont calculés (`scripts/make-qr.mjs`). Les QR de démonstration encodent un texte qui indique qu'ils sont fictifs. Le QR final encode `https://fastamp.vercel.app/demo-request`.
- Pas de caisse connectée : l'équipe scanne la carte dans Fastamp puis confirme. Le solde passe de 6/8 à 7/8 seulement après cette confirmation.
- Signals propose un brouillon et c'est la personne qui le valide. Autopilot fait une analyse quotidienne avec consentement et limites. Impact montre ce qui est observé, sans chiffres ni causalité.
- Les modules Premium apparaissent avec leur badge, dans le compte manager.
- Le film n'affiche ni prix, ni ROI, ni taux d'ouverture.
- Les mentions apparaissent à l'écran : « Illustration — rendu variable selon le Wallet », « Données de démonstration », « Affichage et réception selon le Wallet… ».

## Commandes

```bash
npm i
npm run dev                      # Remotion Studio (aperçu interactif)
node scripts/make-qr.mjs         # régénère les QR
python3 scripts/make-audio.py 80 # régénère musique + bruitages
python3 scripts/make-srt.py      # sous-titres FR calés sur les scènes
npx remotion render Fastamp-16x9 out/fastamp-16x9.mp4
npx remotion render Fastamp-9x16 out/fastamp-9x16.mp4
```

Chaque scène est aussi enregistrée comme composition autonome (dossiers `Scenes-16x9` et `Scenes-9x16` dans le Studio).

## Structure

- `src/Film.tsx` : enchaînement des scènes, origines des iris, musique
- `src/scenes/S01…S10` : une scène par fichier, qui lit `useLayout()` pour gérer les deux formats
- `src/components` : carte Wallet, appareils, logo animé, titres, mentions, sons
- `src/components/Space.tsx` : moteur 3D (caméra, objets, profondeur de champ, sol réfléchissant, anneau de lumière)
- `src/transitions/flyThrough.tsx` : la traversée d'anneau entre les scènes

## Voix off

Le film est conçu pour fonctionner sans voix : le texte à l'écran porte le message. Le script de voix off du brief est fourni en sous-titres dans `out/fastamp-sous-titres.srt`. Si une voix est enregistrée, il suffit de placer un fichier par scène et d'ajouter un `<Audio>` dans `Film.tsx`, en baissant la musique d'environ 40 %.
