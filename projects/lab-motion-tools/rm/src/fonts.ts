import { continueRender, delayRender, staticFile } from "remotion";
// fonts: load before first frame (delayRender) so no frame ever captures a fallback face
const fontHandle = typeof window !== "undefined" ? delayRender("fonts") : 0;
if (typeof window !== "undefined") {
  // bytes, not URLs: this box's Chrome fails URL font loads (NetworkError) but FontFace(ArrayBuffer) always works
  const face = (fam: string, file: string, desc: FontFaceDescriptors = {}) =>
    fetch(staticFile(file)).then(r => r.arrayBuffer()).then(buf => new FontFace(fam, buf, desc).load());
  Promise.all([face("MuseDisplay", "ArchivoBlack-Regular.ttf"), face("MuseSerif", "InstrumentSerif-Italic.ttf", { style: "italic" }), face("MuseMono", "IBMPlexMono-Medium.ttf")])
    .then(fs => { fs.forEach(f => document.fonts.add(f)); continueRender(fontHandle); });
}

