"""Day 09 entry point: keyboard -> pure game model -> wireframe renderer.

Run `python main.py`. --frames N and --demo are for automated smoke tests.
Pygame supplies only the window, drawing, input, clock and optional audio.
"""
import argparse
from array import array
import math
import random

import pygame

from game import Controls, Game
from renderer import BLACK, Renderer


def read_controls(keys):
    """Map keys to a small model value, rather than importing pygame in game.py.

    Each tank track can move independently: left forward + right reverse turns
    right on the spot. Average speed drives forward; difference turns the hull.
    Conventional arrow/WASD controls are an accessibility/convenience alternative.
    """
    left = int(keys[pygame.K_t]) - int(keys[pygame.K_g])
    right = int(keys[pygame.K_u]) - int(keys[pygame.K_j])
    if left or right:
        throttle, turn = (left + right) / 2, (left - right) / 2
    else:
        throttle = int(keys[pygame.K_UP] or keys[pygame.K_w]) - int(keys[pygame.K_DOWN] or keys[pygame.K_s])
        turn = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
    return Controls(throttle, turn, bool(keys[pygame.K_SPACE]))


class Sounds:
    """Optional, original synthesised effects; no downloaded audio or samples.

    Signed 16-bit samples oscillate around zero. An envelope fades each sound
    smoothly to avoid an abrupt end-click. A missing audio device is harmless.
    """
    def __init__(self, enabled=True):
        self.enabled = False
        self.effects = {}
        self.engine = None
        if not enabled:
            return
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            rate = pygame.mixer.get_init()[0]
            rng = random.Random(9)  # Does not consume the game's random stream.
            for name, frequency, duration in [('shot', 190, .20), ('hit', 65, .48), ('enemy', 350, .12)]:
                samples = array('h')
                for i in range(int(rate * duration)):
                    t = i / rate
                    fade = 1 - t / duration
                    noise = rng.uniform(-1, 1) * (.7 if name == 'hit' else .15)
                    tone = math.sin(math.tau * frequency * t * (1 - t / (2*duration)))
                    samples.append(int((tone*.3 + noise*.3) * fade * 11000))
                self.effects[name] = pygame.mixer.Sound(buffer=samples)
            # A seamless integer number of cycles makes a low engine loop.
            samples = array('h', (int(1600 * (math.sin(math.tau*55*i/rate) + .3*math.sin(math.tau*110*i/rate))) for i in range(rate)))
            self.engine = pygame.mixer.Sound(buffer=samples)
            self.channel = self.engine.play(loops=-1)
            self.enabled = True
        except pygame.error:
            # Desktop/audio-less CI machines can still play the entire game.
            pygame.mixer.quit()

    def play(self, name):
        if self.enabled:
            self.effects[name].play()

    def motor(self, moving, active):
        if self.enabled and self.channel:
            self.channel.set_volume((.28 if moving else .1) if active else 0)


def positive_frames(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('frames must be positive')
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description='Original Battlezone-inspired wireframe tank game')
    parser.add_argument('--seed', type=int, default=None, help='reproducible initial world/AI random stream')
    parser.add_argument('--frames', type=positive_frames, help='exit after this many frames (testing)')
    parser.add_argument('--demo', action='store_true', help='start immediately and drive/fire automatically (testing)')
    parser.add_argument('--mute', action='store_true', help='disable synthesised sounds')
    args = parser.parse_args(argv)
    # Initialise just the subsystems we need: optional audio failure must not
    # prevent the display from starting. Font(None) uses Pygame's bundled font.
    pygame.display.init()
    pygame.font.init()
    window = pygame.display.set_mode((1000, 750), pygame.RESIZABLE)
    pygame.display.set_caption('Day 09 - Vector Tanks (Battlezone-inspired)')
    renderer = Renderer()
    game = Game(args.seed)
    game.state = 'playing' if args.demo else 'title'
    sounds = Sounds(not args.mute)
    clock = pygame.time.Clock()
    paused, running, frames = False, True, 0
    try:
        while running:
            dt = min(clock.tick(60) / 1000, .1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.WINDOWFOCUSLOST and game.state == 'playing':
                    paused = True  # No surprise deaths while in another app.
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RETURN:
                        if game.state != 'playing':
                            game.start()
                        paused = False
                    elif event.key == pygame.K_r:
                        game.start()
                        paused = False
                    elif event.key in (pygame.K_p, pygame.K_h) and game.state == 'playing':
                        paused = not paused
            controls = read_controls(pygame.key.get_pressed())
            if args.demo:
                controls = Controls(.6, .22, True)
            old_shot = game.cooldown
            old_score, old_lives = game.score, game.lives
            if not paused:
                game.update(dt, controls)
            if game.cooldown > old_shot:
                sounds.play('shot')
            if game.score > old_score or game.lives < old_lives:
                sounds.play('hit')
            sounds.motor(bool(controls.throttle or controls.turn), game.state == 'playing' and not paused)
            frame = renderer.draw(game, paused)
            # Letterbox rather than stretch, preserving perspective and circles.
            width, height = window.get_size()
            scale = min(width / 1000, height / 750)
            size = (max(1, round(1000*scale)), max(1, round(750*scale)))
            window.fill(BLACK)
            window.blit(pygame.transform.smoothscale(frame, size), ((width-size[0])//2, (height-size[1])//2))
            pygame.display.flip()
            frames += 1
            if args.frames and frames >= args.frames:
                running = False
    finally:
        pygame.quit()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
