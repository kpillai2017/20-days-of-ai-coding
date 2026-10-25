# Battlezone (1980): inspiration and boundaries

Atari released **Battlezone** in 1980. Its first-person tank combat presented a three-dimensional battlefield as luminous wireframe lines on a vector display. Arcade cabinet designs included a distinctive viewing arrangement; the separate left/right controls evoked tank tracks. Radar and a sparse landscape helped players locate threats outside the forward view.

The display was not a modern textured 3D engine. A vector monitor traced lines rather than painting the conventional raster grid used by a desktop screen. Perspective, changing scale and turning scenery created a convincing sense of navigating a space with remarkably little visual information.

Tanks, faster opponents, saucers and a missile threat contributed to the original's combat vocabulary. This project adopts only a subset. It should not be used as a historical reference for precise score tables, enemy schedules, cabinet variants or ROM timing.

## What this tribute tries to preserve

- First-person movement with the hull and gun aligned.
- Bright green line-art tanks, geometric cover and a distant mountain/volcano landmark.
- A cockpit-style reticle, radar, threat cue and simple numeric score/lives.
- Independent-track keyboard controls alongside convenient arrow keys.
- Deliberate shooting: one active player projectile at a time.

## What is deliberately different

All source, meshes, scenery and sound samples are newly created. The program does not load Atari ROMs or reproduce original machine instructions. Pygame draws antialiased lines onto a raster Surface, not a physical vector CRT. Optional tones/noise evoke a period machine without recreating its audio circuitry.

The 200×200-unit bounded arena, fixed obstacle layout, probabilistic reinforcement spawning, enemy movement/aiming, collision circles, scoring values, three-life rule, respawn protection and difficulty curve are this project's choices. There is no missile enemy, original attract sequence, high-score persistence, exact bonus-life system, cabinet periscope effect or guarantee of original play balance. Wireframes remain transparent rather than performing original-style selective edge visibility.

“Close to the original” here means a recognisable **visual and control tribute**, not arcade accuracy. For the original's actual rules, consult historical manuals and lawful access to the original game.

## Rights and sources

**Battlezone** and **Atari** are used to identify the historical game; rights in those names and original materials remain with their respective owners. No affiliation or endorsement is implied. The repository MIT licence applies to this project's own implementation, not to third-party brands, ROMs or artwork. A game idea or visual style is not permission to distribute proprietary assets.

Further learning:

- [Internet Archive search: Atari Battlezone manual](https://archive.org/search?query=Atari+Battlezone+manual) — historical manual scans; availability and rights vary. We do not bundle scans or transcribe their prose.
- [The Strong search: Battlezone](https://www.museumofplay.org/?s=Battlezone) — museum/history starting point.
- [Pygame documentation](https://www.pygame.org/docs/) — the modern drawing/input/audio toolkit used here.

These links are background references, not claims that this program has been validated against an original cabinet or every archived source. No third-party historical image, text passage, model, translation or recording is copied into the game.
