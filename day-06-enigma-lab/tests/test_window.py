"""Exercise actual pygame controls/rendering with SDL's invisible dummy driver.

A display smoke test doesn't prove usability on every monitor. Try the app by
hand too; keep each day's Python tests in a separate process (main.py names).
"""
from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    import pygame
    import main
except ModuleNotFoundError as error:
    if error.name != 'pygame':
        raise
    pygame = None


@unittest.skipIf(pygame is None, 'pygame not installed; model tests still work')
class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.environment = patch.dict(os.environ, {'SDL_VIDEODRIVER':'dummy'})
        cls.environment.start()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.environment.stop()

    def tearDown(self):
        pygame.quit()

    def key(self, lab, key, char='', mod=0):
        return main.handle_event(pygame.event.Event(pygame.KEYDOWN,key=key,unicode=char,mod=mod), lab)

    def click(self, lab, rect):
        return main.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=rect.center),lab)

    def test_physical_keyboard_and_mouse_reference_vector(self):
        lab=main.Lab()
        for char in 'hello':
            self.key(lab,ord(char),char)
        for char in 'WORLD':
            self.click(lab,main.key_rects(542)[char])
        self.assertEqual(lab.plain,'HELLOWORLD')
        self.assertEqual(lab.cipher,'ILBDAAMTAZ')
        self.assertEqual(lab.lamp,'Z')
        self.assertEqual(lab.machine.positions,'AAK')

    def test_reset_then_decrypt_and_backspace_does_not_rewind(self):
        lab=main.Lab()
        for char in 'HELLOWORLD': lab.press(char)
        cipher=lab.cipher
        self.click(lab,main.RESET)
        self.assertEqual(lab.machine.positions,'AAA')
        self.assertEqual((lab.plain,lab.cipher,lab.lamp),('','',None))
        for char in cipher: lab.press(char)
        self.assertEqual(lab.cipher,'HELLOWORLD')
        before=(lab.machine.positions,lab.cipher)
        self.key(lab,pygame.K_BACKSPACE)
        self.assertEqual((lab.machine.positions,lab.cipher),before)

    def test_fields_edit_without_cipher_steps_and_apply(self):
        lab=main.Lab()
        self.click(lab,main.FIELDS[1][2])  # initial windows
        self.key(lab,pygame.K_a,'a',pygame.KMOD_CTRL)
        for char in 'bcd': self.key(lab,ord(char),char)
        self.assertEqual(lab.fields['positions'],'BCD')
        self.assertEqual(lab.machine.positions,'AAA')
        self.assertEqual(lab.plain,'')
        self.key(lab,pygame.K_RETURN)
        self.assertEqual(lab.machine.positions,'BCD')
        self.assertIsNone(lab.active_field)

    def test_invalid_apply_preserves_live_machine_and_transcript(self):
        lab=main.Lab();lab.press('A')
        machine=lab.machine
        lab.fields['rotors']='I I III'
        self.assertFalse(lab.apply())
        self.assertIs(lab.machine,machine)
        self.assertEqual((lab.machine.positions,lab.cipher),('AAB','B'))
        self.assertIn('Settings error',lab.message)
        lab.fields['rotors']='V III II'
        lab.fields['positions']='MCK'
        lab.fields['rings']='BDF'
        lab.fields['plugboard']='AV BS CG DL FU HZ IN KM OW RX'
        self.assertTrue(lab.apply())
        for char in 'ENIGMALABTEACHESROTORS':lab.press(char)
        self.assertEqual(lab.cipher,'XGWFNZPJFXTVBBVYUMGEBI')

    def test_tab_escape_and_ignored_nonletters(self):
        lab=main.Lab()
        self.key(lab,pygame.K_TAB)
        self.assertEqual(lab.active_field,'rotors')
        self.key(lab,pygame.K_TAB,mod=pygame.KMOD_SHIFT)
        self.assertEqual(lab.active_field,'plugboard')
        self.assertTrue(self.key(lab,pygame.K_ESCAPE))
        self.assertIsNone(lab.active_field)
        for char in (' ','1','ß','K','🙂'):
            self.key(lab,pygame.K_SPACE,char)
        self.key(lab,pygame.K_c,'c',pygame.KMOD_CTRL)
        self.assertEqual(lab.machine.positions,'AAA')
        self.assertFalse(self.key(lab,pygame.K_ESCAPE))
        self.assertFalse(main.handle_event(pygame.event.Event(pygame.QUIT),lab))

    def test_transcript_limit_is_explicit_and_does_not_step(self):
        lab=main.Lab()
        for _ in range(500):lab.press('A')
        before=lab.machine.positions
        lab.press('A')
        self.assertEqual(len(lab.cipher),500)
        self.assertEqual(lab.machine.positions,before)
        self.assertIn('limit',lab.message)

    def test_render_default_trace_and_invalid_settings(self):
        pygame.display.init();pygame.font.init()
        screen=pygame.display.set_mode((main.WIDTH,main.HEIGHT))
        fonts=tuple(pygame.font.Font(None,size) for size in (21,24,34))
        lab=main.Lab()
        main.draw(screen,lab,fonts)
        lab.press('A');main.draw(screen,lab,fonts)
        lab.fields['plugboard']='AB AC';lab.apply();main.draw(screen,lab,fonts)
        self.assertEqual(screen.get_size(),(1080,860))
        self.assertEqual(set(main.key_rects(542)),set('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        self.assertEqual(main.grouped_tail('ABCDEFGHIJK'),'ABCDE FGHIJ K')

    def test_real_loop_and_cleanup(self):
        main.run(max_frames=3)
        self.assertFalse(pygame.display.get_init())

    def test_window_close_in_real_loop(self):
        with patch.object(pygame.event,'get',return_value=[pygame.event.Event(pygame.QUIT)]):
            main.run(max_frames=3)
        self.assertFalse(pygame.display.get_init())


if __name__ == '__main__':
    unittest.main()
