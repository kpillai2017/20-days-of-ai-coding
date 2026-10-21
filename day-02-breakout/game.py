"""
Breakout game engine - pure Python implementation.
Physics with fixed timesteps, AABB collision detection, and directional resolution.
"""

from dataclasses import dataclass
import math
from typing import List


# Public API constants
WIDTH = 800
HEIGHT = 600

# Gameplay constants
BALL_SPEED = 340  # pixels per second
PADDLE_SPEED = 460  # pixels per second
BALL_SIZE = 12  # width and height of square ball
INITIAL_LIVES = 3
POINTS_PER_BRICK = 10
MAX_FRAME_DT = 0.1  # cap frame delta to avoid jumping through bricks
MAX_PHYSICS_STEP = 1.0 / 240.0  # largest permitted physics substep

# Brick layout constants
BRICK_ROWS = 5
BRICK_COLS = 10
BRICK_WIDTH = 68
BRICK_HEIGHT = 20
BRICK_TOP = 90
BRICK_GAP_X = 8
BRICK_GAP_Y = 8

# Computed brick layout (horizontal centering)
_BRICK_ROW_WIDTH = BRICK_COLS * BRICK_WIDTH + (BRICK_COLS - 1) * BRICK_GAP_X
BRICK_START_X = (WIDTH - _BRICK_ROW_WIDTH) / 2


@dataclass
class Rect:
    """Simple rectangle with floating-point coordinates."""
    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def centerx(self) -> float:
        return self.x + self.width / 2

    @property
    def centery(self) -> float:
        return self.y + self.height / 2

    def intersects(self, other: "Rect") -> bool:
        """Check if this rectangle overlaps with another (AABB test)."""
        return not (self.right <= other.left or self.left >= other.right or
                   self.bottom <= other.top or self.top >= other.bottom)


class Game:
    """Breakout game engine with physics and collision handling."""

    def __init__(self):
        """Initialize game state."""
        # Paddle: centered at bottom, above the play area
        self.paddle = Rect(x=(WIDTH - 110) / 2, y=550, width=110, height=14)

        # Ball: square with side BALL_SIZE
        self.ball = Rect(x=WIDTH / 2 - BALL_SIZE / 2, y=self.paddle.top - BALL_SIZE,
                         width=BALL_SIZE, height=BALL_SIZE)

        # Starting a new instance and pressing R share exactly the same setup.
        # reset() also prepares the ball, velocity and collision history.
        self.reset()

    def _create_bricks(self) -> List[Rect]:
        """Create initial brick layout: 5 rows x 10 columns."""
        bricks = []
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x = BRICK_START_X + col * (BRICK_WIDTH + BRICK_GAP_X)
                y = BRICK_TOP + row * (BRICK_HEIGHT + BRICK_GAP_Y)
                bricks.append(Rect(x=x, y=y, width=BRICK_WIDTH, height=BRICK_HEIGHT))
        return bricks

    def reset(self):
        """Reset entire level: bricks, ball position, ball at rest, ready state."""
        self.score = 0
        self.lives = INITIAL_LIVES
        self.paddle.x = (WIDTH - self.paddle.width) / 2
        self.bricks = self._create_bricks()
        self._prepare_serve()

    def _prepare_serve(self):
        """Reset only the ball. Losing a life must not restore cleared bricks."""
        self.ball.x = self.paddle.centerx - self.ball.width / 2
        self.ball.y = self.paddle.top - self.ball.height
        self.vx = self.vy = 0.0
        self.state = "ready"
        self._prev_ball_x = self.ball.x
        self._prev_ball_y = self.ball.y

    def launch(self):
        """Launch the ball from ready state (ball moves up and right initially)."""
        if self.state == "ready":
            # Launch at BALL_SPEED px/sec target speed, initially up-right
            self.vx = BALL_SPEED * 0.6
            self.vy = -BALL_SPEED * 0.8
            self.state = "playing"

    def update(self, dt: float, direction: float = 0.0):
        """
        Update game state.

        Args:
            dt: Delta time in seconds. Clamped to max 0.1 and must be >= 0.
            direction: -1 for left, +1 for right, 0 for stationary.
        """
        if not math.isfinite(dt) or dt < 0:
            raise ValueError("dt must be a finite non-negative number")
        if not math.isfinite(direction):
            raise ValueError("direction must be finite")
        if dt == 0 or self.state in ("won", "game_over"):
            return

        # Discard long pauses rather than simulating a huge backlog. Splitting
        # each update into tiny slices avoids jumping across thin bricks.
        dt = min(dt, MAX_FRAME_DT)
        direction = max(-1.0, min(1.0, direction))
        steps = math.ceil(dt / MAX_PHYSICS_STEP)
        substep = dt / steps
        for _ in range(steps):
            self.paddle.x = max(0, min(
                self.paddle.x + direction * PADDLE_SPEED * substep,
                WIDTH - self.paddle.width,
            ))
            if self.state == "ready":
                self.ball.x = self.paddle.centerx - self.ball.width / 2
                self.ball.y = self.paddle.top - self.ball.height
            else:
                self._physics_step(substep)
                # A lost life or a win ends this update immediately. Otherwise
                # the remaining slices could move an already-stopped ball.
                if self.state != "playing":
                    break

    def _physics_step(self, dt: float):
        """Execute one physics substep with collision handling."""
        # Save previous position for collision resolution
        self._prev_ball_x = self.ball.x
        self._prev_ball_y = self.ball.y

        # Update ball position
        self.ball.x += self.vx * dt
        self.ball.y += self.vy * dt

        # Wall collisions (reflect once, resolve position)
        if self.ball.left < 0:
            self.ball.x = 0
            self.vx = abs(self.vx)
        elif self.ball.right > WIDTH:
            self.ball.x = WIDTH - self.ball.width
            self.vx = -abs(self.vx)

        if self.ball.top < 0:
            self.ball.y = 0
            self.vy = abs(self.vy)

        # Bottom: check if ball passed entirely below paddle
        if self.ball.top > HEIGHT:
            self.lives -= 1
            if self.lives > 0:
                self._prepare_serve()
            else:
                self.state = "game_over"
                self.lives = 0  # Ensure lives doesn't go negative
            return

        # Paddle collision: only bounce if ball hits top (downward velocity)
        if self._check_paddle_collision():
            self._resolve_paddle_collision()

        # Brick collisions
        self._check_brick_collisions()

        # Check win condition
        if len(self.bricks) == 0:
            self.state = "won"

    def _check_paddle_collision(self) -> bool:
        """Check if ball intersects paddle and is coming from above."""
        # Require crossing the TOP while descending. An overlap alone would
        # wrongly rescue a ball already below the paddle, or bounce it upward
        # when it hits the underside on its way back up.
        return (self.vy > 0
                and self._prev_ball_y + self.ball.height <= self.paddle.top
                and self.ball.intersects(self.paddle))

    def _resolve_paddle_collision(self):
        """Resolve paddle collision with directional bounce and angle."""
        # Clamp ball to top of paddle
        self.ball.y = self.paddle.top - self.ball.height

        # Angle based on hit position: -1 (left) to +1 (right)
        paddle_center = self.paddle.centerx
        hit_offset = (self.ball.centerx - paddle_center) / (self.paddle.width / 2)
        hit_offset = max(-1, min(1, hit_offset))  # Clamp

        # Target speed and angle
        angle_factor = hit_offset * 0.6  # Max 60% horizontal
        self.vx = BALL_SPEED * angle_factor
        # Pythagoras keeps total speed constant: vx² + vy² = speed².
        # With vx limited to 60%, upward speed is always at least 80%.
        self.vy = -math.sqrt(BALL_SPEED * BALL_SPEED - self.vx * self.vx)

    def _check_brick_collisions(self):
        """Check collisions with bricks and resolve with directional response."""
        for brick in self.bricks[:]:  # Iterate over copy to allow removal
            if not self.ball.intersects(brick):
                continue

            # Determine collision side using previous position
            # Check if ball came from top or bottom
            came_from_top = self._prev_ball_y + self.ball.height <= brick.top
            came_from_bottom = self._prev_ball_y >= brick.bottom
            came_from_left = self._prev_ball_x + self.ball.width <= brick.left
            came_from_right = self._prev_ball_x >= brick.right

            # Resolve based on approach direction
            if came_from_top:
                self.ball.y = brick.top - self.ball.height
                self.vy = -abs(self.vy)  # Bounce upward
            elif came_from_bottom:
                self.ball.y = brick.bottom
                self.vy = abs(self.vy)  # Bounce downward
            elif came_from_left:
                self.ball.x = brick.left - self.ball.width
                self.vx = -abs(self.vx)  # Bounce left
            elif came_from_right:
                self.ball.x = brick.right
                self.vx = abs(self.vx)  # Bounce right
            else:
                # Corner hit: default to reversing vertical
                self.vy = -self.vy

            # Remove brick and score (only once per brick per collision)
            self.bricks.remove(brick)
            self.score += POINTS_PER_BRICK
            break  # Process only one brick per substep to avoid double-scoring
