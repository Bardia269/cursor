"""Sous-titres FR (voix off du brief, phrases courtes, 2 lignes max) calés sur les scènes du film."""
FPS = 30
T = 24
DUR = [300, 240, 240, 270, 255, 255, 255, 255, 210, 300]
VO = [
    ["Une carte dans leur téléphone.\nUne raison de revenir.", "Voici Fastamp, la fidélité pensée\npour les commerces indépendants."],
    ["Votre client scanne le QR du commerce", "et ajoute sa carte à Apple Wallet\nou Google Wallet."],
    ["Votre logo, vos couleurs, votre bannière :", "une carte à votre image, sans\napplication Fastamp à télécharger."],
    ["À chaque passage, votre équipe\nscanne la carte dans Fastamp,", "puis confirme les points ou les tampons\net les récompenses."],
    ["Gardez le lien avec des annonces envoyées\naux clients qui les ont acceptées,", "directement via leur carte Wallet."],
    ["Avec Premium, Signals transforme vos\ndonnées en suggestions concrètes.", "L'assistance IA aide à préparer\ndes messages que vous validez."],
    ["Autopilot analyse les visites enregistrées\net aide à relancer les clients,", "selon leur rythme, vos réglages\net des limites de contact."],
    ["Avec Impact, observez les visites et les\nrécompenses enregistrées après vos campagnes.", "Un retour observé n'est pas\nune vente supplémentaire prouvée."],
    ["Essentielle pour démarrer simplement.", "Premium pour cibler, analyser\net automatiser les relances."],
    ["Et si votre fidélité suivait votre métier ?", "Parlons de vos besoins et découvrez\nFastamp en démonstration."],
]


def ts(f):
    s = f / FPS
    h, m = int(s // 3600), int(s % 3600 // 60)
    return f"{h:02d}:{m:02d}:{int(s % 60):02d},{int(round((s - int(s)) * 1000)):03d}"


start = 0
cues = []
for i, d in enumerate(DUR):
    a = start + (10 if i else 6)
    b = start + d - (T if i < len(DUR) - 1 else 40)
    half = a + (b - a) // 2
    cues.append((a, half - 4, VO[i][0]))
    cues.append((half, b, VO[i][1]))
    start += d - T
with open("out/fastamp-sous-titres.srt", "w", encoding="utf-8") as f:
    for n, (a, b, t) in enumerate(cues, 1):
        f.write(f"{n}\n{ts(a)} --> {ts(b)}\n{t}\n\n")
print("total", start + T, "frames")
