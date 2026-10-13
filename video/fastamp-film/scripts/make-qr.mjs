// Génère les matrices QR (calculées, jamais dessinées à la main) utilisées dans le film.
import QRCode from "qrcode";
import { writeFileSync } from "node:fs";

const make = (text, ecl) => {
  const qr = QRCode.create(text, { errorCorrectionLevel: ecl });
  const size = qr.modules.size;
  const rows = [];
  for (let y = 0; y < size; y++) {
    let row = "";
    for (let x = 0; x < size; x++) row += qr.modules.get(x, y) ? "1" : "0";
    rows.push(row);
  }
  return { text, size, rows };
};

const data = {
  // CTA final : URL validée du brief.
  cta: make("https://fastamp.vercel.app/demo-request", "M"),
  // QR décoratifs : ne mènent à aucune inscription réelle.
  demoJoin: make("Fastamp - QR de démonstration (Maison Centrale, commerce fictif)", "L"),
  demoCard: make("Fastamp - carte de démonstration (Camille - Démo)", "L"),
};
writeFileSync("src/data/qr.json", JSON.stringify(data));
console.log(Object.fromEntries(Object.entries(data).map(([k, v]) => [k, v.size])));
