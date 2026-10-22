"""Day 04: a pygame interface for the independently testable maze algorithms.

Run python main.py. Try --seed 42 for a reproducible initial maze, or
--frames 5 for a short unattended run (set SDL_VIDEODRIVER=dummy for no window).
"""
import argparse
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from maze import MazeGame

WIDTH, HEIGHT = 720, 820
MAZE_SIZE = 600
MAZE_X, MAZE_Y = 60, 140
BACKGROUND = (12, 17, 23)
FLOOR = (22, 32, 43)
WALL = (166, 184, 201)
TEXT = (237, 244, 250)
MUTED = (166, 184, 201)
MINT = (141, 240, 187)
GOLD = (255, 206, 117)
TRAIL = (65, 91, 108)

# A dictionary removes repetitive if/elif branches. Both key layouts map to
# the same model vocabulary; the model itself knows nothing about pygame keys.
MOVE_KEYS = {
    pygame.K_UP: "up", pygame.K_w: "up",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
    pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left",
}


def draw_text(screen, font, text, position, color=TEXT, centered=False):
    """Render text to pixels, then blit (copy) those pixels onto the screen."""
    image = font.render(text, True, color)
    rect = image.get_rect()
    if centered:
        rect.center = position
    else:
        rect.topleft = position
    screen.blit(image, rect)


def cell_center(cell, cell_width, cell_height):
    """The model uses (row, column); the screen uses horizontal x, vertical y."""
    row, col = cell
    return (round(MAZE_X + (col + 0.5) * cell_width),
            round(MAZE_Y + (row + 0.5) * cell_height))


def draw_game(screen, game, fonts):
    """Derive a frame from the model. Drawing never changes maze or player state.

    A passage means the shared wall is ABSENT. Draw top/left boundaries once,
    then each cell's right/bottom walls: this avoids drawing shared walls twice.
    Cell dimensions are computed so custom model sizes still fit the board.
    """
    small, normal, large = fonts
    maze = game.maze
    cell_width = MAZE_SIZE / maze.cols
    cell_height = MAZE_SIZE / maze.rows
    screen.fill(BACKGROUND)
    draw_text(screen, small, "20 DAYS OF AI CODING / DAY 04", (MAZE_X, 25), MINT)
    draw_text(screen, large, "Maze Explorer", (MAZE_X, 48))
    status = "Escaped! R: try again · N: new maze" if game.won else "Find the gold exit in the bottom-right corner."
    draw_text(screen, small, status, (MAZE_X, 100), GOLD if game.won else MUTED)
    pygame.draw.rect(screen, FLOOR, (MAZE_X, MAZE_Y, MAZE_SIZE, MAZE_SIZE))

    # Visited markers record exploration, not just the current shortest path.
    for cell in game.visited:
        pygame.draw.circle(screen, TRAIL, cell_center(cell, cell_width, cell_height),
                           max(1, round(min(cell_width, cell_height) * 0.09)))
    if game.show_solution:
        # The solution property starts at the CURRENT position. Computing it
        # only while visible keeps the ordinary drawing path inexpensive.
        path = [cell_center(cell, cell_width, cell_height) for cell in game.solution]
        if len(path) > 1:
            pygame.draw.lines(screen, GOLD, False, path, 3)
    start_center = cell_center(maze.start, cell_width, cell_height)
    goal_center = cell_center(maze.goal, cell_width, cell_height)
    marker = max(3, round(min(cell_width, cell_height) * 0.23))
    pygame.draw.circle(screen, MINT, start_center, marker, width=2)
    # Goal is square, player is round: information isn't conveyed by colour alone.
    pygame.draw.rect(screen, GOLD, (goal_center[0] - marker, goal_center[1] - marker,
                                    marker * 2, marker * 2), width=2)

    pygame.draw.line(screen, WALL, (MAZE_X, MAZE_Y), (MAZE_X + MAZE_SIZE, MAZE_Y), 2)
    pygame.draw.line(screen, WALL, (MAZE_X, MAZE_Y), (MAZE_X, MAZE_Y + MAZE_SIZE), 2)
    for row in range(maze.rows):
        for col in range(maze.cols):
            cell = (row, col)
            x0 = round(MAZE_X + col * cell_width)
            y0 = round(MAZE_Y + row * cell_height)
            x1 = round(MAZE_X + (col + 1) * cell_width)
            y1 = round(MAZE_Y + (row + 1) * cell_height)
            if (row, col + 1) not in maze.passages[cell]:
                pygame.draw.line(screen, WALL, (x1, y0), (x1, y1), 2)
            if (row + 1, col) not in maze.passages[cell]:
                pygame.draw.line(screen, WALL, (x0, y1), (x1, y1), 2)
    pygame.draw.circle(screen, MINT, cell_center(game.position, cell_width, cell_height), marker)
    hint = "on" if game.show_solution else "off"
    draw_text(screen, normal, f"Moves {game.moves}    Explored {len(game.visited)}/{maze.rows * maze.cols}    Hint {hint}", (MAZE_X, 754))
    draw_text(screen, small, "Arrows / WASD: move   H: hint   R: restart   N: new   Esc: quit", (MAZE_X, 788), MUTED)


def handle_event(event, game):
    """Return False to quit; otherwise translate one event into one action."""
    if event.type == pygame.QUIT:
        return False
    if event.type != pygame.KEYDOWN:
        return True
    if event.key == pygame.K_ESCAPE:
        return False
    if event.key in MOVE_KEYS:
        game.move(MOVE_KEYS[event.key])
    elif event.key == pygame.K_h:
        game.show_solution = not game.show_solution
    elif event.key == pygame.K_r:
        game.restart()
    elif event.key == pygame.K_n:
        game.new_maze()
    return True


def run(seed=None, max_frames=None):
    """One event loop: read input → update via handlers → draw → present.

    Movement is discrete, not velocity-based: no delta-time physics is needed.
    tick(60) simply avoids burning CPU redrawing faster than necessary.
    """
    pygame.display.init()
    pygame.font.init()
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Day 04 · Maze Explorer | 20 Days of AI Coding")
        pygame.key.set_repeat()  # Disable repeat: one movement per key-down.
        fonts = tuple(pygame.font.Font(None, size) for size in (20, 25, 46))
        game = MazeGame(seed=seed)
        clock = pygame.time.Clock()
        frames = 0
        running = True
        while running:
            clock.tick(60)
            for event in pygame.event.get():
                if not handle_event(event, game):
                    running = False
                    break
            if not running:
                break
            draw_game(screen, game, fonts)
            pygame.display.flip()
            frames += 1
            if max_frames is not None and frames >= max_frames:
                break
    finally:
        # Release window/font resources even when an exception interrupts a frame.
        pygame.quit()


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


if __name__ == "__main__":
    # The guard lets tests import drawing helpers without launching a window.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, help="reproduce the initial maze")
    parser.add_argument("--frames", type=positive_int, help="quit after N rendered frames")
    args = parser.parse_args()
    run(seed=args.seed, max_frames=args.frames)
