# Enigma Lab: a beginner's code tour

Read [setup and controls](README.md), then [how Enigma works](HOW_ENIGMA_WORKS.md). You don't need to understand every formula before making the first lamp light.

## 1. A reading route

1. Run the app with default settings. Press A; expect lamp B and windows AAB.
2. Reset and type HELLOWORLD; expect ILBDAAMTAZ. Reset again before decrypting that result.
3. Read the constants at the top of `enigma.py`: alphabet, rotor wiring, reflector.
4. Read `_step()`, then `encode_letter()`. Follow the right-to-left outward path and left-to-right return.
5. Read `_through_rotor()` beside the formula in the mechanics guide.
6. Read `Lab.apply()` and `handle_event()` in `main.py` to see how settings and keypresses reach the model.
7. Run `test_enigma.py` and inspect the known-vector and double-step tests.

## 2. Strings can represent a permutation

`ALPHABET` is a string. Its index gives the numeric contact:

```python
ALPHABET[0]        # 'A'
ALPHABET.index('E') # 4
```

Rotor I's wiring string has 26 letters, each exactly once. At zero offset its first letter E says input contact A exits at E. This is a **permutation**, not a one-way encryption hash. An inverse permutation recovers the input contact from an output contact.

The constructor builds reverse wirings once:

```python
ALPHABET[wiring.index(char)]
```

For output E, `wiring.index('E')` is 0, so the reverse map returns A. The code computes this for every letter and each selected rotor. A rotor can map a contact to itself; don't confuse that with the whole machine's no-self-encoding property.

## 3. Keep order explicit

The configuration tuple `('I', 'II', 'III')` means **left, middle, right**. Python indexes those positions 0, 1 and 2. The outward signal visits indexes 2, 1, 0. The return visits 0, 1, 2 using inverse wiring.

The labels R/M/L in `last_trace` help distinguish signal direction from installation order. A very plausible bug is to reverse one but not the other; that is why reference vectors matter.

## 4. Modular arithmetic is a circular alphabet

`% 26` wraps a contact into the alphabet:

```python
25 + 1          # 26, outside the alphabet
(25 + 1) % 26   # 0, back to A
(-1) % 26       # 25, back to Z
```

The rotor transform changes coordinate systems, follows one wire, then changes coordinates back:

```text
external contact → add position-minus-ring → internal wire
→ subtract position-minus-ring → external contact
```

For rotor I at position B and ring A, input A becomes J. Work it out: contact `(0+1)%26=1`; wiring[1] is K=10; subtract 1 gives J=9. This is one rotor without stepping, not the whole machine's output.

## 5. State is what changes between calls

An `Enigma` instance owns its configuration and `_positions` list. `_positions` changes after each valid keypress. The `positions` property converts those numbers into a fresh display string. `initial_positions` remains available so `reset()` can return to the starting state.

Underscores mark internal helpers by convention; they aren't security barriers. Treat configuration and internals as read-only from application code. Construct another Enigma for a new configuration.

The constructor validates all settings before a usable machine is returned. `encode_letter()` validates before stepping, so a bad input doesn't half-change the machine. `process()` filters original ASCII characters before uppercasing; uppercasing arbitrary Unicode first would turn ß into SS and incorrectly add two rotor steps.

## 6. Double-stepping: inspect before changing

Try from the project folder in a Python REPL:

```python
from enigma import Enigma
machine = Enigma(rotors=('III', 'II', 'I'), positions='ADO')
for _ in range(4):
    machine.encode_letter('A')
    print(machine.positions)
```

Expected:

```text
ADP
ADQ
AER
BFS
```

At ADQ the right rotor's Q notch moves the middle to E. On the next press the middle starts at its own E notch, so it moves again and also moves the left rotor. Both notch flags must be captured **before** any position is updated.

Ring adjustment changes electrical offset, not these window-notch letters for I–V. Don't implement ring changes by moving Q/E/V/J/Z in the window test.

## 7. One keypress end to end

1. pygame supplies a `KEYDOWN` event or a clicked key rectangle.
2. `handle_event()` distinguishes editing a settings field from typing on the machine.
3. `Lab.press()` calls `machine.encode_letter()` once.
4. The model steps, applies plugs, traverses rotors, reflects, returns through inverses and applies plugs again.
5. `Lab` records input/output and the last lamp. The model records a list of `(label, letter)` trace tuples.
6. `draw()` renders current windows, lamp, transcript tail and trace without changing cipher state.

A physical Backspace cannot undo electrical/mechanical history. Our keyboard mode deliberately ignores it. Reset reinitializes the entire message; undo would need explicit state snapshots or replay.

## 8. Applying settings safely

The UI fields are draft strings. `Lab.apply()` first constructs a new Enigma in a local variable. Only if validation succeeds does it replace the live machine and clear the transcript. Invalid duplicate rotors or reused plug letters leave the old machine intact.

This is a small example of a **transactional update**: validate and prepare, then commit the new state. It is not a database transaction, but the same sequencing idea prevents half-applied changes.

The simple settings fields append typed letters/spaces; Backspace removes the last character and Ctrl+A (or Command+A) clears the whole field for replacement. They are not a full text editor: no cursor movement, selection or clipboard paste.

## 9. Test independent facts, not just round trips

Run:

```sh
python -m unittest discover -s tests -p test_enigma.py -v
```

A wrong reciprocal machine could still decrypt its own ciphertext. Stronger checks combine:

- Known configured inputs and outputs.
- Exact rotor-window sequences, especially double-stepping.
- Every wiring being a permutation.
- Inverse mappings undoing forward mappings.
- Invalid input leaving state unchanged.
- All 60 choices/orderings of three distinct rotors from five.

[Validation notes](VALIDATION.md) record a separate development comparison against py-enigma. That library is not imported by this app or its tests. The comparison is useful evidence, not a mathematical proof that every future change is correct.

## 10. Small exercises

1. **Trace one A.** Reset defaults; expect AAB, lamp B. Read each contact in `last_trace` and compare with the mechanics guide.
2. **Try another ring.** Compare fresh AAA/AAA with fresh AAA/AAB. Windows can agree while ciphertext differs. Then place the right rotor at its notch and verify turnover still uses the same window letter.
3. **Test plugboard reversal.** AB and BA describe the same swap. Two machines with those pairs and otherwise identical settings should produce the same message output.
4. **Propose undo before coding it.** Decide whether it restores windows, transcript and trace together. Write tests first; deleting a displayed character alone is insufficient.

## Glossary

| Term | Meaning here |
| --- | --- |
| Permutation | Rearrangement with no duplicate or missing contacts |
| Inverse | Mapping that undoes a previous mapping |
| Involution | Mapping that reverses itself, like a pair swap |
| Modulo | Wrap arithmetic around a fixed range |
| Instance | One machine with independent state |
| Property | Method-like calculation accessed as an attribute |
| Validation | Reject unsupported or malformed inputs before use |
| Reference vector | Fixed settings/input with independently checked expected output |

Python references: [classes](https://docs.python.org/3/tutorial/classes.html), [data structures](https://docs.python.org/3/tutorial/datastructures.html), [unittest](https://docs.python.org/3/library/unittest.html). History references are in [HISTORY.md](HISTORY.md).

Own code/docs: [MIT licence](../LICENSE); dependencies and linked references retain their own licences, as explained in [third-party notices](../THIRD_PARTY_NOTICES.md).

## Physical-looking art, separate from cipher state

`appearance.py` draws the carry case, metal deck, rotor windows, lamps and
round keys from primitives. Dark offset circles suggest a key stem; ivory disks
and an edge highlight suggest a raised keycap. The depressed key moves down
a few pixels. Alpha-blended concentric circles make a warm lamp halo without
an image asset. Clipping a moving letter strip to a rotor window lets the old
and new letters slide through a single aperture; stationary wheels do not roll.

`Lab.press()` remembers the previous windows, then calls `encode_letter()`
exactly once. It snapshots a timestamp for presentation, not encryption.
`animation()` returns rotor progress, key depression and lamp brightness from
elapsed milliseconds. Key-up, mouse-up or focus loss releases the visual key
without touching rotors or transcripts. Repeated keydown events are ignored.
The last result remains available even after the physical-looking lamp fades.

Rapid typing replaces the current visual transition; it is not queued cipher
work. Model tests still prove the same reference vectors, while animation tests
check release, double-stepping, settings isolation and read-only rendering.

## From a flat drawing to OpenGL

`scene3d.py` keeps camera maths independent of OpenGL imports. World coordinates
use x across the keyboard, y upward and z toward the operator. `Camera.basis()`
builds forward/right/up vectors with dot and cross products. Perspective shrinks
objects with distance; `project()` uses the same field of view and viewport as
OpenGL, letting a short click select a projected key. Dragging beyond six pixels
orbits instead. Camera distance/elevation are bounded for a usable view.

`Renderer` builds boxes and capped cylinders, applies normals, depth testing and
a directional-looking point light. Keys combine stems and round caps; the
active key changes height. Lamp emission adds visible brightness without changing
the cipher. Rotor drums and knurls rotate about their x axles. Each alphabet
letter is a cached alpha texture placed tangent to a ring. The top plaque gives
an easy-to-read logical position even while the ring is moving.

`view3d.View` owns the display context. Switching modes disposes GPU textures
and quadrics BEFORE destroying the old context. The 2D settings/trace are drawn
into an alpha surface and uploaded as an overlay texture after the 3D scene.
The transparent viewport lets the model show through. This reuses form logic
without sharing cipher state between two copies: there is only one `Lab`.

OpenGL imports are lazy and context creation is guarded. If it fails, recreate
a normal Pygame window and keep the 2D interface usable. Tests exercise this
fallback under SDL dummy, plus projection, orbit limits, click-versus-drag and
state preservation. A real-context smoke check is needed in addition to those
unit tests; GPU drawing cannot be proven by mocked calls alone.
