"""Day 02: a pygame window around the independently testable Breakout model.

Run ``python main.py`` from this folder after installing requirements.txt.
The model in game.py owns the rules; this file owns input, timing and drawing.
No images, music, network connections or external fonts are required.
"""

import argparse
import os

# Hide pygame's startup banner, not errors. Set this before importing pygame.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game import Game, HEIGHT, WIDTH

BACKGROUND = (12, 17, 23)
PANEL = (22, 32, 43)
TEXT = (237, 244, 250)
MUTED = (166, 184, 201)
MINT = (141, 240, 187)
BRICK_COLORS = [(255, 137, 144), (255, 185, 113), (255, 220, 126), (141, 240, 187), (135, 192, 255)]


def draw_text(surface, font, text, position, color=TEXT, centered=False):
    """Render text once, then copy (blit) its pixels onto our drawing surface."""
    image = font.render(text, True, color)
    rect = image.get_rect()
    if centered:
        rect.center = position
    else:
        rect.topleft = position
    surface.blit(image, rect)


def draw_game(screen, game, fonts, paused=False):
    """Draw a complete frame from game state. Drawing never changes the model."""
    small, normal, large = fonts
    screen.fill(BACKGROUND)
    pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, 67))
    draw_text(screen, small, "DAY 02 / BREAKOUT", (24, 12), MINT)
    draw_text(screen, normal, "Score {:03d}".format(game.score), (24, 32))
    draw_text(screen, normal, "Lives {}".format(game.lives), (WIDTH - 115, 32))

    for brick in game.bricks:
        # Row colour comes from its position, so it doesn't change after removal.
        row = max(0, min(4, int((brick.y - 90) // 28)))
        pygame.draw.rect(screen, BRICK_COLORS[row], pygame.Rect(round(brick.x), round(brick.y), round(brick.width), round(brick.height)), border_radius=4)
    for body, color in ((game.paddle, MINT), (game.ball, TEXT)):
        # The model uses floats for smooth movement; only drawing rounds pixels.
        rect = pygame.Rect(round(body.x), round(body.y), round(body.width), round(body.height))
        pygame.draw.rect(screen, color, rect, border_radius=4)

    draw_text(screen, small, "A/D or arrows: move   Space: launch   P: pause   R: restart   Esc: quit", (WIDTH // 2, HEIGHT - 17), MUTED, centered=True)

    if paused or game.state in ("ready", "won", "game_over"):
        # A translucent panel makes prompts readable without hiding the board.
        overlay = pygame.Surface((WIDTH, 150), pygame.SRCALPHA)
        overlay.fill((12, 17, 23, 225))
        screen.blit(overlay, (0, 270))
        if paused:
            title, subtitle = "Paused", "Press P to continue"
        elif game.state == "ready":
            title, subtitle = "Ready to bounce?", "Move your paddle, then press Space to launch"
        elif game.state == "won":
            title, subtitle = "Wall cleared!", "You scored {} points. Press R to play again".format(game.score)
        else:
            title, subtitle = "Game over", "You scored {} points. Press R to try again".format(game.score)
        draw_text(screen, large, title, (WIDTH // 2, 320), MINT, centered=True)
        draw_text(screen, normal, subtitle, (WIDTH // 2, 370), centered=True)


def run(max_frames=None):
    """Run until quit. An optional frame limit supports unattended smoke tests.

    clock.tick caps rendering around 60 FPS and returns elapsed milliseconds.
    Dividing by 1000 converts to the seconds expected by Game.update().
    """
    # We don't use audio. Initialising only these modules avoids audio-device
    # errors on machines without speakers (and in headless CI).
    pygame.display.init()
    pygame.font.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Day 02 · Breakout | 20 Days of AI Coding")
        fonts = (pygame.font.Font(None, 20), pygame.font.Font(None, 26), pygame.font.Font(None, 52))
        clock = pygame.time.Clock()
        game = Game()
        running = True
        paused = False
        frames = 0
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        game.reset()
                        paused = False
                    elif event.key == pygame.K_p and game.state == "playing":
                        paused = not paused
                    elif event.key == pygame.K_SPACE and not paused:
                        game.launch()
                elif event.type == pygame.WINDOWFOCUSLOST and game.state == "playing":
                    # Switching apps shouldn't quietly cost a life.
                    paused = True
            if not running:
                break
            keys = pygame.key.get_pressed()
            # Booleans become 0/1: opposing keys cancel rather than favouring one.
            direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
            if not paused:
                game.update(dt, direction)
            draw_game(screen, game, fonts, paused)
            pygame.display.flip()
            frames += 1
            if max_frames is not None and frames >= max_frames:
                running = False
    finally:
        # Always release the window, including if drawing raises an exception.
        pygame.quit()


def positive_int(value):
    """argparse helper: a frame limit must be a positive whole number."""
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=positive_int, help="quit after N frames (smoke tests)")
    args = parser.parse_args()
    run(args.frames)
