# Cipher validation notes

## Scope

Enigma I-style identity entry disc, rotors I–V, reflector B, three moving wheels. All orders, positions and rings below are **left/middle/right**. Positions are the window letters **before** the first press. Rings A–Z mean 01–26.

Historical wiring and stepping references: [Crypto Museum wiring](https://www.cryptomuseum.com/crypto/enigma/wiring.htm) and [mechanical explanation/double-step example](https://www.cryptomuseum.com/crypto/enigma/working.htm).

## Fixed reference cases

Fresh machine for each row:

| Rotors | Start | Rings | Plugboard | Input | Output | Final windows |
| --- | --- | --- | --- | --- | --- | --- |
| I II III | AAA | AAA | none | AAAAA | BDZGO | AAF |
| I II III | AAA | AAA | none | HELLOWORLD | ILBDAAMTAZ | AAK |
| V III II | MCK | BDF | AV BS CG DL FU HZ IN KM OW RX | ENIGMALABTEACHESROTORS | XGWFNZPJFXTVBBVYUMGEBI | MDG |

These ciphertexts were independently checked against **py-enigma 1.0.2** during development on 23 October 2026. The third message is an original development fixture, not a claimed historical intercepted message. The first two are convenient standard demonstrations; their explicit settings matter more than the phrase alone.

For rotors III II I, start ADO, rings AAA, no plugs, four successive presses produce windows **ADP → ADQ → AER → BFS**, matching Crypto Museum's published mechanical example.

## Additional independent comparison

A temporary, separately installed py-enigma 1.0.2 instance was compared against this model for **100 deterministic random configurations of 500 letters each**: 50,000 letters in total. The check varied three distinct rotors from I–V, start positions, non-default rings and ten disjoint plugboard pairs. Both output strings and final windows matched.

The comparison used a private Python `Random(2026)`, py-enigma's `EnigmaMachine.from_key_sheet(...)`, zero-based numeric `ring_settings`, reflector B and `set_display(start)`. The local model was loaded under a different module name using `importlib.util`, because both libraries otherwise use the name `enigma`.

This was a development experiment, not a runtime dependency, a CI network requirement or a formal proof. No py-enigma source is copied or bundled. See its [documentation](https://py-enigma.readthedocs.io/en/latest/) for its own implementation and terms.

## What automated tests additionally check

- All wiring strings are permutations; reflector B is reciprocal and has no fixed point.
- Forward and inverse rotor transforms undo each other.
- Exact double-stepping and right-wheel wrap behavior.
- Turnover window letters don't shift when ring settings change.
- Every one of the 60 three-rotor arrangements round-trips and avoids self-encoding.
- Invalid settings/letters leave live state unchanged; Unicode uppercase expansions aren't mistaken for ASCII letters.
- UI configuration edits don't advance the machine; failed Apply preserves the current transcript.

A reciprocal cipher can still be historically wrong. Round trips alone are therefore not enough; keep fixed outputs, window sequences and independent checks when changing the model.

Own notes: [MIT licence](../LICENSE). Reference software and linked material retain their own rights.

## Physical-view regression checks

New headless tests cover key down/up, mouse release, focus loss, repeat-event
rejection, lamp fade, reset, rapid reference-vector typing, actual double-step
window transitions and read-only rendering at multiple animation times.
The original pure cipher model is unchanged. Rendering was visually inspected
at an intermediate rotor step; this is not a claim of measured dimensional
accuracy or historical machine certification.

## OpenGL view validation

The expanded suite has **41 tests** across cipher, interface, animation, camera
and fallback. The new camera tests require no OpenGL. SDL dummy checks verify
that unavailable contexts fall back to a working 2D window. A real macOS OpenGL
compatibility context was also exercised: 3D rendering, camera orbit, emissive
lamp/rotor appearance, and repeated 3D → 2D → 3D context recreation. A rendered
frame was visually reviewed. This is platform-specific smoke evidence, not a
guarantee for every graphics driver or accessibility certification.
