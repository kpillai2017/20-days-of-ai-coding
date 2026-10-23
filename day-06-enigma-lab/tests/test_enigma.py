"""Deterministic model tests: no display and no third-party test dependencies.

Round-trip tests alone are insufficient: the same wrong rotor algorithm could
reverse itself. Reference outputs and exact window sequences check the model.
"""
from pathlib import Path
import itertools
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from enigma import ALPHABET, ROTOR_SPECS, REFLECTOR_B, Enigma


class EnigmaTests(unittest.TestCase):
    def test_wirings_are_permutations_and_reflector_is_fixed_point_free_involution(self):
        for spec in ROTOR_SPECS.values():
            self.assertEqual(sorted(spec['wiring']), list(ALPHABET))
        for index, char in enumerate(REFLECTOR_B):
            self.assertNotEqual(char, ALPHABET[index])
            self.assertEqual(REFLECTOR_B[ALPHABET.index(char)], ALPHABET[index])

    def test_reference_vectors_default(self):
        # Independently checked against py-enigma 1.0.2; see VALIDATION.md.
        for plain, expected in [('AAAAA','BDZGO'), ('HELLOWORLD','ILBDAAMTAZ')]:
            with self.subTest(plain=plain):
                self.assertEqual(Enigma().process(plain), expected)

    def test_reference_vector_nontrivial_rings_and_plugs(self):
        machine = Enigma(('V','III','II'), 'MCK', 'BDF', 'AV BS CG DL FU HZ IN KM OW RX')
        self.assertEqual(machine.process('ENIGMALABTEACHESROTORS'), 'XGWFNZPJFXTVBBVYUMGEBI')
        self.assertEqual(machine.positions, 'MDG')

    def test_historical_double_step_example(self):
        machine = Enigma(('III','II','I'), 'ADO')
        for expected in ('ADP','ADQ','AER','BFS','BFT'):
            machine.encode_letter('A')
            self.assertEqual(machine.positions, expected)

    def test_default_double_step(self):
        machine = Enigma(positions='ADU')
        for expected in ('ADV','AEW','BFX'):
            machine.encode_letter('A')
            self.assertEqual(machine.positions, expected)

    def test_turnover_window_does_not_shift_with_ring(self):
        for rings in ('AAA','BCD','ZZZ'):
            machine = Enigma(positions='ADV', rings=rings)
            machine.encode_letter('A')
            self.assertEqual(machine.positions,'AEW')
            machine.encode_letter('A')
            self.assertEqual(machine.positions,'BFX')

    def test_right_wrap_is_not_automatic_middle_carry(self):
        machine = Enigma(positions='AAZ')  # III turns over at V, not Z.
        machine.encode_letter('A')
        self.assertEqual(machine.positions,'AAA')

    def test_each_right_notch_triggers_middle(self):
        for name, spec in ROTOR_SPECS.items():
            others = [n for n in ROTOR_SPECS if n != name][:2]
            machine = Enigma(tuple(others + [name]), 'AA'+spec['notch'])
            machine.encode_letter('A')
            self.assertEqual(machine.positions[1], 'B')

    def test_ring_setting_changes_wiring_but_not_initial_display(self):
        a,b = Enigma(),Enigma(rings='AAB')
        self.assertEqual(a.positions,b.positions)
        self.assertNotEqual(a.process('AAAAA'),b.process('AAAAA'))

    def test_all_sixty_rotor_orders_reciprocal_and_no_self_encoding(self):
        message = ALPHABET * 4
        for rotors in itertools.permutations(ROTOR_SPECS,3):
            machine = Enigma(rotors, 'QEV', 'CDE', 'AV BS CG DL FU HZ IN KM OW RX')
            cipher = machine.process(message)
            self.assertTrue(all(a != b for a,b in zip(message,cipher)))
            machine.reset()
            self.assertEqual(machine.process(cipher),message)

    def test_inverse_mapping_every_contact_position_ring(self):
        machine = Enigma(rings='BDF')
        for position in range(26):
            machine._positions = [position] * 3
            for index in range(3):
                for value in range(26):
                    forward = machine._through_rotor(value,index)
                    self.assertEqual(machine._through_rotor(forward,index,True),value)

    def test_trace_first_letter_and_output(self):
        machine=Enigma()
        self.assertEqual(machine.encode_letter('A'),'B')
        self.assertEqual(machine.positions,'AAB')
        self.assertEqual(machine.last_trace,[('Input','A'),('Plug in','A'),('R III','C'),
            ('M II','D'),('L I','F'),('Reflector B','S'),('L I return','S'),
            ('M II return','E'),('R III return','B'),('Plug out','B')])

    def test_reset_and_independent_instances(self):
        a,b=Enigma(positions='ABC'),Enigma(positions='ABC')
        a.process('HELLO')
        self.assertEqual(b.positions,'ABC')
        a.reset()
        self.assertEqual(a.positions,'ABC')
        self.assertEqual(a.last_trace,[])
        self.assertEqual(a.process('HELLO'),b.process('HELLO'))

    def test_case_normalization(self):
        machine=Enigma(positions='abc',rings='def',plugboard='ab cd')
        self.assertEqual((machine.positions,machine.rings,machine.plugboard_pairs),('ABC','DEF','AB CD'))
        self.assertEqual(machine.encode_letter('x'),Enigma(positions='ABC',rings='DEF',plugboard='AB CD').encode_letter('X'))

    def test_skip_nonascii_without_steps_including_uppercase_expansions(self):
        a,b=Enigma(),Enigma()
        self.assertEqual(a.process('A ßKé🙂-1b!'),b.process('AB'))
        self.assertEqual(a.positions,'AAC')
        before=a.positions
        self.assertEqual(a.process('123 ß🙂'),'')
        self.assertEqual(a.positions,before)

    def test_plugboard_unordered_pair_orientation_equivalent(self):
        self.assertEqual(Enigma(plugboard='AB CD').process(ALPHABET),
                         Enigma(plugboard='BA DC').process(ALPHABET))

    def test_ten_pairs_allowed_eleven_rejected(self):
        Enigma(plugboard='AB CD EF GH IJ KL MN OP QR ST')
        with self.assertRaises(ValueError):
            Enigma(plugboard='AB CD EF GH IJ KL MN OP QR ST UV')

    def test_invalid_configuration(self):
        for kwargs in [dict(rotors='I II III'),dict(rotors=('I','I','III')),dict(rotors=('I','II')),
                       dict(rotors=('I','II','VI')),dict(rotors=([],'II','III')),
                       dict(positions='AA'),dict(positions='AßA'),dict(positions=123),
                       dict(rings='12A'),dict(rings='AAAA'),dict(plugboard=None),
                       dict(plugboard='AA'),dict(plugboard='AB AC'),dict(plugboard='ABC'),
                       dict(plugboard='A1'),dict(plugboard='ßA')]:
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                Enigma(**kwargs)

    def test_invalid_letter_does_not_change_state_or_trace(self):
        machine=Enigma();machine.encode_letter('A')
        before=(machine.positions,machine.last_trace[:])
        for value in ('','AA','ß','K','!',None,1):
            with self.subTest(value=value),self.assertRaises(ValueError):
                machine.encode_letter(value)
            self.assertEqual((machine.positions,machine.last_trace),before)
        with self.assertRaises(ValueError):
            machine.process(None)
        self.assertEqual((machine.positions,machine.last_trace),before)


if __name__ == '__main__':
    unittest.main()
