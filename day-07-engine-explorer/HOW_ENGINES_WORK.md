# Two strokes or four: what changes?

These are simplified **spark-ignition** engines. A spark ignites an air–fuel charge; hot expanding gases exert force on the piston. The connecting rod turns that reciprocating motion into crank rotation. This app prescribes a constant crank speed so you can study the sequence; the graphics do not calculate the force required to sustain it.

## 1. Shared moving parts

```text
        spark plug
             ↓
       ┌───────────┐  cylinder head
       │ gas space │
       │ ┌───────┐ │
       │ │piston │ │  slides, never follows the crank's circular path
       │ └───●───┘ │  piston pin
       └─────│─────┘
             ╲        connecting rod (fixed length)
              ●       rotating crank pin
             ╱
            ●         crankshaft centre
```

### Why the rod does not pass through the crankshaft

A crankshaft is not a straight bar through the connecting rod. Two main journals lie on the rotation axis, one on each side of the rod. Offset webs connect them to a crank pin displaced from that axis. The connecting rod's big-end bearing surrounds that pin and moves between the webs. At bottom dead centre the rod crosses the shaft's axis in a side-view projection, but the main journals occupy different front/back positions—there is no solid main shaft there for it to hit. The renderer now models that separation explicitly.

**Top dead centre (TDC)** is the highest piston position. **Bottom dead centre (BDC)** is the lowest. One stroke means one journey between them. One full crank revolution moves the piston down and back up: two strokes.

Positive crank angle starts at TDC. In the first 180° the piston moves down; in the next 180° it moves up. A four-stroke cycle needs two such revolutions; piston geometry alone cannot identify which of its four processes is happening.

## 2. Four-stroke: 720° per complete cycle

Our ideal timing has no valve overlap or advance. Real engines usually open/close valves away from dead centres.

| Angle | Piston | Intake valve | Exhaust valve | Process |
| --- | --- | --- | --- | --- |
| 0–180° | Down | Open | Closed | Draw fresh mixture in |
| 180–360° | Up | Closed | Closed | Compress trapped mixture |
| 360–540° | Down | Closed | Closed | Expanding combustion gases deliver power |
| 540–720° | Up | Closed | Open | Displace burnt gas through exhaust |

```text
INTAKE                 COMPRESSION
fresh → valve          both valves closed
       ↓                       ↑ piston
    piston ↓               charge squeezed

POWER                  EXHAUST
spark / hot gas         exhaust valve → burnt gas
       ↓                       ↑ piston
    piston ↓
```

Only one of the four piston strokes is the nominal power stroke. Inertia/flywheel and other cylinders help real machinery continue through the other strokes. The app's crank moves uniformly without calculating those dynamics.

The spark cue spans 350–370° to make ignition around TDC visible. It is not a claim that a physical spark arc lasts for those twenty degrees. Combustion takes finite time and can start before TDC; the gold fill is a phase cue, not a flame-front or pressure calculation.

### Why 0° and 360° look mechanically alike

The piston is at TDC at both angles, but at 0° it is about to intake and at 360° it is about to expand burnt gas. Head-valve scheduling distinguishes the processes. This display moves schematic poppet valves, but does not include their real camshaft/drive.

## 3. Two-stroke: cylinder and crankcase work together

This example is **crankcase-scavenged and piston-ported**, with a pressure-operated reed inlet into the crankcase. Many other layouts exist. In particular, large two-stroke diesels can use external scavenging air and exhaust valves; don't generalize this drawing to them.

The piston separates two changing volumes:

```text
           CYLINDER above piston
        combustion / compression
           ┌────────────┐
exhaust ←  │            │  ← transfer from crankcase
           │  PISTON    │
           └────────────┘
              rod
fresh → reed → CRANKCASE below piston
                │
                └──── transfer duct ────↑ cylinder
```

Fresh mixture does **not** simply enter the cylinder through a head intake valve. It first enters the crankcase, then transfers up a duct into the cylinder when ports are exposed and pressure permits.

### Follow one revolution

1. **Near TDC / ignition:** the cylinder charge is compressed. A spark cue appears shortly before TDC.
2. **Downstroke / power:** hot gas expands above the piston. Below it, decreasing crankcase volume compresses the next fresh charge, with the inlet reed shut.
3. **Exhaust blowdown:** the descending crown uncovers the higher exhaust port first. Gas starts escaping before transfer opens, reducing cylinder pressure.
4. **Transfer and scavenging:** the lower transfer port opens. Crankcase mixture enters and is directed upward, helping push remaining burnt gas toward exhaust. Some real engines lose fresh charge through the exhaust; that is not calculated here.
5. **Upstroke / port closing:** transfer closes first; exhaust stays open briefly. Fully trapped cylinder compression begins only after exhaust closes.
6. **Cylinder compression / crankcase filling:** rising piston squeezes the trapped cylinder charge while increasing crankcase volume below draws in new mixture through a reed. Reed movement is driven by pressure difference, not a cam.

So a power event can occur once per revolution, but this does **not** guarantee twice the useful power or better efficiency than a comparable four-stroke. Filling, scavenging, heat losses and operating conditions matter.

## 4. Exact timings in this teaching model

The selected numbers are illustrative, not universal engine specifications:

| Event | Open/visible interval |
| --- | --- |
| Two-stroke exhaust port | 105° ≤ angle < 255° |
| Two-stroke transfer port | 120° ≤ angle < 240° |
| Crankcase reed inlet cue | 190° ≤ angle < 350° |
| Two-stroke spark cue | 350–360° and 0–10° |
| Four-stroke spark cue | 350–370° of 720° cycle |

At **245°**, transfer is closed but exhaust is still open. This is explicitly captioned; calling the whole interval after 240° “both ports closed” would be wrong.

Piston-controlled openings are symmetric about BDC in this simplified geometry. Exhaust roof height equals the crown height at 105° and 255°. Transfer roof equals crown height at 120° and 240°. As the piston crown drops below a roof, the opening becomes exposed; on the upstroke it covers it again. The indicator changes at the boundary even though initial physical opening area would be zero.

The reed interval is merely a teaching cue. Real reed behavior depends on pressure waves, stiffness, flow and speed, so it cannot be predicted from the imposed angle interval alone. Scavenging arrows show a simplified net direction even while the piston has begun rising; actual flow directions/strengths depend on pressures and port geometry.

## 5. The linkage equation

Let crank radius r=0.6 and rod length L=1.8. The crank pin is:

```text
x = r sin θ
y = r cos θ
```

The piston pin stays on x=0. With fixed rod length:

```text
x² + (pistonY − crankY)² = L²
pistonY = r cos θ + √(L² − r² sin² θ)
```

Take the positive root because the piston is above the crank. TDC=2.4 and BDC=1.2 in arbitrary world units. The renderer places the crown 0.25 above the pin. These are consistent teaching proportions, not dimensions from a specific engine.

The motion is not a perfect sine wave: the rod-length square-root term makes piston speed/asymmetry differ from a simple cosine animation. At dead centres the instantaneous piston direction turns.

## 6. Read the visual cues carefully

- Blue incoming mixture and red exhaust arrows show flow; gold arrows may show compression or expansion force. The fixed stroke caption and side explanation distinguish them.
- Spark rays indicate an ignition event, not incoming/outgoing gas.
- Transfer arrows start in the crankcase and finish in the cylinder, not at an external fuel source.
- Front cylinder material is removed for a cutaway. The remaining shell, head, ports, crankcase and valves are schematic shapes, not sealed working CAD geometry.
- Phase-dependent colours don't show real pressure, temperature or chemical composition.

## 7. Questions to try

1. Pause four-stroke at 0° and 360°. What is the same geometrically? What changes in the cycle state?
2. Scrub two-stroke at 110°, 150°, 245° and 290°. Which ports are open at each?
3. Rotate behind the retained shell, then Reset view. Why is the front view easier for seeing the rod?
4. Compare the two cycles at the same teaching speed. How many power phases occur per crank revolution?

Further reading: [Four-stroke engine](https://en.wikipedia.org/wiki/Four-stroke_engine), [Two-stroke engine](https://en.wikipedia.org/wiki/Two-stroke_engine), [Slider-crank linkage](https://en.wikipedia.org/wiki/Slider-crank_linkage). These describe broader real-engine variations; the numbers above define this particular model.

Own illustrations/prose/code: [MIT licence](../LICENSE). Reference material retains its authors' rights; see [third-party notices](../THIRD_PARTY_NOTICES.md).
