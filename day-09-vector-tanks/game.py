"""
Pure Python 3.9+ Battlezone-inspired wireframe tank game model.
No pygame imports. Deterministic, seeded RNG. Novice-friendly comments.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import math
import random


# ============================================================================
# CONSTANTS - Configure game behavior
# ============================================================================

# World boundaries (solid square arena; there is no wrapping)
WORLD_RADIUS = 100.0

# Player movement and turning
PLAYER_FORWARD_SPEED = 12.0      # units per second moving forward
PLAYER_REVERSE_SPEED = 8.0       # units per second moving backward
PLAYER_YAW_SPEED = 1.5           # radians per second turning
PLAYER_RADIUS = 1.2              # collision radius

# Enemy configuration
ENEMY_RADIUS = 1.4
ENEMY_MAX_COUNT = 3
ENEMY_FORWARD_SPEED = 10.0
ENEMY_YAW_SPEED = 1.2
ENEMY_FIRE_COOLDOWN = 1.5        # seconds between shots

# Shell (projectile) configuration
SHELL_SPEED = 35.0               # units per second
SHELL_TTL = 3.0                  # time to live in seconds
PLAYER_FIRE_COOLDOWN = 0.5       # seconds between player shots
SHELL_RADIUS = 0.3               # collision radius for swept segment

# Player state
INITIAL_LIVES = 3
INVULNERABILITY_DURATION = 2.5   # grace period after hit
MAX_PHYSICS_STEP = 1.0 / 60.0    # largest permitted substep (60 Hz)

# Enemy scoring
TANK_SCORE = 1000
SUPERTANK_SCORE = 3000
SAUCER_SCORE = 5000

# Physics substeps
MAX_FRAME_DT = 0.1


# ============================================================================
# DATACLASSES - Data structures for game entities
# ============================================================================

@dataclass(frozen=True)
class Obstacle:
    """Static cover: box/pyramid square footprint, or cylinder circle."""
    x: float                    # center x coordinate
    z: float                    # center z coordinate (forward is +z)
    size: float                 # radius for circle, half-width for box
    height: float               # vertical extent (not used for collision)
    kind: str = 'box'           # 'box', 'pyramid', or 'circle'

    def collides_segment(self, x1: float, z1: float, x2: float, z2: float,
                         radius: float) -> Optional[float]:
        """
        Check if line segment from (x1,z1) to (x2,z2) with radius collides.
        Returns normalized t (0..1) of earliest collision, or None.
        """
        if self.kind == 'circle':
            return segment_circle_t(x1, z1, x2, z2, self.x, self.z,
                                    self.size + radius)
        else:  # 'box'
            return segment_box_t(x1, z1, x2, z2, self.x, self.z,
                                 self.size + radius)


@dataclass(frozen=True)
class Controls:
    """Input from player each frame."""
    throttle: float = 0.0       # -1.0 (reverse) to 1.0 (forward)
    turn: float = 0.0           # -1.0 (left) to 1.0 (right)
    fire: bool = False          # True to request fire


@dataclass
class Enemy:
    """Mobile adversary."""
    x: float
    z: float
    heading: float              # radians; 0 = +z, positive = clockwise (right)
    kind: str = 'tank'          # 'tank', 'supertank', 'saucer'
    cooldown: float = 0.0       # seconds until next shot available
    vx: float = 0.0             # velocity x
    vz: float = 0.0             # velocity z


@dataclass
class Shell:
    """Projectile (player or enemy)."""
    x: float
    z: float
    vx: float                   # velocity x
    vz: float                   # velocity z
    owner: str                  # 'player' or 'enemy'
    ttl: float = SHELL_TTL      # time remaining before expiry


@dataclass
class Explosion:
    """Visual effect marker (optional)."""
    x: float
    z: float
    ttl: float = 0.5


# ============================================================================
# HELPER FUNCTIONS - Math and geometry
# ============================================================================

def wrap_angle(angle: float) -> float:
    """Normalize angle to [-π, π]."""
    if not math.isfinite(angle):
        raise ValueError("angle must be finite")
    wrapped = (angle + math.pi) % math.tau - math.pi
    return math.pi if wrapped == -math.pi and angle > 0 else wrapped


def segment_circle_t(x1: float, z1: float, x2: float, z2: float,
                     cx: float, cz: float, r: float) -> Optional[float]:
    """
    Ray-circle collision. Segment from (x1,z1) to (x2,z2) vs circle at (cx,cz) radius r.
    Returns earliest normalized t in [0,1], or None if no collision.
    Uses quadratic formula on closest point.
    """
    dx = x2 - x1
    dz = z2 - z1
    fx = x1 - cx
    fz = z1 - cz

    # Quadratic: |p(t)|² = r²  where p(t) = (x1,z1) + t*(dx,dz)
    a = dx * dx + dz * dz
    b = 2.0 * (fx * dx + fz * dz)
    c = fx * fx + fz * fz - r * r

    if c <= 0:
        return 0.0  # Already inside, even for a stationary segment.
    if a < 1e-12:
        return None

    discriminant = b * b - 4.0 * a * c
    if discriminant < 0.0:
        return None

    sqrt_disc = math.sqrt(discriminant)
    t1 = (-b - sqrt_disc) / (2.0 * a) if a > 1e-6 else None
    t2 = (-b + sqrt_disc) / (2.0 * a) if a > 1e-6 else None

    # Find earliest t in [0, 1]
    if t1 is not None and 0.0 <= t1 <= 1.0:
        return t1
    if t2 is not None and 0.0 <= t2 <= 1.0:
        return t2
    return None


def segment_box_t(x1: float, z1: float, x2: float, z2: float,
                  bx: float, bz: float, half_width: float) -> Optional[float]:
    """
    Segment vs axis-aligned box collision. Box centered at (bx, bz) with half_width.
    Returns earliest normalized t in [0,1], or None if no collision.
    """
    dx = x2 - x1
    dz = z2 - z1

    # Box bounds
    box_x_min = bx - half_width
    box_x_max = bx + half_width
    box_z_min = bz - half_width
    box_z_max = bz + half_width

    # Slab intersection times
    t_min = 0.0
    t_max = 1.0

    # X axis
    if abs(dx) > 1e-6:
        t_x_min = (box_x_min - x1) / dx
        t_x_max = (box_x_max - x1) / dx
        if t_x_min > t_x_max:
            t_x_min, t_x_max = t_x_max, t_x_min
        t_min = max(t_min, t_x_min)
        t_max = min(t_max, t_x_max)
    else:
        if x1 < box_x_min or x1 > box_x_max:
            return None

    # Z axis
    if abs(dz) > 1e-6:
        t_z_min = (box_z_min - z1) / dz
        t_z_max = (box_z_max - z1) / dz
        if t_z_min > t_z_max:
            t_z_min, t_z_max = t_z_max, t_z_min
        t_min = max(t_min, t_z_min)
        t_max = min(t_max, t_z_max)
    else:
        if z1 < box_z_min or z1 > box_z_max:
            return None

    # Collision if slabs overlap
    if t_min <= t_max and t_max >= 0.0 and t_min <= 1.0:
        return max(0.0, t_min)
    return None


def distance(x1: float, z1: float, x2: float, z2: float) -> float:
    """Euclidean distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (z2 - z1) ** 2)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


# ============================================================================
# GAME CLASS - Main game state and logic
# ============================================================================

class Game:
    """
    Core game model. No pygame. Deterministic with seed.
    Tracks player position/heading, enemies, shells, obstacles, score.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize game with optional seed for deterministic RNG."""
        self.seed = seed
        self.rng = random.Random(seed)

        # Player state
        self.x: float = 0.0
        self.z: float = 0.0
        self.heading: float = 0.0      # radians; 0 = +z direction
        self.vx: float = 0.0
        self.vz: float = 0.0

        # World state
        self.obstacles: List[Obstacle] = []
        self.enemies: List[Enemy] = []
        self.shells: List[Shell] = []
        self.explosions: List[Explosion] = []

        # Gameplay state
        self.score: int = 0
        self.lives: int = INITIAL_LIVES
        self.state: str = 'title'          # 'title', 'playing', 'game_over'
        self.kills: int = 0

        # Cooldowns and timers
        self.cooldown: float = 0.0         # player fire cooldown
        self.invulnerable: float = 0.0     # invulnerability timer
        self.elapsed: float = 0.0          # total elapsed time

        # Message for renderer
        self.message: str = ""

        self.start()

    def start(self) -> None:
        """Reset to initial state with current seed."""
        # Reset RNG with same seed
        self.rng = random.Random(self.seed)

        # Player
        self.x = 0.0
        self.z = 0.0
        self.heading = 0.0
        self.vx = 0.0
        self.vz = 0.0

        # World
        self.obstacles = self._create_obstacles()
        self.enemies = []
        self.shells = []
        self.explosions = []

        # Gameplay
        self.score = 0
        self.lives = INITIAL_LIVES
        self.state = 'playing'
        self.kills = 0

        # Timers
        self.cooldown = 0.0
        self.invulnerable = 0.25           # start with brief invuln
        self.elapsed = 0.0
        self.message = "Vector Tanks"

        # Spawn initial enemies
        self._spawn_enemies()

    def _create_obstacles(self) -> List[Obstacle]:
        """Generate static obstacles, leaving spawn area clear."""
        obstacles = []
        # Create a few simple obstacles
        # Placement avoids origin (player spawn)
        obstacles.append(Obstacle(x=30.0, z=40.0, size=4.0, height=5.0, kind='box'))
        obstacles.append(Obstacle(x=-40.0, z=50.0, size=3.0, height=6.0, kind='circle'))
        obstacles.append(Obstacle(x=50.0, z=-30.0, size=4.0, height=4.0, kind='box'))
        obstacles.append(Obstacle(x=-30.0, z=-50.0, size=3.0, height=5.0, kind='circle'))
        obstacles.append(Obstacle(x=0.0, z=70.0, size=4.0, height=7.0, kind='pyramid'))
        obstacles.extend([Obstacle(-13, 23, 3, 4, 'pyramid'),
                          Obstacle(14, 31, 3, 4),
                          Obstacle(-24, -15, 4, 4)])
        return obstacles

    def _spawn_enemies(self) -> None:
        """Spawn enemies distant from player at game start or when needed."""
        if len(self.enemies) >= ENEMY_MAX_COUNT:
            return
        # Try a bounded number of placements; never spawn inside cover or on
        # the player. Enemies can enter from any direction: use the radar.
        for _ in range(80):
            angle = self.rng.uniform(0, math.tau)
            dist = self.rng.uniform(45, 65)
            ex = self.x + math.sin(angle) * dist
            ez = self.z + math.cos(angle) * dist
            if abs(ex) > WORLD_RADIUS-3 or abs(ez) > WORLD_RADIUS-3:
                continue
            if self._check_collision_path(ex, ez, ex, ez, ENEMY_RADIUS) is not None:
                continue
            if any(distance(ex, ez, e.x, e.z) < 5 for e in self.enemies):
                continue
            kind = self.rng.choices(['tank', 'supertank', 'saucer'],
                                    weights=[max(25, 85-self.kills*3), 10+self.kills*2, 5])[0]
            self.enemies.append(Enemy(ex, ez, math.atan2(self.x-ex, self.z-ez),
                                      kind=kind, cooldown=2.0))
            return

    def update(self, dt: float, controls: Controls) -> None:
        """
        Update game state. Clamps dt to substeps <= 1/60.
        No effect unless state == 'playing'.
        """
        # Validate dt
        if dt < 0 or dt != dt or math.isinf(dt):  # negative, NaN, inf
            raise ValueError(f"Invalid dt: {dt}")

        if self.state != 'playing':
            return

        # Clamp dt and split into substeps
        dt = clamp(dt, 0, MAX_FRAME_DT)
        if dt == 0:
            return

        num_substeps = max(1, int(math.ceil(dt / MAX_PHYSICS_STEP)))
        substep_dt = dt / num_substeps

        for _ in range(num_substeps):
            if self.state != 'playing':
                break
            self._physics_step(substep_dt, controls)

    def _physics_step(self, dt: float, controls: Controls) -> None:
        """Single physics timestep."""
        # Update timers
        self.cooldown = max(0, self.cooldown - dt)
        self.invulnerable = max(0, self.invulnerable - dt)
        self.elapsed += dt

        # Player movement
        self._update_player(dt, controls)

        # Enemy AI
        self._update_enemies(dt)

        # Shell movement and collisions
        self._update_shells(dt)

        # Spawn more enemies if needed (difficulty scaling)
        if len(self.enemies) < ENEMY_MAX_COUNT and self.rng.random() < 0.02:
            self._spawn_enemies()

    def _update_player(self, dt: float, controls: Controls) -> None:
        """Update player position, heading, and fire."""
        # Heading (yaw)
        self.heading += clamp(controls.turn, -1, 1) * PLAYER_YAW_SPEED * dt
        self.heading = wrap_angle(self.heading)

        # Velocity from throttle
        speed = 0.0
        if controls.throttle > 0.01:
            speed = clamp(controls.throttle, -1, 1) * PLAYER_FORWARD_SPEED
        elif controls.throttle < -0.01:
            speed = clamp(controls.throttle, -1, 1) * PLAYER_REVERSE_SPEED

        # Velocity components
        self.vx = math.sin(self.heading) * speed
        self.vz = math.cos(self.heading) * speed

        # Position update (with collision)
        new_x = self.x + self.vx * dt
        new_z = self.z + self.vz * dt

        # Clamp to world
        new_x = clamp(new_x, -WORLD_RADIUS, WORLD_RADIUS)
        new_z = clamp(new_z, -WORLD_RADIUS, WORLD_RADIUS)

        # Check obstacle collision
        collision_t = self._check_collision_path(self.x, self.z, new_x, new_z,
                                                 PLAYER_RADIUS)
        if collision_t is not None:
            # Stop at collision
            new_x = self.x + self.vx * dt * collision_t * 0.95
            new_z = self.z + self.vz * dt * collision_t * 0.95

        self.x = new_x
        self.z = new_z

        # Fire
        if controls.fire and self.cooldown <= 0 and not any(s.owner == 'player' for s in self.shells):
            self._fire_shell()
            self.cooldown = PLAYER_FIRE_COOLDOWN

    def _update_enemies(self, dt: float) -> None:
        """Update enemy positions and AI behavior."""
        for enemy in self.enemies:
            # AI: approach player or standoff, aim and fire
            player_dist = distance(enemy.x, enemy.z, self.x, self.z)

            # Decide action based on distance
            standoff_dist = 25.0
            if player_dist > standoff_dist + 5:
                # Approach
                dx = self.x - enemy.x
                dz = self.z - enemy.z
                target_heading = math.atan2(dx, dz)
                # Turn toward target
                angle_diff = wrap_angle(target_heading - enemy.heading)
                turn = clamp(angle_diff, -1, 1)
                enemy.heading += turn * ENEMY_YAW_SPEED * dt
            elif player_dist < standoff_dist - 5:
                # Retreat
                dx = self.x - enemy.x
                dz = self.z - enemy.z
                target_heading = math.atan2(dx, dz) + math.pi
                angle_diff = wrap_angle(target_heading - enemy.heading)
                turn = clamp(angle_diff, -1, 1)
                enemy.heading += turn * ENEMY_YAW_SPEED * dt
            else:
                # Standoff: aim at player
                dx = self.x - enemy.x
                dz = self.z - enemy.z
                target_heading = math.atan2(dx, dz)
                angle_diff = wrap_angle(target_heading - enemy.heading)
                turn = clamp(angle_diff * 0.5, -1, 1)
                enemy.heading += turn * ENEMY_YAW_SPEED * dt

            enemy.heading = wrap_angle(enemy.heading)

            # Move forward slowly
            speed = (8.5 if enemy.kind == 'supertank' else 5.0) * (1 + min(self.kills, 20) * .015)
            if enemy.kind != 'saucer' and 20 <= player_dist <= 30:
                speed = 0.0
            enemy.vx = math.sin(enemy.heading) * speed
            enemy.vz = math.cos(enemy.heading) * speed

            new_x = enemy.x + enemy.vx * dt
            new_z = enemy.z + enemy.vz * dt

            # Clamp to world
            new_x = clamp(new_x, -WORLD_RADIUS, WORLD_RADIUS)
            new_z = clamp(new_z, -WORLD_RADIUS, WORLD_RADIUS)

            # Obstacle collision
            collision_t = self._check_collision_path(enemy.x, enemy.z, new_x, new_z,
                                                     ENEMY_RADIUS)
            if collision_t is not None:
                new_x = enemy.x + enemy.vx * dt * collision_t * 0.9
                new_z = enemy.z + enemy.vz * dt * collision_t * 0.9

            enemy.x = new_x
            enemy.z = new_z

            # Fire cooldown
            enemy.cooldown = max(0, enemy.cooldown - dt)

            # Fire toward player if aimed
            if enemy.cooldown <= 0 and enemy.kind != 'saucer':
                dx = self.x - enemy.x
                dz = self.z - enemy.z
                angle_to_player = math.atan2(dx, dz)
                angle_diff = abs(wrap_angle(angle_to_player - enemy.heading))

                # Fire if aimed within 15 degrees
                if angle_diff < 0.26:  # ~15 degrees
                    # Check line of sight (no terrain)
                    los_t = self._check_collision_path(enemy.x, enemy.z, self.x, self.z,
                                                       SHELL_RADIUS)
                    if los_t is None:  # Clear line of sight
                        self._fire_shell_from_enemy(enemy)
                        enemy.cooldown = max(.7, ENEMY_FIRE_COOLDOWN - self.kills*.025) + self.rng.uniform(-0.2, 0.2)

    def _update_shells(self, dt: float) -> None:
        """Update shell positions, collisions, and remove expired shells."""
        new_shells = []

        for shell in self.shells:
            # Update TTL
            shell.ttl -= dt
            if shell.ttl <= 0:
                continue

            # Update position
            new_x = shell.x + shell.vx * dt
            new_z = shell.z + shell.vz * dt

            # Pick the EARLIEST impact, not just the first object in a list.
            # Sweeping the whole segment prevents high-speed shells tunnelling.
            impact_t = self._check_collision_path(shell.x, shell.z, new_x, new_z, SHELL_RADIUS)
            victim = None
            if shell.owner == 'player':
                for enemy in self.enemies:
                    t = segment_circle_t(shell.x, shell.z, new_x, new_z,
                                         enemy.x, enemy.z, ENEMY_RADIUS + SHELL_RADIUS)
                    if t is not None and (impact_t is None or t < impact_t):
                        impact_t, victim = t, enemy
            elif shell.owner == 'enemy':
                t = segment_circle_t(shell.x, shell.z, new_x, new_z,
                                     self.x, self.z, PLAYER_RADIUS + SHELL_RADIUS)
                if t is not None and (impact_t is None or t < impact_t):
                    impact_t, victim = t, 'player'
            if impact_t is not None:
                hit_x = shell.x + (new_x-shell.x)*impact_t
                hit_z = shell.z + (new_z-shell.z)*impact_t
                self.explosions.append(Explosion(hit_x, hit_z))
                if victim == 'player' and self.invulnerable <= 0:
                    self._handle_player_hit()
                elif isinstance(victim, Enemy):
                    self._handle_enemy_hit(self.enemies.index(victim))
                continue
            shell.x, shell.z = new_x, new_z
            new_shells.append(shell)

        self.shells = new_shells
        
        # Clean up expired explosions
        expired_explosions = []
        for e in self.explosions:
            e.ttl -= dt
            if e.ttl > 0:
                expired_explosions.append(e)
        self.explosions = expired_explosions

    def _check_collision_path(self, x1: float, z1: float, x2: float, z2: float,
                              radius: float) -> Optional[float]:
        """
        Check if swept segment (x1,z1)->(x2,z2) with radius collides with obstacles.
        Returns earliest normalized t in [0,1], or None.
        """
        earliest_t = None

        for obs in self.obstacles:
            t = obs.collides_segment(x1, z1, x2, z2, radius)
            if t is not None and (earliest_t is None or t < earliest_t):
                earliest_t = t

        return earliest_t

    def _fire_shell(self) -> None:
        """Fire a shell from player."""
        vx = math.sin(self.heading) * SHELL_SPEED
        vz = math.cos(self.heading) * SHELL_SPEED
        shell = Shell(
            x=self.x + math.sin(self.heading) * PLAYER_RADIUS,
            z=self.z + math.cos(self.heading) * PLAYER_RADIUS,
            vx=vx,
            vz=vz,
            owner='player',
            ttl=SHELL_TTL
        )
        self.shells.append(shell)

    def _fire_shell_from_enemy(self, enemy: Enemy) -> None:
        """Fire a shell from an enemy."""
        vx = math.sin(enemy.heading) * SHELL_SPEED
        vz = math.cos(enemy.heading) * SHELL_SPEED
        shell = Shell(
            x=enemy.x + math.sin(enemy.heading) * ENEMY_RADIUS,
            z=enemy.z + math.cos(enemy.heading) * ENEMY_RADIUS,
            vx=vx,
            vz=vz,
            owner='enemy',
            ttl=SHELL_TTL
        )
        self.shells.append(shell)

    def _handle_enemy_hit(self, enemy_index: int) -> None:
        """Remove enemy, award points, play explosion."""
        enemy = self.enemies[enemy_index]
        if enemy.kind == 'tank':
            points = TANK_SCORE
        elif enemy.kind == 'supertank':
            points = SUPERTANK_SCORE
        else:  # saucer
            points = SAUCER_SCORE

        self.score += points
        self.kills += 1
        self.enemies.pop(enemy_index)
        self.message = f"Hit! +{points}"

    def _handle_player_hit(self) -> None:
        """Damage player: lose life, become invulnerable, respawn."""
        self.lives -= 1
        self.invulnerable = INVULNERABILITY_DURATION

        if self.lives <= 0:
            self.state = 'game_over'
            self.message = f"Game Over! Final Score: {self.score}"
        else:
            # Respawn at safe position
            self.x = 0.0
            self.z = 0.0
            self.vx = 0
            self.vz = 0
            self.message = f"Hit! {self.lives} lives left"


# ============================================================================
# MODULE API
# ============================================================================

__all__ = [
    'Game',
    'Controls',
    'Enemy',
    'Shell',
    'Obstacle',
    'Explosion',
    'WORLD_RADIUS',
    'PLAYER_RADIUS',
    'ENEMY_RADIUS',
    'SHELL_TTL',
    'INVULNERABILITY_DURATION',
    'wrap_angle',
    'distance',
]
