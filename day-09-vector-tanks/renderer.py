"""Original wireframe art and a tiny 3D engine, written for this project.

Coordinates: x = right, y = up, z = forward. The game simulates x/z only;
this file supplies height. There are no Atari models, ROMs or image assets.
"""
import math
import pygame

GREEN = (105, 255, 135)
DIM = (29, 113, 61)
BRIGHT = (194, 255, 200)
RED = (255, 103, 82)
BLACK = (2, 10, 6)


def camera_point(point, x, z, heading):
    """Subtract camera position, then undo its yaw (a 2D rotation in x/z)."""
    dx, y, dz = point[0] - x, point[1] - 1.55, point[2] - z
    c, s = math.cos(heading), math.sin(heading)
    return dx * c - dz * s, y, dx * s + dz * c


def project_segment(a, b, width=1000, horizon=360, focal=620, near=0.35):
    """Clip a camera-space line before perspective division.

    A point behind the eye has negative depth. Dividing by that depth makes
    lines flip across the screen; clipping against a small near plane prevents
    that. Return None only when BOTH endpoints are behind that plane.
    """
    if a[2] < near and b[2] < near:
        return None
    if a[2] < near or b[2] < near:
        t = (near - a[2]) / (b[2] - a[2])
        cut = tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
        if a[2] < near:
            a = cut
        else:
            b = cut
    return tuple((width / 2 + p[0] * focal / p[2],
                  horizon - p[1] * focal / p[2]) for p in (a, b))


def box(x, y, z):
    """Eight corners and twelve edges; x/z are half-widths, y is full height."""
    points = [(sx * x, yy, sz * z) for yy in (0, y) for sz in (-1, 1) for sx in (-1, 1)]
    edges = [(0, 1), (1, 3), (3, 2), (2, 0), (4, 5), (5, 7), (7, 6), (6, 4),
             (0, 4), (1, 5), (2, 6), (3, 7)]
    return points, edges


def tank_mesh(super_tank=False):
    """Build recognisable tracks, hull, turret and a forward-facing gun."""
    points, edges = [], []
    parts = [(-1.05, 0, 0, .35, .65, 1.65), (1.05, 0, 0, .35, .65, 1.65),
             (0, .35, 0, 1.05, .8, 1.35), (0, 1.15, -.15, .65, .65, .75),
             (0, 1.55, 1.3, .12, .16, 1.05)]
    for px, py, pz, sx, sy, sz in parts:
        vertices, lines = box(sx, sy, sz)
        base = len(points)
        points.extend((x + px, y + py, z + pz) for x, y, z in vertices)
        edges.extend((a + base, b + base) for a, b in lines)
    if super_tank:
        # A raised command mast distinguishes the faster, higher-value tank.
        base = len(points)
        points.extend([(0, 1.8, -.2), (0, 3, -.2), (.55, 2.65, -.2)])
        edges.extend([(base, base + 1), (base + 1, base + 2)])
    return points, edges


def saucer_mesh():
    """Two polygon rings and a low canopy. This bonus target does not shoot."""
    points = [(math.sin(i * math.tau / 12) * radius, y,
               math.cos(i * math.tau / 12) * radius)
              for radius, y in ((2.2, 1), (.9, 1.8)) for i in range(12)]
    edges = [(i, (i + 1) % 12) for i in range(12)]
    edges += [(12 + i, 12 + (i + 1) % 12) for i in range(12)]
    edges += [(i, i + 12) for i in range(12)]
    return points, edges


class Renderer:
    """Draw at one logical resolution; main.py scales it to the real window."""
    def __init__(self):
        self.surface = pygame.Surface((1000, 750))
        # Pygame's bundled default font avoids depending on installed fonts.
        self.font = pygame.font.Font(None, 27)
        self.small = pygame.font.Font(None, 21)
        self.large = pygame.font.Font(None, 72)
        self.tanks = {False: tank_mesh(), True: tank_mesh(True)}
        self.saucer = saucer_mesh()
        self.viewport = pygame.Rect(20, 190, 960, 490)

    def text(self, text, pos, color=GREEN, center=False, large=False, small=False):
        font = self.large if large else self.small if small else self.font
        image = font.render(text, True, color)
        self.surface.blit(image, image.get_rect(center=pos) if center else pos)

    def mesh(self, mesh, x, z, heading, game, color=GREEN):
        points, edges = mesh
        c, s = math.cos(heading), math.sin(heading)
        view = [camera_point((x + px * c + pz * s, py, z - px * s + pz * c),
                             game.x, game.z, game.heading) for px, py, pz in points]
        for a, b in edges:
            segment = project_segment(view[a], view[b])
            if segment:
                # Clip in screen space too, preventing huge near-plane lines.
                clipped = self.viewport.clipline(segment[0], segment[1])
                if clipped:
                    pygame.draw.aaline(self.surface, color, *clipped)

    def landscape(self, game):
        # A panoramic, repeating mountain silhouette rotates with your heading.
        # It stays at infinity: turning shifts it, translation does not.
        for i in range(-18, 19):
            angle = i * .23
            delta = (angle - game.heading + math.pi) % math.tau - math.pi
            if abs(delta) > 1.05:
                continue
            x = 500 + math.tan(delta) * 620
            height = 25 + (i * i * 13 % 57)
            pygame.draw.lines(self.surface, DIM, False, [(x - 85, 360), (x, 360 - height), (x + 85, 360)])
        pygame.draw.line(self.surface, DIM, (20, 360), (980, 360))
        # A volcano-shaped distant landmark is original vector scenery.
        delta = (.7 - game.heading + math.pi) % math.tau - math.pi
        if abs(delta) < 1:
            x = 500 + math.tan(delta) * 620
            pygame.draw.lines(self.surface, GREEN, False, [(x-85,360),(x-22,285),(x-10,294),(x+9,285),(x+80,360)])

    def radar(self, game):
        center, radius = (500, 99), 68
        pygame.draw.circle(self.surface, DIM, center, radius, 1)
        pygame.draw.line(self.surface, DIM, (432,99), (568,99))
        pygame.draw.line(self.surface, DIM, (500,31), (500,167))
        # The fan indicates the forward camera's field of view; blips rotate
        # relative to the player, not world north. One world unit is 0.65 pixels.
        for sign in (-1, 1):
            pygame.draw.line(self.surface, DIM, center, (500 + sign * 47, 51))
        angle = game.elapsed * 2
        pygame.draw.line(self.surface, GREEN, center,
                         (500 + math.sin(angle)*radius, 99 - math.cos(angle)*radius))
        pygame.draw.polygon(self.surface, BRIGHT, [(500,94),(496,103),(504,103)], 1)
        for enemy in game.enemies:
            dx, _, dz = camera_point((enemy.x, 2.5, enemy.z), game.x, game.z, game.heading)
            if math.hypot(dx, dz) < 100:
                color = BRIGHT if enemy.kind == 'saucer' else GREEN
                pygame.draw.circle(self.surface, color, (round(500+dx*.65),round(99-dz*.65)), 3, 1)
        self.text("RADAR", (500, 177), small=True, center=True)

    def draw(self, game, paused=False):
        self.surface.fill(BLACK)
        self.text("VECTOR TANKS", (28, 24))
        self.text(f"SCORE  {game.score:07d}", (28, 62), RED)
        self.text(f"TANKS  {game.lives}", (28, 98), RED)
        self.text("DAY 09 / ORIGINAL TRIBUTE", (700, 25), small=True)
        self.text("SPACE: FIRE     P: PAUSE", (700, 62), small=True)
        self.text("R: RESTART     H: HELP", (700, 92), small=True)
        self.radar(game)
        self.surface.set_clip(self.viewport)
        self.landscape(game)
        for obstacle in game.obstacles:
            if obstacle.kind == 'pyramid':
                r = obstacle.size
                mesh = ([(-r,0,-r),(r,0,-r),(r,0,r),(-r,0,r),(0,obstacle.height,0)],
                        [(0,1),(1,2),(2,3),(3,0),(0,4),(1,4),(2,4),(3,4)])
            elif obstacle.kind == 'circle':
                # Physical footprint is circular; visible mesh is a cylinder.
                points = [(math.sin(i*math.tau/10)*obstacle.size,y,math.cos(i*math.tau/10)*obstacle.size)
                          for y in (0,obstacle.height) for i in range(10)]
                edges = [(i,(i+1)%10) for i in range(10)] + [(10+i,10+(i+1)%10) for i in range(10)] + [(i,i+10) for i in range(10)]
                mesh = points, edges
            else:
                mesh = box(obstacle.size, obstacle.height, obstacle.size)
            self.mesh(mesh, obstacle.x, obstacle.z, 0, game, DIM)
        for enemy in game.enemies:
            mesh = self.saucer if enemy.kind == 'saucer' else self.tanks[enemy.kind == 'supertank']
            self.mesh(mesh, enemy.x, enemy.z, enemy.heading, game)
        for shell in game.shells:
            # A short luminous segment makes a shell's flight readable.
            point = (shell.x, 1.55, shell.z)
            tail = (shell.x - shell.vx*.07, 1.55, shell.z - shell.vz*.07)
            a = camera_point(point,game.x,game.z,game.heading)
            b = camera_point(tail,game.x,game.z,game.heading)
            segment = project_segment(a,b)
            if segment:
                clipped = self.viewport.clipline(*segment)
                if clipped:
                    pygame.draw.line(self.surface, BRIGHT if shell.owner=='player' else RED, *clipped, 2)
        for explosion in game.explosions:
            # Expanding spokes are procedural effects, not sprite sheets.
            for i in range(8):
                a = i*math.tau/8
                r = (0.6 - explosion.ttl)*9
                mesh = ([(0,1,0),(math.sin(a)*r,1+math.cos(a)*r,0)],[(0,1)])
                self.mesh(mesh,explosion.x,explosion.z,0,game,BRIGHT)
        # Reticle has a gap so distant targets remain visible at its centre.
        for side in (-1,1):
            pygame.draw.line(self.surface,GREEN,(500+side*9,360),(500+side*45,360))
            pygame.draw.line(self.surface,GREEN,(500,360+side*9),(500,360+side*25))
        if game.invulnerable > 0 and game.elapsed % .4 < .2:
            self.text("SHIELDS RECOVERING",(500,625),center=True)
        if game.invulnerable > 2.05:
            # Brief broken-viewfinder lines signal an actual hit.
            pygame.draw.lines(self.surface, RED, False, [(200,190),(470,350),(440,410),(560,480),(610,680)],2)
            pygame.draw.lines(self.surface, RED, False, [(980,240),(550,380),(700,570)],2)
        self.surface.set_clip(None)
        pygame.draw.rect(self.surface, GREEN, self.viewport, 1)
        target = "SCAN RADAR / TURN TO FIND ENEMY"
        for enemy in game.enemies:
            dx, _, dz = camera_point((enemy.x,2.5,enemy.z),game.x,game.z,game.heading)
            if dz > 0 and abs(math.atan2(dx,dz)) < .055:
                blocked = game._check_collision_path(game.x,game.z,enemy.x,enemy.z,0.3)
                target = "TARGET OBSCURED" if blocked is not None else "ENEMY IN SIGHTS / FIRE"
                break
        self.text(target,(500,705),center=True)
        self.text("ARROWS / WASD: DRIVE   |   T,G: LEFT TRACK   U,J: RIGHT TRACK",(500,735),center=True,small=True)
        if paused:
            self.overlay("PAUSED", ["P or Enter to resume", "Arrows / WASD drive; SPACE fires.", "Dual tracks: T/G left forward/reverse, U/J right.", "Use cover. One player shell at a time.", "Focus lost? Click the window, then resume."])
        elif game.state != 'playing':
            heading = "VECTOR TANKS" if game.state == 'title' else "GAME OVER"
            self.overlay(heading, ["A wireframe tank-combat tribute to Battlezone (1980)",
                "Arrow keys / WASD drive and steer. SPACE fires.",
                "Dual tracks: T/G left forward/reverse, U/J right.",
                "One shell at a time. Lead moving targets; use cover.",
                "Tank 1000 / Supertank 3000 / Saucer 5000",
                "ENTER to deploy   |   ESC to quit"])
        return self.surface

    def overlay(self, title, lines):
        veil = pygame.Surface((920, 335), pygame.SRCALPHA)
        veil.fill((0, 12, 5, 242))
        self.surface.blit(veil, (40, 270))
        pygame.draw.rect(self.surface, GREEN, (40,270,920,335),1)
        self.text(title,(500,320),center=True,large=True)
        for i, line in enumerate(lines):
            self.text(line,(500,378+i*32),center=True,small=True)
