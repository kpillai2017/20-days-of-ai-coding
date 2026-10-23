"""Educational Enigma I: three moving rotors, identity entry disc, reflector B.

Only this model knows cipher rules. It has no pygame, file, clock or network
code. See HOW_ENIGMA_WORKS.md for the formulas and historical limits.
"""
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Wiring is indexed A=0 ... Z=25, looking from the keyboard/entry-disc side.
# The notch is the WINDOW letter before a press which triggers turnover.
# Sources: https://www.cryptomuseum.com/crypto/enigma/wiring.htm
ROTOR_SPECS = {
    "I": {"wiring": "EKMFLGDQVZNTOWYHXUSPAIBRCJ", "notch": "Q"},
    "II": {"wiring": "AJDKSIRUXBLHWTMCQGZNPYFVOE", "notch": "E"},
    "III": {"wiring": "BDFHJLCPRTXVZNYEIWGAKMUSQO", "notch": "V"},
    "IV": {"wiring": "ESOVPZJAYQUIRHXLNFTGKDCMWB", "notch": "J"},
    "V": {"wiring": "VZBRGITYUPSDNHLXAWMJQOFECK", "notch": "Z"},
}
REFLECTOR_B = "YRUHQSLDPXNGOKMIEBFZCWVJAT"


def letters(value, length, name):
    """Validate ASCII BEFORE uppercasing: Unicode 'ß'.upper() is 'SS'."""
    if (not isinstance(value, str) or len(value) != length
            or any(char not in ALPHABET + ALPHABET.lower() for char in value)):
        raise ValueError(f"{name} must contain exactly {length} ASCII letters A-Z")
    return value.upper()


def parse_plugboard(value):
    """Return canonical pairs and an involution (a swap reverses itself).

    A dictionary starts with identity mappings for unplugged letters. Validate
    every pair before returning a completed mapping, never a half-built machine.
    Ten is our operational teaching limit, not the hardware maximum of thirteen.
    """
    if not isinstance(value, str):
        raise ValueError("plugboard must be text such as 'AB CD'")
    pairs = value.split()
    if len(pairs) > 10:
        raise ValueError("use at most ten plugboard pairs")
    mapping = dict(zip(ALPHABET, ALPHABET))
    used, normalized = set(), []
    for pair in pairs:
        pair = letters(pair, 2, "each plugboard pair")
        a, b = pair
        if a == b or a in used or b in used:
            raise ValueError("plugboard pairs must be disjoint, without self-pairs")
        used.update((a, b))
        mapping[a], mapping[b] = b, a
        normalized.append(pair)
    return " ".join(normalized), mapping


class Enigma:
    """Order all triples LEFT (slow), MIDDLE, RIGHT (fast), not signal order.

    Letters in positions/rings accept lower case and normalize to upper case.
    Rings A...Z represent historical settings 01...26. For a new configuration
    construct a new machine; reset restores this one's original window letters.
    """
    def __init__(self, rotors=("I", "II", "III"), positions="AAA", rings="AAA", plugboard=""):
        if (not isinstance(rotors, (tuple, list)) or len(rotors) != 3
                or any(not isinstance(name, str) or name not in ROTOR_SPECS for name in rotors)
                or len(set(rotors)) != 3):
            raise ValueError("select three different rotors from I, II, III, IV, V")
        self.rotor_names = tuple(rotors)
        self.initial_positions = letters(positions, 3, "positions")
        self.rings = letters(rings, 3, "rings")
        self.plugboard_pairs, self._plugs = parse_plugboard(plugboard)
        self._rings = [ALPHABET.index(char) for char in self.rings]
        self._wirings = [ROTOR_SPECS[name]["wiring"] for name in self.rotor_names]
        # Inverse permutation: locate which input contact produces an output.
        # Precompute once, rather than searching for it on every keypress.
        self._inverse = ["".join(ALPHABET[wiring.index(char)] for char in ALPHABET)
                         for wiring in self._wirings]
        self.reset()

    @property
    def positions(self):
        """A fresh display string, not the internal mutable list of numbers."""
        return "".join(ALPHABET[position] for position in self._positions)

    def reset(self):
        self._positions = [ALPHABET.index(char) for char in self.initial_positions]
        self.last_trace = []

    def _step(self):
        # Inspect ALL notches BEFORE changing any window. A normal odometer
        # carry is wrong: a middle rotor at its notch also steps itself.
        middle_notch = ALPHABET[self._positions[1]] == ROTOR_SPECS[self.rotor_names[1]]["notch"]
        right_notch = ALPHABET[self._positions[2]] == ROTOR_SPECS[self.rotor_names[2]]["notch"]
        if middle_notch:
            self._positions[0] = (self._positions[0] + 1) % 26
        if middle_notch or right_notch:
            self._positions[1] = (self._positions[1] + 1) % 26
        self._positions[2] = (self._positions[2] + 1) % 26
        # For I-V the notch is attached to the index ring. Changing Ringstellung
        # changes wiring relative to the window, NOT these window-notch letters.

    def _through_rotor(self, value, index, reverse=False):
        offset = self._positions[index] - self._rings[index]
        contact = (value + offset) % 26
        wiring = self._inverse[index] if reverse else self._wirings[index]
        return (ALPHABET.index(wiring[contact]) - offset) % 26

    def encode_letter(self, letter):
        # Validate BEFORE stepping so invalid calls leave the machine unchanged.
        letter = letters(letter, 1, "input")
        self._step()
        trace = [("Input", letter)]
        value = ALPHABET.index(self._plugs[letter])
        trace.append(("Plug in", ALPHABET[value]))
        # Signal enters from the RIGHT. Human configuration order is opposite.
        for index, role in ((2, "R"), (1, "M"), (0, "L")):
            value = self._through_rotor(value, index)
            trace.append((f"{role} {self.rotor_names[index]}", ALPHABET[value]))
        value = ALPHABET.index(REFLECTOR_B[value])
        trace.append(("Reflector B", ALPHABET[value]))
        for index, role in ((0, "L"), (1, "M"), (2, "R")):
            value = self._through_rotor(value, index, reverse=True)
            trace.append((f"{role} {self.rotor_names[index]} return", ALPHABET[value]))
        output = self._plugs[ALPHABET[value]]
        trace.append(("Plug out", output))
        self.last_trace = trace
        return output

    def process(self, text):
        """Skip everything outside ASCII A-Z/a-z, with NO extra rotor steps.

        Real operators used specific message procedures. This whitespace policy
        is a teaching convenience, not a reconstruction of all those procedures.
        """
        if not isinstance(text, str):
            raise ValueError("message must be text")
        return "".join(self.encode_letter(char) for char in text
                       if char in ALPHABET + ALPHABET.lower())
