# Day 06 · Enigma Lab

An interactive **Python + pygame** simulation of an Enigma I: three moving rotors chosen from I–V, identity entry disc, fixed reflector B, ring settings and plugboard. Type a letter, watch the windows advance, see the lamp light and follow the signal trace.

**For history and learning only. Not secure encryption.** No audio, saved messages, clipboard export, networking or AI API. The simulated machine's behavior is carefully scoped; it is not every historical Enigma variant or operating procedure.

## 1. Install and run

Use **Python 3.9–3.13**; 3.12/3.13 is recommended for convenient pygame wheels. Update your clone with `git pull` or download/extract the repository ZIP. From the repository root:

### macOS / Linux

```sh
cd day-06-enigma-lab
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

### Windows PowerShell

```powershell
cd day-06-enigma-lab
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

A virtual environment isolates packages from other projects. Windows commands use its interpreter directly so activation-policy restrictions aren't an obstacle. On macOS/Linux you can also use `.venv/bin/python` without activation. `deactivate` leaves an activated environment.

The fixed desktop window is **1080 × 860**; it isn't a phone/browser app. A graphical session is needed for normal play. The requirements install pygame plus PyOpenGL for the optional 3D view; the 2D view also works without PyOpenGL. The cipher model and its tests require Python alone.

## 2. First experiment: encrypt, reset, decrypt

Default settings: rotors **I II III** left-to-right, start **AAA**, rings **AAA**, no plugs.

1. Click an on-screen key or type A–Z using your physical keyboard.
2. First A gives **B**, and the rotor windows become **AAB**.
3. Click **Reset message**. Type **HELLOWORLD**. Expect **ILBDAAMTAZ**.
4. Reset again with the same settings. Type **ILBDAAMTAZ**. Expect **HELLOWORLD**.

Reset is essential: decryption starts from the same initial state, not from the encryption's final windows. IN means what you typed; OUT means the result. The same controls encrypt and decrypt.

## 3. Controls and settings

| Control | Behavior |
| --- | --- |
| On-screen keyboard / physical A–Z | One letter and one rotor step per press |
| Rotors L M R | Three distinct names separated by spaces, e.g. `V III II` |
| Start L M R | Three initial window letters, e.g. `MCK` |
| Rings L M R | Three ring letters, e.g. `BDF`; A corresponds to 01 |
| Plug pairs | Up to ten disjoint pairs, e.g. `AB CD EF`; blank means none |
| Apply + reset / Enter in a field | Validate all drafts; on success replace machine and clear transcript |
| Reset message | Restore the **applied** initial positions and clear transcript/trace |
| Keyboard mode | Leave settings editing and return to machine typing |
| Tab / Shift+Tab | Select next/previous settings field |
| Escape | Leave a settings field; otherwise quit |

Click a field to edit. Fields append letters/spaces; Backspace removes the last character; **Ctrl+A or Command+A clears the field** for replacement. These lightweight fields do not implement cursor selection or paste. They accept up to 40 characters; a ten-pair plugboard string needs 29. Type rotor names in uppercase or lowercase; valid values normalize to uppercase on Apply.

Editing a field never encrypts letters or advances rotors. Draft changes don't affect the live machine until Apply succeeds. Invalid settings display an error and preserve the live machine and transcript. Reset does not apply draft changes.

Machine typing ignores spaces, punctuation, digits and non-ASCII letters; they don't step the rotors. No key auto-repeat. Backspace in keyboard mode does **not** rewind. The physical-looking lamp glows while a key is held and fades after release; the last output remains in the transcript and LAST KEY / LAMP readout. Input/output show the most recent six five-letter groups; full in-memory transcripts are limited to 500 letters. At the limit the app refuses further presses without stepping. Reset clears them; closing the app loses them. Five-letter grouping is display formatting, not an encrypted space character.

## 4. Teaching documents

- **[How Enigma works](HOW_ENIGMA_WORKS.md):** wiring, ring versus position, modular arithmetic, double-stepping, a complete first-A trace and reciprocity.
- **[Brief history and usage](HISTORY.md):** commercial origins, military use, key sheets, Polish breakthroughs and the wider Allied effort.
- **[Beginner code tour](LEARNING_GUIDE.md):** data structures, classes, inverse permutations, input handling and exercises.
- **[Validation notes](VALIDATION.md):** exact reference settings and independent implementation checks.

## 5. Files and architecture

```text
day-06-enigma-lab/
├── enigma.py              # Pure cipher model; no pygame import
├── main.py                # UI state, event routing and animation timing
├── appearance.py          # Original procedural case, rotor, key and lamp artwork
├── requirements.txt       # pygame 2.6.1 only
├── README.md
├── HOW_ENIGMA_WORKS.md
├── HISTORY.md
├── LEARNING_GUIDE.md
├── VALIDATION.md
└── tests/
    ├── test_enigma.py     # Reference vectors, stepping and validation
    └── test_window.py     # Headless pygame controls and drawing
```

`Enigma(rotors=('I','II','III'), positions='AAA', rings='AAA', plugboard='')` configures a machine. All triples use left/middle/right order. `encode_letter()` accepts exactly one ASCII letter; `process()` encodes a string while skipping other characters. `positions` exposes current windows; `reset()` restores initial windows; `last_trace` holds contact labels and letters for the latest press. Invalid inputs raise `ValueError` before stepping.

`Lab` holds draft field strings, live machine, transcripts and last lamp. `handle_event()` ensures settings editing and cipher input are exclusive. `draw()` only reads state. `run()` handles events, draws, presents, and caps redraws at 60 FPS; animation clocks never determine cipher results. `finally` closes pygame even after an exception. The `__main__` guard allows tests to import functions without launching a window.

## 6. Tests

From this day's folder, model tests need Python alone:

```sh
python -m unittest discover -s tests -p test_enigma.py -v
```

After installing pygame:

```sh
python -m unittest discover -s tests -v
```

Window tests use SDL's dummy driver and skip if pygame is absent. Test each day's Python files in a separate process to avoid identically named `main.py` modules colliding. CI runs the suite and a five-frame real-loop smoke check on Python 3.9, 3.12 and 3.13.

macOS/Linux smoke check:

```sh
SDL_VIDEODRIVER=dummy python main.py --frames 5
```

PowerShell:

```powershell
$env:SDL_VIDEODRIVER = "dummy"
.\.venv\Scripts\python.exe main.py --frames 5
Remove-Item Env:SDL_VIDEODRIVER
```

`--frames` must be positive; it does not itself enable headless mode. Unset the dummy driver for normal play.

### Manual checklist

- Confirm first A/default windows and HELLOWORLD examples above.
- Edit fields, including invalid duplicate rotors/reused plugs: ensure no hidden keypresses or transcript loss.
- Apply III II I / ADO / AAA / no plugs. Four presses show ADP, ADQ, AER, BFS.
- Repeat with non-A ring settings: the turnover **window letters** stay the same.
- Reset and decrypt with identical settings; check input/lamp/trace agree.
- Quit by Escape outside a field or close the window.

## 7. Troubleshooting and limitations

- **No pygame:** install requirements using the same environment interpreter that runs main.py.
- **Source-build installation errors:** upgrade pip, then try Python 3.12/3.13 with a prebuilt pygame wheel.
- **No visible window:** remove `SDL_VIDEODRIVER=dummy`; normal operation needs a display. The 1080×860 layout may not fit a small desktop.
- **Letters edit fields instead of encrypting:** click Keyboard mode or press Escape to leave the field.
- **Unexpected decryption:** reset first and match every setting, including rotor order and rings. Starting position and ring setting are not interchangeable.
- **Transcript tail only:** intentional; this is a teaching display, not a message archival tool. No file/export/undo features are promised.

The pygame-drawn fields/buttons do not expose native screen-reader widgets. Keyboard configuration navigation is provided, but this UI is not a fully accessible desktop form. The pure model can be explored from a terminal without graphics.

## Licence, attribution and references

Original educational code and prose created with AI coding assistance. Historical wiring data is attributed to [Crypto Museum's wiring tables](https://www.cryptomuseum.com/crypto/enigma/wiring.htm); no photographs, museum prose, sound or third-party source code is bundled. History sources are listed in [HISTORY.md](HISTORY.md).

Own code/docs: [MIT licence](../LICENSE). pygame is installed separately under its [LGPL 2.1 licence](https://github.com/pygame/pygame/blob/2.6.1/docs/LGPL.txt); its default font and native dependencies retain upstream rights. The independent py-enigma comparison was a development check, not an application dependency. See [third-party notices](../THIRD_PARTY_NOTICES.md).

## Physical-machine-inspired view

The machine face now uses an original shaded wooden carry case, metal deck,
ivory round typewriter keys, circular lamp lenses, a warm lamp halo and three
rotor letter windows with knurled wheel edges. The historical staggered
QWERTZ-style key/lamp layout and all existing settings controls are retained.
Click and hold a key (or hold its physical keyboard letter): the key depresses
and the enciphered output lamp glows. Release or leaving window focus releases
the key and lets the lamp fade. A held key does not auto-repeat.

Rotor windows roll one letter over approximately 240 ms when their wheel
actually steps, including turnover and double-stepping. The model steps once
BEFORE computing the signal; animation merely visualises that completed state.
Rapid typing never waits for an animation, loses a letter or adds a step: the
latest press replaces the visual transition. Reset/apply clears animation.

This is an illustrative **2D** Enigma-inspired machine face, not a mechanically exact reconstruction. A separate OpenGL 3D view is now available (below). It does not show exposed internal wiring or
simulate key interlocks, contact bounce, sound or physical plug insertion. The
configuration form still controls the plugboard. No photos, logos, historic
insignia, museum scans, fonts or commercial art were copied or bundled.

## Optional 3D view — Pygame + OpenGL

Reinstall requirements after updating: `python -m pip install -r requirements.txt`.
This installs **PyOpenGL 3.1.10** alongside Pygame. You also need a working desktop
OpenGL **compatibility** context/driver; no GPU models, textures or shaders are
downloaded. Start normally and click **3D view**, or launch directly:

```sh
python main.py --3d
```

- **Left-drag within the machine viewport:** orbit the camera (360° horizontally;
  elevation limited to avoid pole flips).
- **Mouse wheel:** zoom in/out, within safe distance limits.
- **Short left-click on a visible 3D key:** enter one letter with a brief animated
  key/lamp pulse. A drag never types a letter. Mouse picking is disabled when
  viewing from below or behind the case to avoid typing through its walls.
- **Physical keyboard:** hold A–Z to depress the key and illuminate its output
  lamp; release to fade. Clear settings focus using Keyboard mode first.
- **Reset 3D view:** restore the default camera only, not the cipher.
- **2D view / 3D view:** switch presentation without clearing text or rotor state.
- Configuration, Apply/reset, Reset message and the signal trace remain available.

The original procedural 3D model includes a thick wooden case, open lid, raised
keycaps and stems, lamp lenses, rotor drums with rotating knurls/alphabet rings
and readable window plaques. Selected lamps use emissive material. This is a
low-poly **historically inspired illustration**, not a dimensionally exact
reconstruction: no internal pawls, real contacts, removable components, ray-
traced light, editable physical cables or mechanical interlocks are simulated.
Window plaques show the current logical letter; the underlying ring/wheel rolls
over 240 ms. Plug sockets are decorative; use the configuration form.

If PyOpenGL or a usable context is unavailable, the app reports the failure and
returns to 2D. SDL's dummy driver cannot render OpenGL; headless CI tests maths,
interaction and fallback, not GPU image quality. 2D/model tests work without
PyOpenGL. Rendering uses compatibility-era fixed-function APIs for readability;
this is not a modern shader-performance tutorial.
