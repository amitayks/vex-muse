# LEARNINGS — svg-transform

- 2026-09-26 Chrome on this box fails URL font loads (NetworkError, even data: URIs) and has no system fonts: register every face from bytes (FontFace(ArrayBuffer)) or text renders blank.
- 2026-09-26 Hard morph pairs (concave glyph → heart): naive index lerp and @remotion/paths interpolatePath tear; flubber and GSAP MorphSVG stay clean — test a 5-step strip before using any new pair.
- 2026-09-26 A 3D/4D object's key beat can hide its structure (the octahedron slice showed 2 faces instead of its 4-face checker): choose the camera angle by numeric search over the landmark frame, not by eye.
- 2026-09-26 Turns that end on 90° multiples map a tesseract onto itself — they give free, exact loop and cut points; land them on a beat and hold.
