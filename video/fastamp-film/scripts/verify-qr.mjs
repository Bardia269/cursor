// Décode le QR final sur une image rendue (contrôle exigé par le brief).
import { readFileSync } from "node:fs";
import { PNG } from "pngjs";
import jsQR from "jsqr";
const png = PNG.sync.read(readFileSync(process.argv[2]));
const res = jsQR(new Uint8ClampedArray(png.data), png.width, png.height);
console.log(res ? `QR décodé : ${res.data}` : "QR NON décodé");
process.exit(res ? 0 : 1);
