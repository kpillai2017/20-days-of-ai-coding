# What makes a mechanical clock tick?

## The real energy path

```text
raised weight / wound spring
             ↓ stored energy
       wheel train (gears)
             ↓ controlled release
       escapement ↔ pendulum
             ↓ counted rotation
          dial hands
```

A raised weight stores gravitational potential energy. As it falls, it turns a drum and gear train. A spring-driven clock supplies energy differently but still needs controlled release. Without a regulator the train would run down quickly, not keep time.

The **escapement** both limits release and gives the oscillator small energy impulses to replace frictional losses. In an anchor escapement, two pallets alternately lock/release teeth of an escape wheel as the anchor rocks. It is not simply a pendulum knocking the hour hand forward.

## Pendulum rhythm

For a small-angle ideal simple pendulum:

```text
T ≈ 2π √(L / g)
```

T is one complete back-and-forth period, L effective length, g gravitational acceleration. A roughly two-second oscillator has one endpoint/tick per second. Real regulation depends on effective length, temperature, friction, amplitude and escapement design; decorative pixels are not physical metres.

Here the bob follows `angle = 0.19 × sin(π × epochSeconds)`: a two-second period with alternating extremes half a second after each whole-second timestamp. A tick/tock cue sounds at those extremes. The sound timing is browser polling, not a simulated pallet contact. The drawn anchor's motion is illustrative and does not determine tooth release or pendulum energy.

## Gears exchange speed and direction

For ideal externally meshing gears, contact pitch speeds agree:

```text
ω₁ r₁ = −ω₂ r₂
```

A smaller gear spins faster; neighbouring external wheels turn opposite ways. Coaxial pinions can transmit rotation to a second wheel plane, allowing large overall ratios. A real motion-work mechanism produces a 12:1 minute-to-hour relation, while the minute hand completes a turn per hour and the hour hand per twelve hours.

Both the preserved v0.1 illustration and the v0.2 solid 3D scene assign alternating gear directions and related radius speeds for a readable exposed train. Tooth shapes, overlaps, clearances and the anchor are artistic approximations. There is no complete train connecting the illustrated wheels to the hands, no tooth-contact solver and no bill of materials. Do not use this as a printable mechanism design.

## Our time path is intentionally reversed

```text
OS local time → Date → hand angles
                    → pendulum/gear illustration
                    → safe sound-boundary scheduler
```

The system time is authoritative. Reading Date every frame avoids accumulated error from incrementing seconds in a timer. After a slow frame the picture simply shows the current time. This keeps a visual clock correct but does not model a real autonomous mechanism.

## Chimes are a separate mechanism in a real clock

Many striking clocks have a separate train for chimes/strikes, triggered by the time train. Pins, cams and hammers can sequence tuned rods or bells. Counting strikes is not the same as the escapement's tick.

Our Web Audio engine substitutes generated resonant tones, not recordings. One, two and three phrases mark the first three quarters. Four phrases introduce the hourly 1–12 strikes. These are original arrangements, not a claimed authentic Westminster composition. You can preview them; previews never alter civil time.

## See and question the simplifications

- The weights remain at fixed heights; no winding or declining power reserve.
- Gear teeth have decorative profiles and simplified contact.
- Pendulum motion is prescribed, not integrated from gravity/impulses.
- Glass reflections are canvas gradients, not ray-traced optics.
- No audio plays without browser permission; hidden/sleeping tabs miss bells.

A useful simulation makes its assumptions visible. The goal is to invite exploration of energy, gearing, oscillation and timekeeping without implying engineering accuracy.

References: [Britannica pendulum](https://www.britannica.com/science/pendulum), [escapement](https://www.britannica.com/technology/escapement), and the [project setup/provenance guide](README.md).

## Inspect in three dimensions

Toggle to 3D and left-drag to inspect the open-backed case, extruded wheels, axles and pendulum from all directions. Reset restores the default view. Real geometric depth does not make the motion physically accurate: the same prescribed time-driven state feeds both renderers. The original 2D v0.1 view remains available unchanged as artwork.


### Gear-motion refinement

Both views now share `gears.js`: a common tooth module, exact pitch-circle contact distances, alternating directions and tooth-count-derived angular speeds. Contact-direction phases put each tooth crown against a neighbour's gap, including where the train turns a corner. A four-root-turn cycle bounds numeric angles without introducing a visual jump. All wheels remain driven by the same elapsed time; none runs an independent timer. The visible root speed is 0.28 radians/second for clarity, not a real clock reduction ratio.

The revised U-shaped layout avoids unrelated wheels overlapping. The 3D view reflects both y coordinates and tooth-angle direction consistently. This improves visual kinematic coherence but is still not an involute tooth-contact, force, friction or escapement simulation. Original v0.1 artwork remains the basis of the 2D view; its gear layout/motion received this correction in the combined app.
