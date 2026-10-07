# Components: what to reach for, what to avoid

Full props: `scripts/catalog.py show <Name>`. Flags: `scripts/catalog.py list`.

## Preset format
`{components: [{type, id, props, children}]}`, evaluated top to bottom and blended on the GPU.
- A `CHILD` component is a filter on its `children` (Glass refracts them, Halftone screens them).
- Universal props: `opacity`, `blendMode` (normal, multiply, screen, overlay, add, difference, …),
  `maskSource` (+ `maskType` alpha/luminance/inverted), `transform` {offsetX, offsetY, rotation,
  scale, anchorX, anchorY, edges}, `boundingBox`. `visible` exists but recompiles: animate `opacity`.
- `position` props are `{x, y}` in 0–1 UV; colors are hex strings; `speed` props drive internal time.

## Shape materials (take `shape`)
BrushedMetal, CarbonFiber, Chrome, Frost, Goo, Heatmap, Hologram, Holographic, Irradiance, LightEdge,
LiquidMetal, Nebula, Neon, Obsidian, Plastic, ThinFilm, Voxels, Water; Glass, Crystal and Emboss
(CHILD: they refract or emboss their children — give them a busy child). Avoid Particles and
SmokeFill (SIM). Look sheet of all of them on one torus: `material-grid.jpg` (beside this file).
- Read best on a dark flat field: Neon, LightEdge, Hologram, Heatmap, ThinFilm (raise `intensity`).
- Read on any field: Chrome, LiquidMetal, Plastic, CarbonFiber, Obsidian, Voxels, Water, Frost.
- Weak: Irradiance (35 s first compile, dark), Emboss (needs texture under it).

## Shapes (`shape: {type, ...sub-props}`)
sphere3D, cube3D, torus3D, octahedron3D, cylinder3D, capsule3D, cone3D, pyramid3D, prism3D,
ellipsoid3D, diamond3D, link3D, gem3D, helix3D, metaballs3D, dodecahedron3D, hemisphere3D, ribbon3D,
blob3D, gyroscope3D. Sub-props: size (`radius`, `tube`, `sizeX/Y/Z`, `height`, …) and `rotX`,
`rotY`, `rotZ` in degrees. `svgExtrude3D` takes an SVG converted to an SDF `.bin`; the free converter
is the vendor's public endpoint, so the SVG leaves the box: ask before sending a client mark.
- Pose: a torus's axis is +Y (rotX 0 = edge-on, 90 = face-on), and every Euler angle tilts that axis.
  A free spin on any axis shows the edge (a pill). Bound the angles near the readable pose.
- Shape sub-props, `scale`, `center` animate per frame without a recompile (~130 ms per 480×270 frame).

## Filters worth knowing (CHILD)
Halftone, Dither (2-colour, `pixelSize`), CRTScreen (`pixelSize` 30–60 reads at video size),
ChromaticAberration (kick pulse on `strength`), Kaleidoscope (`segments` per beat), Repeater (grid or
radial copies, `hueShift`), Glow, FilmGrain, VHS, ZoomBlur, Bulge, Posterize, Duotone, Tritone,
transitions (IrisWipe, PagePeel, NoiseDissolve, … driven by `progress` 0–1).
Generators: FlowingGradient, MeshGradient, Aurora, Prism (light beam), Godrays, Plasma, Voronoi,
StudioBackground, SolidColor.

## Never in a render
- SIM (state carries frame to frame): Particles, SmokeFill, ReactionDiffusion, TimeTrail, DataMosh,
  Smoke, SmokeFlow, InkFlow, FlowField, Boids, ParticleFlow, Liquify, Shatter, PixelThrow, PixelSort,
  MagneticFilings, ChromaFlow, GridDistortion, Fog. Only a strictly sequential single-process render
  could use them, and Modal chunks are not that.
- NET: Text, Ascii (load Google Fonts over the network). Type stays in the DOM.
- INPUT: cursor effects, webcam, video textures (untested). `ImageTexture` works with a data: URL; the
  driver waits for its decode before the first frame.
- Auto-animate prop drivers on shape sub-props (their phase reads the wall clock).

## Speed (SwiftShader on CPU)
480×270: 0.5–3 s per frame. 1080p on a 2-CPU box: 4–19 s per frame. Modal 8-CPU containers:
0.34–3.1 s per 1080p frame (33.6 s at 60 fps with 23 presets: 154 s wall on 48 chunks).
