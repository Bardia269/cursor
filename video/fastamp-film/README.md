# Fastamp — film motion design

Le film de présentation de Fastamp est codé avec [Remotion](https://www.remotion.dev) (React → MP4). Il fait 78,8 s et existe en deux formats : 1920×1080 (16:9) et 1080×1920 (9:16). Le format vertical est recomposé scène par scène, pas recadré.

## Concept : « Le film se tamponne »

- **Ouverture** : les six anneaux du symbole se posent un à un en très gros plan, avec un son de tampon. La caméra recule ensuite et révèle le logo officiel, puis plonge dans l'anneau lavande.
- **Transitions** : chaque scène s'ouvre par un iris en forme d'anneau de tampon, avec un double contour aux proportions du symbole. L'iris part de l'élément que l'œil regarde déjà.
- **Alternance de fonds** : violet nuit et blanc cassé, comme le site, avec la trame d'anneaux en rotation diagonale. Le motif s'efface derrière les textes.
- **Fermeture** : le logo se tamponne de nouveau et la composition finale reste stable pendant plus de 5 s, avec un QR réel qui mène vers `/demo-request`.
- **Son** : la musique (120 BPM, Fmaj9 – Am7 – Dm9 – B♭maj9) et les bruitages (tampon, clic, iris, notification) sont synthétisés par `scripts/make-audio.py`. Ce sont des créations originales, donc sans droits à acheter.

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
- `src/transitions/stampIris.tsx` : la transition signature

## Voix off

Le film est conçu pour fonctionner sans voix : le texte à l'écran porte le message. Le script de voix off du brief est fourni en sous-titres dans `out/fastamp-sous-titres.srt`. Si une voix est enregistrée, il suffit de placer un fichier par scène et d'ajouter un `<Audio>` dans `Film.tsx`, en baissant la musique d'environ 40 %.
