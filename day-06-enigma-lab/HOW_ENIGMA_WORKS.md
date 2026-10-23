# How this Enigma works

This is a model of **Enigma I with three moving rotors selected from I–V, an identity entry disc and fixed reflector B**. It is not every Enigma variant: it excludes naval VI–VIII, M4's fourth rotor, alternative reflectors and message-procedure automation. Never use it for modern secrets.

## 1. Parts you can see

- **Keyboard:** selects a letter A–Z.
- **Plugboard (Steckerbrett):** swaps paired letters before and after the rotor stack. AB means A↔B; unpaired letters stay unchanged.
- **Rotors:** each has 26 internal wires connecting a permutation of contacts. Their changing orientations change the substitution.
- **Windows:** show current rotor positions.
- **Ring setting (Ringstellung):** adjusts the alphabet/index ring relative to the wiring core. This is a different adjustment from changing the window position.
- **Reflector (Umkehrwalze):** connects contacts in pairs, sending current back through the rotors.
- **Lampboard:** lights the resulting letter.

Configuration triples are always **left, middle, right**, where right is the fast rotor. Electrical input travels in the opposite direction first:

```text
key → plugboard → right → middle → left → reflector B
lamp ← plugboard ← right ← middle ← left ← reflector B
```

The identity entry disc connects A to A, B to B, etc.; it adds no substitution in this variant. The UI omits that identity stage from its trace.

## 2. A rotor is a permutation, not a Caesar shift

Rotor I's wiring is:

```text
input:  ABCDEFGHIJKLMNOPQRSTUVWXYZ
output: EKMFLGDQVZNTOWYHXUSPAIBRCJ
```

At zero offset, A maps to E and B to K on the forward journey. The return journey uses the **inverse**, so E maps back to A. Individual rotors can have fixed points; it is the complete machine with this reflector that never maps a letter to itself.

Historical wiring and pre-keypress turnover window letters:

| Rotor | Wiring | Window notch |
| --- | --- | --- |
| I | EKMFLGDQVZNTOWYHXUSPAIBRCJ | Q |
| II | AJDKSIRUXBLHWTMCQGZNPYFVOE | E |
| III | BDFHJLCPRTXVZNYEIWGAKMUSQO | V |
| IV | ESOVPZJAYQUIRHXLNFTGKDCMWB | J |
| V | VZBRGITYUPSDNHLXAWMJQOFECK | Z |

Reflector B: `YRUHQSLDPXNGOKMIEBFZCWVJAT`. Sources: [Crypto Museum wiring](https://www.cryptomuseum.com/crypto/enigma/wiring.htm).

## 3. Position versus ring

A window letter describes the rotor's current orientation. Ring setting describes the index ring's relationship to the wiring. Our letters A–Z correspond to historical numeric ring settings 01–26; the arithmetic uses zero-based A=0 through Z=25.

For a contact value x, position p, ring r and wiring permutation W:

```text
offset = p - r
contact = (x + offset) mod 26
output = (W[contact] - offset) mod 26
```

For the return journey replace W with its inverse. `% 26` wraps around; in Python even a negative offset produces a result from 0 to 25.

At ring A, position B, rotor I receives A (0): offset=1, contact=1, W[1]=K (10), output=9 (J). This is a **single-rotor** calculation, not a full keypress. The complete machine steps before applying any signal transformations.

**Turnover nuance:** on these rotors the notch is attached to the index ring. Ring adjustment changes wiring relative to the displayed letters; it does **not** shift the turnover letters listed above. Rotating a rotor to another window letter and changing its ring can produce the same instantaneous electrical offset, but they need not produce the same future stepping schedule.

## 4. Step before the signal

Inspect notch positions before moving anything:

1. If the middle rotor is at its notch, step the left rotor.
2. If the middle OR right rotor is at its notch, step the middle rotor once.
3. Always step the right rotor.
4. Then pass the electrical signal through the machine.

This is not an ordinary odometer. With rotor order **III, II, I**, Crypto Museum's worked window sequence is:

| Before press | After press | Explanation |
| --- | --- | --- |
| ADO | ADP | Right I advances |
| ADP | ADQ | Right I advances to Q |
| ADQ | AER | Right I started at Q, so middle advances D→E |
| AER | BFS | Middle II started at E: left advances, middle advances again |

The middle rotor moves on consecutive presses: **double-stepping**. At AER the right rotor isn't at its notch; the middle rotor's own notch causes the next advance. See [Crypto Museum's mechanical explanation](https://www.cryptomuseum.com/crypto/enigma/working.htm).

## 5. First A, worked through the whole machine

Set order I–II–III, windows AAA, rings AAA, no plugboard pairs, reflector B. Press A. Windows first become **AAB**. The trace then is:

```text
Input A → Plug in A → R III C → M II D → L I F
→ Reflector B S → L I return S → M II return E
→ R III return B → Plug out B
```

The labelled letters are contact coordinates in the model's alphabet, not a claim that a physical rotor displayed all these letters at once. Only the windows display positions.

Continue five A presses from a fresh reset: `AAAAA → BDZGO`. Separately, from a fresh reset: `HELLOWORLD → ILBDAAMTAZ`. They are independent attempts, not consecutive messages. [Validation notes](VALIDATION.md) explain independent checks and their limits.

## 6. Why decryption uses the same operation

At one fixed rotor state the outward path is a permutation, the reflector pairs contacts, and the return path reverses the outward wiring. Plugboard swaps reverse themselves too. Therefore if A produces B at that state, B produces A at that same state.

For a message, both sender and receiver must use the same rotor order, rings, plugs and initial positions so each press reaches the same successive state. **Reset before typing the ciphertext.** Continuing from the end of encryption is not decryption.

Because reflector B has no self-connections, the complete machine has no letter that encrypts to itself. This structural property helped cryptanalysis; it does not make the cipher stronger.

## 7. Teaching conveniences and limits

- Hardware could support up to 13 plug pairs; this app deliberately limits input to ten, a common military operating choice. Historical practices varied.
- `process()` ignores non-ASCII characters without stepping. Real operators followed service/date-specific conventions for spacing, numbers and message indicators; this app does not reproduce those procedures.
- The lamp stays lit on the last output for study rather than only while holding a key.
- Input/output histories and signal traces are teaching additions. Backspace in keyboard mode does not undo a keypress or rotor state.
- No sound, saved messages, network or cryptanalysis tools are included.

See [history and usage](HISTORY.md), [beginner code tour](LEARNING_GUIDE.md), [MIT licence](../LICENSE) and [third-party notices](../THIRD_PARTY_NOTICES.md).
