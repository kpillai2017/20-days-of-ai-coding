"""Original low-poly chess sculptures, projected into an isometric scene.

Pygame draws shaded polygons, not imported models or Battle Chess sprites.
World x/y cover the board; z is height. Painter sorting gives a readable 3D
illusion without an external 3D engine, but is not a full depth-buffer renderer.
"""

import math
import pygame
from animation import pose, STYLES

BG = (21, 28, 42)
GOLD = (235, 193, 112)
TEXT = (227, 235, 245)
MUTED = (158, 176, 198)
LIGHT = (174, 183, 176)
DARK = (65, 91, 101)


def project(
    file, rank, height=0, flipped=False, view="3d", yaw=0.0, zoom=1.0, tilt=0.5
):
    """Map board coordinates and height to logical screen pixels.

    2D is a fixed square grid. 3D rotates the ground plane, scales it and
    foreshortens depth; it is parallel projection, not a perspective camera."""
    # Flat mode ignores camera controls: square size and hit testing stay stable.
    if view == "2d":
        return (
            (216 + file * 80, 694 - rank * 80 - height * 18)
            if flipped
            else (776 - file * 80, 134 + rank * 80 - height * 18)
        )
    u, v = file - 3.5, rank - 3.5
    if flipped:
        u, v = -u, -v
    # Rotate ground coordinates before parallel projection. At yaw=0 preserve
    # the familiar White-facing a-to-h direction. tilt is the ground foreshortening.
    c, s = math.cos(yaw), math.sin(yaw)
    u, v = u * c - v * s, u * s + v * c
    return (
        440 + (v - u) * 46 * zoom,
        410 + (u + v) * 46 * tilt * zoom - height * 49 * zoom,
    )


def cell_polygon(square, flipped=False, view="3d", yaw=0.0, zoom=1.0, tilt=0.5):
    """Project a square's four corners in consistent winding order."""
    f, r = square % 8, square // 8
    return [
        project(f + df, r + dr, 0, flipped, view, yaw, zoom, tilt)
        for df, dr in [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]
    ]


def square_at(pos, flipped=False, view="3d", yaw=0.0, zoom=1.0, tilt=0.5):
    """Invert the board transform; clicks hit square footprints, not sculptures."""
    if view == "2d":
        f = (pos[0] - 216) / 80 if flipped else (776 - pos[0]) / 80
        r = (694 - pos[1]) / 80 if flipped else (pos[1] - 134) / 80
        f, r = math.floor(f + 0.5), math.floor(r + 0.5)
        return r * 8 + f if 0 <= f < 8 and 0 <= r < 8 else None
    a = (pos[0] - 440) / (46 * zoom)
    b = (pos[1] - 410) / (46 * tilt * zoom)
    # Invert a=v-u, b=u+v; this must match project() exactly.
    u, v = (b - a) / 2, (a + b) / 2
    c, s = math.cos(yaw), math.sin(yaw)
    u, v = u * c + v * s, -u * s + v * c  # Inverse rotation, not the forward rotation.
    if flipped:
        u, v = -u, -v
    f, r = math.floor(u + 4), math.floor(v + 4)
    return r * 8 + f if 0 <= f < 8 and 0 <= r < 8 else None


def lathe(profile, segments=12):
    """Spin a radius/height profile around z to form a faceted solid."""
    # Each ring is an equally spaced circle at one profile height.
    rings = [
        [
            (
                math.cos(i * math.tau / segments) * radius,
                math.sin(i * math.tau / segments) * radius,
                z,
            )
            for i in range(segments)
        ]
        for radius, z in profile
    ]
    faces = []
    # Join matching neighbours into quads; modulo closes the final seam.
    for low, high in zip(rings, rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            faces.append([low[i], low[j], high[j], high[i]])
    faces.append(list(reversed(rings[0])))
    faces.append(rings[-1])
    return faces


def cuboid(cx, cy, cz, sx, sy, sz):
    """Return six polygon faces for a box; sx/sy are half-widths, sz is full height."""
    points = [
        (cx + x * sx, cy + y * sy, cz + z * sz)
        for z in (0, 1)
        for y in (-1, 1)
        for x in (-1, 1)
    ]
    return [
        [points[i] for i in face]
        for face in [
            (0, 1, 3, 2),
            (4, 6, 7, 5),
            (0, 4, 5, 1),
            (1, 5, 7, 3),
            (3, 7, 6, 2),
            (2, 6, 4, 0),
        ]
    ]


def make_piece(kind):
    """Each piece is a different silhouette, not merely a letter on a token."""
    profile = [
        (0.32, 0),
        (0.35, 0.07),
        (0.35, 0.13),
        (0.27, 0.19),
        (0.24, 0.23),
        (0.16, 0.30),
    ]
    tops = {
        "p": [(0.14, 0.50), (0.22, 0.57), (0.24, 0.70), (0.16, 0.82), (0, 0.86)],
        "r": [(0.19, 0.65), (0.29, 0.72), (0.29, 0.86)],
        "b": [(0.13, 0.65), (0.22, 0.72), (0.25, 0.84), (0.15, 1.05), (0, 1.19)],
        "q": [(0.14, 0.79), (0.28, 0.89), (0.20, 1.04), (0.28, 1.16)],
        "k": [(0.15, 0.84), (0.23, 0.94), (0.20, 1.05)],
        "n": [(0.17, 0.52), (0.22, 0.57)],
    }
    faces = lathe(profile + tops[kind])
    if kind == "r":
        for x, y in [(-0.2, -0.2), (-0.2, 0.2), (0.2, -0.2), (0.2, 0.2)]:
            faces += cuboid(x, y, 0.84, 0.09, 0.09, 0.18)
    elif kind == "k":
        faces += cuboid(0, 0, 1.04, 0.055, 0.055, 0.36)
        faces += cuboid(0, 0, 1.23, 0.19, 0.055, 0.08)
    elif kind == "q":
        for i in range(6):
            a = i * math.tau / 6
            faces += (
                lathe([(0.04, 1.16), (0.055, 1.24), (0, 1.30)], 6) if i == 0 else []
            )
            faces += cuboid(
                math.cos(a) * 0.22, math.sin(a) * 0.22, 1.12, 0.035, 0.035, 0.15
            )
    elif kind == "n":
        # Extrude a hand-drawn horse-head profile through a short thickness.
        outline = [
            (-0.22, 0.52),
            (-0.15, 0.90),
            (0.02, 1.22),
            (0.12, 1.08),
            (0.28, 1.00),
            (0.37, 0.79),
            (0.16, 0.77),
            (0.08, 0.61),
        ]
        sides = [[(x, y, z) for y, z in outline] for x in (-0.12, 0.12)]
        faces += sides
        for i in range(len(outline)):
            j = (i + 1) % len(outline)
            faces.append([sides[0][i], sides[0][j], sides[1][j], sides[1][i]])
    return faces


class Renderer:
    """Own drawing resources and cached meshes, but never change chess rules/state."""

    def __init__(self):
        """Create a logical canvas, bundled fonts and reusable procedural meshes."""
        # One logical resolution keeps drawing math independent of window size.
        self.canvas = pygame.Surface((1240, 800))
        self.font = pygame.font.Font(None, 28)
        self.small = pygame.font.Font(None, 22)
        self.title = pygame.font.Font(None, 45)
        self.meshes = {kind: make_piece(kind) for kind in "pnbrqk"}
        self.view = "3d"
        self.yaw = 0.0
        self.zoom = 1.0
        self.tilt = 0.5
        self.buttons = {}

    def text(self, value, pos, color=TEXT, font=None, center=False):
        """Render one text label; center=True interprets pos as its centre."""
        image = (font or self.font).render(str(value), True, color)
        self.canvas.blit(image, image.get_rect(center=pos) if center else pos)

    def wrap(self, text, x, y, width, color=TEXT):
        """Split a message at word boundaries so sidebar text stays inside its width."""
        line = ""
        for word in text.split():
            trial = (line + " " + word).strip()
            if self.small.size(trial)[0] > width and line:
                self.text(line, (x, y), color, self.small)
                y += 23
                line = word
            else:
                line = trial
        self.text(line, (x, y), color, self.small)
        return y + 23

    def button(self, key, label, rect, active=False):
        """Draw a button and register its logical hit rectangle for the controller."""
        rect = pygame.Rect(rect)
        self.buttons[key] = rect
        pygame.draw.rect(
            self.canvas, (91, 74, 45) if active else (41, 54, 75), rect, border_radius=7
        )
        pygame.draw.rect(
            self.canvas, GOLD if active else (91, 112, 138), rect, 1, border_radius=7
        )
        self.text(label, rect.center, GOLD if active else TEXT, self.small, True)

    def project(self, f, r, z=0, flipped=False):
        """Use the active camera settings so all scene elements share one transform."""
        return project(f, r, z, flipped, self.view, self.yaw, self.zoom, self.tilt)

    def flat_piece(self, piece, file, rank, flipped, lift, scale):
        """Original Staunton-style vector silhouettes, not downloaded artwork.

        Shared stepped plinth/collar, spherical pawn, slotted bishop, crenellated
        rook, horse-head knight, coronet queen and cross-topped king distinguish
        the traditional forms. Shapes stay within an 80px square at full scale.
        """
        cx, cy = self.project(file, rank, lift, flipped)
        fill = (248, 241, 220) if piece.isupper() else (35, 41, 51)
        edge = (45, 43, 41) if piece.isupper() else (223, 229, 235)

        def polygon(points, color=None):
            """Scale a local silhouette around its square centre and outline it."""
            pts = [(cx + x * scale, cy + y * scale) for x, y in points]
            pygame.draw.polygon(self.canvas, color or fill, pts)
            pygame.draw.lines(self.canvas, edge, True, pts, 2)

        def line(a, b):
            """Draw a small detail with the same scaling as the surrounding silhouette."""
            pygame.draw.line(
                self.canvas,
                edge,
                (cx + a[0] * scale, cy + a[1] * scale),
                (cx + b[0] * scale, cy + b[1] * scale),
                max(1, round(2 * scale)),
            )

        def circle(x, y, r, color=None):
            """Draw rounded details without depending on external images or fonts."""
            centre = (round(cx + x * scale), round(cy + y * scale))
            radius = max(1, round(r * scale))
            pygame.draw.circle(self.canvas, color or fill, centre, radius)
            pygame.draw.circle(
                self.canvas, edge, centre, radius, max(1, round(2 * scale))
            )

        # Weighted stepped base and flared stem: all six share a family profile.
        polygon(
            [
                (-25, 31),
                (25, 31),
                (25, 25),
                (21, 20),
                (17, 17),
                (-17, 17),
                (-21, 20),
                (-25, 25),
            ]
        )
        line((-22, 25), (22, 25))
        kind = piece.lower()
        if kind == "n":
            polygon(
                [
                    (-18, 18),
                    (-18, 4),
                    (-15, -8),
                    (-8, -20),
                    (-9, -29),
                    (-2, -24),
                    (5, -26),
                    (12, -18),
                    (18, -13),
                    (23, -3),
                    (18, 3),
                    (8, 1),
                    (3, 6),
                    (7, 18),
                ]
            )
            # Mane, bridle and nostril make it a horse, not a featureless wedge.
            line((-11, -9), (-5, -18))
            line((-12, -1), (-7, -10))
            line((7, -17), (17, -7))
            circle(6, -14, 2, edge)
            line((15, -1), (20, -1))
        elif kind == "r":
            polygon(
                [
                    (-18, 18),
                    (-14, 10),
                    (-13, -12),
                    (-21, -16),
                    (-21, -31),
                    (-12, -31),
                    (-12, -23),
                    (-5, -23),
                    (-5, -31),
                    (5, -31),
                    (5, -23),
                    (12, -23),
                    (12, -31),
                    (21, -31),
                    (21, -16),
                    (13, -12),
                    (14, 10),
                    (18, 18),
                ]
            )
            line((-13, -11), (13, -11))
            line((-14, 10), (14, 10))
        else:
            polygon(
                [
                    (-18, 18),
                    (-13, 11),
                    (-9, -2),
                    (-9, -9),
                    (9, -9),
                    (9, -2),
                    (13, 11),
                    (18, 18),
                ]
            )
            polygon([(-14, -5), (14, -5), (14, -10), (-14, -10)])
            if kind == "p":
                circle(0, -21, 11)
            elif kind == "b":
                polygon(
                    [
                        (0, -36),
                        (-10, -25),
                        (-13, -18),
                        (-7, -11),
                        (7, -11),
                        (13, -18),
                        (10, -25),
                    ]
                )
                line((2, -30), (-4, -19))
                circle(0, -36, 2)
            elif kind == "q":
                polygon(
                    [
                        (-11, -11),
                        (-19, -29),
                        (-9, -23),
                        (0, -34),
                        (9, -23),
                        (19, -29),
                        (11, -11),
                    ]
                )
                for x, y in [(-19, -29), (0, -34), (19, -29)]:
                    circle(x, y, 3)
                line((-9, -16), (9, -16))
            else:
                polygon(
                    [
                        (-11, -11),
                        (-14, -21),
                        (-8, -25),
                        (-4, -25),
                        (-4, -30),
                        (-11, -30),
                        (-11, -35),
                        (-4, -35),
                        (-4, -40),
                        (4, -40),
                        (4, -35),
                        (11, -35),
                        (11, -30),
                        (4, -30),
                        (4, -25),
                        (8, -25),
                        (14, -21),
                        (11, -11),
                    ]
                )
                line((-11, -20), (11, -20))

    def piece(
        self,
        piece,
        file,
        rank,
        flipped=False,
        lift=0,
        scale=1,
        lean=0,
        facing=None,
        attack=0,
        stride=0,
    ):
        """Draw a 2D icon or assemble and shade one original 3D-style character.

        Local mesh coordinates are rotated toward facing, then placed on a board
        square. Animation supplies lift, collapse, arm thrust and walking stride."""
        if self.view == "2d":
            self.flat_piece(piece, file, rank, flipped, lift, scale)
            return
        white = piece.isupper()
        kind = piece.lower()
        skin = (230, 185, 136) if white else (164, 180, 188)
        cloth = (159, 58, 49) if white else (55, 82, 153)
        metal = (218, 210, 176) if white else (96, 135, 167)
        gold = (225, 178, 75)
        # A cache holds each original sculpture's stone base. Humanoid parts
        # are added as separate coloured solids with articulated arms/feet.
        components = []
        if kind == "r":
            components = [(self.meshes[kind], metal)]
            components.append((cuboid(0, -0.34, 0.35, 0.31, 0.10, 0.22), cloth))
            # A siege-ram face/barrel, extended during the strike.
            components.append(
                (cuboid(0.30 + attack * 0.14, 0, 0.57, 0.27, 0.09, 0.09), gold)
            )
        else:
            base = lathe([(0.32, 0), (0.34, 0.07), (0.28, 0.13), (0.23, 0.17)], 12)
            components.append((base, metal))
            if kind == "n":
                components.append((self.meshes["n"], metal))
                # Mounted rider's torso and plumed helmet.
                components.append(
                    (lathe([(0.13, 0.83), (0.14, 1.12), (0.10, 1.20)], 8), cloth)
                )
                components.append(
                    (
                        lathe([(0.11, 1.19), (0.15, 1.30), (0.10, 1.42), (0, 1.45)], 8),
                        metal,
                    )
                )
                components.append((cuboid(-0.08, 0, 1.43, 0.12, 0.04, 0.08), cloth))
            else:
                if kind in "bq":
                    body = lathe(
                        [(0.24, 0.18), (0.19, 0.42), (0.12, 0.78), (0.18, 0.93)], 10
                    )
                else:
                    body = cuboid(0, 0, 0.34, 0.17, 0.12, 0.46)
                components.append((body, cloth))
                for side in (-1, 1):
                    foot = side * 0.10
                    components.append(
                        (
                            cuboid(
                                0.06 + foot * stride,
                                0.10 * side,
                                0.17,
                                0.15,
                                0.07,
                                0.12,
                            ),
                            metal,
                        )
                    )
                components.append(
                    (
                        lathe(
                            [(0.11, 0.88), (0.15, 0.96), (0.15, 1.10), (0.08, 1.17)], 10
                        ),
                        skin,
                    )
                )
                if kind == "p":
                    components.append(
                        (
                            lathe(
                                [(0.16, 1.02), (0.18, 1.14), (0.08, 1.24), (0, 1.26)],
                                10,
                            ),
                            metal,
                        )
                    )
                    components.append(
                        (
                            cuboid(0.17 + attack * 0.13, -0.19, 0.49, 0.05, 0.15, 0.23),
                            metal,
                        )
                    )
                    components.append(
                        (cuboid(0.17, 0.19, 0.77, 0.07, 0.04, 0.29), gold)
                    )
                elif kind == "b":
                    components.append(
                        (lathe([(0.15, 1.09), (0.15, 1.22), (0, 1.48)], 8), cloth)
                    )
                    components.append(
                        (cuboid(0.20, 0.20, 0.22, 0.035, 0.035, 1.14), gold)
                    )
                elif kind in "qk":
                    components.append(
                        (lathe([(0.16, 1.10), (0.18, 1.22), (0.17, 1.26)], 10), gold)
                    )
                    for i in range(5):
                        a = i * math.tau / 5
                        components.append(
                            (
                                cuboid(
                                    math.cos(a) * 0.13,
                                    math.sin(a) * 0.13,
                                    1.24,
                                    0.035,
                                    0.035,
                                    0.11,
                                ),
                                gold,
                            )
                        )
                    if kind == "k":
                        components.append(
                            (cuboid(0.27, 0.16, 0.65, 0.03, 0.025, 0.61), metal)
                        )
                        components.append(
                            (cuboid(0.27, 0.16, 0.75, 0.13, 0.035, 0.04), gold)
                        )
                    else:
                        components.append(
                            (cuboid(0.20, 0.18, 0.56, 0.025, 0.025, 0.64), gold)
                        )
            # Arms lean into strikes independently of the torso.
            for side in (-1, 1):
                components.append(
                    (
                        cuboid(
                            0.09 + attack * 0.19,
                            side * 0.20,
                            0.60 + attack * 0.12,
                            0.10,
                            0.055,
                            0.21,
                        ),
                        metal,
                    )
                )
        angle = (
            facing if facing is not None else (math.pi / 2 if white else -math.pi / 2)
        )
        # Rotate local character points, then translate to its board position.
        ca, sa = math.cos(angle), math.sin(angle)
        polygons = []
        for mesh, base in components:
            for vertices in mesh:
                world = []
                for x, y, z in vertices:
                    x += z * lean
                    world.append(
                        (
                            file + x * ca - y * sa,
                            rank + x * sa + y * ca,
                            lift + z * scale,
                        )
                    )
                screen = [self.project(x, y, z, flipped) for x, y, z in world]
                depth = sum(
                    self.project(x, y, 0, flipped)[1] for x, y, z in world
                ) / len(world)
                a, b, c = vertices[:3]
                ux, uy, uz = [b[i] - a[i] for i in range(3)]
                vx, vy, vz = [c[i] - a[i] for i in range(3)]
                # Cross product gives a face normal for simple directional shading.
                nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
                length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
                shade = 0.68 + 0.25 * abs((nx * 0.4 + ny * -0.5 + nz * 0.76) / length)
                col = tuple(min(255, int(channel * shade)) for channel in base)
                polygons.append((depth, screen, col))
        # Painter order is approximate: distant polygons first, near ones last.
        for _, poly, col in sorted(polygons, key=lambda item: item[0]):
            pygame.draw.polygon(self.canvas, col, poly)
            pygame.draw.aalines(
                self.canvas, tuple(max(0, c - 25) for c in col), True, poly
            )
        px, py = self.project(file, rank, 0.12 + lift, flipped)
        if scale > 0.5:
            self.text(
                piece.upper(),
                (px, py),
                (40, 35, 30) if white else (225, 235, 245),
                self.small,
                True,
            )

    def effect(self, anim, values, flipped):
        """Draw an attacker-specific combat effect without changing the legal position."""
        if not values["effect"]:
            return
        move = anim["move"]
        kind = anim["piece"].lower()
        t = values["t"]
        source = self.project(values["file"], values["rank"], 0.85, flipped)
        target = self.project(
            anim["capture_sq"] % 8, anim["capture_sq"] // 8, 0.65, flipped
        )
        cx, cy = target
        if kind in "bq":
            color = (167, 129, 255) if kind == "b" else (255, 220, 118)
            pts = [source]
            for i in range(1, 7):
                k = i / 7
                wave = math.sin(i * 3 + t * 50) * 10
                pts.append(
                    (
                        source[0] + (cx - source[0]) * k + wave,
                        source[1] + (cy - source[1]) * k - wave,
                    )
                )
            pts.append(target)
            pygame.draw.lines(self.canvas, color, False, pts, 3)
            pygame.draw.circle(
                self.canvas,
                color,
                (round(cx), round(cy)),
                round(12 + abs(math.sin(t * 30)) * 16),
                2,
            )
        elif kind in "nk":
            radius = 30 if kind == "k" else 39
            pygame.draw.arc(
                self.canvas,
                (238, 237, 210),
                (cx - radius, cy - radius, radius * 2, radius * 2),
                t * 5,
                t * 5 + 2.2,
                3,
            )
        else:
            pygame.draw.circle(
                self.canvas,
                GOLD,
                (round(cx), round(cy)),
                round(15 + (t - 0.45) * 60),
                2,
            )
        if t >= 0.60:
            for i in range(10):
                a = i * math.tau / 10 + t * 3
                r = (t - 0.60) * 145
                pygame.draw.line(
                    self.canvas,
                    GOLD,
                    (cx + math.cos(a) * r * 0.5, cy + math.sin(a) * r * 0.5),
                    (cx + math.cos(a) * r, cy + math.sin(a) * r),
                    2,
                )

    def draw(self, app):
        """Paint one frame back-to-front and rebuild the clickable button map.

        The committed board is normally the source. During a preview, draw the
        before-board and replace affected figures with their interpolated poses."""
        self.canvas.fill(BG)
        self.buttons = {}
        self.text("CLOCKWORK CHESS", (30, 24), GOLD, self.title)
        self.text(
            "DAY 11 / VICE-INSPIRED ENGINE / ORIGINAL ANIMATED ART",
            (32, 72),
            MUTED,
            self.small,
        )
        self.view = app.view
        self.yaw, self.zoom, self.tilt = app.yaw, app.zoom, app.tilt
        flipped = app.flipped
        # The flat board starts at y=94; a 3D-only y=115 clip cut off rank 8.
        self.canvas.set_clip(
            pygame.Rect(
                0,
                90 if self.view == "2d" else 115,
                870,
                653 if self.view == "2d" else 628,
            )
        )
        # Solid board plinth, then individual square top faces.
        corners = [
            self.project(-0.5, -0.5),
            self.project(7.5, -0.5),
            self.project(7.5, 7.5),
            self.project(-0.5, 7.5),
        ]
        for a, b in zip(corners, corners[1:] + corners[:1]):
            pygame.draw.polygon(
                self.canvas, (40, 46, 57), [a, b, (b[0], b[1] + 22), (a[0], a[1] + 22)]
            )
        # Highlights derive from engine-approved moves, never from sprite shapes.
        legal_to = {m.to_sq for m in app.legal if m.from_sq == app.selected}
        for square in range(64):
            poly = cell_polygon(
                square, flipped, self.view, self.yaw, self.zoom, self.tilt
            )
            col = LIGHT if (square % 8 + square // 8) % 2 else DARK
            if app.last_move and square in (app.last_move.from_sq, app.last_move.to_sq):
                col = (144, 137, 82)
            if square == app.selected:
                col = (222, 179, 84)
            if square in legal_to:
                col = (100, 162, 133)
            pygame.draw.polygon(self.canvas, col, poly)
            pygame.draw.aalines(self.canvas, (42, 62, 70), True, poly)
            if app.hint_move and square in (app.hint_move.from_sq, app.hint_move.to_sq):
                # Outlines remain visible around the sculpture in either view.
                pygame.draw.lines(self.canvas, GOLD, True, poly, 4)
        for f in range(8):
            location = self.project(f, -0.85, 0, flipped)
            if self.view == "2d":
                location = (self.project(f, 0, 0, flipped)[0], 746)
            self.text("abcdefgh"[f], location, MUTED, self.small, True)
        for r in range(8):
            location = self.project(-0.85, r, 0, flipped)
            if self.view == "2d":
                location = (160, self.project(0, r, 0, flipped)[1])
            self.text(str(r + 1), location, MUTED, self.small, True)
        figures = []
        anim = app.animation
        hidden = set()
        if anim:
            move = anim["move"]
            hidden.add(move.from_sq)
            if anim["captured"] != ".":
                hidden.add(anim["capture_sq"])
            if move.castle:
                hidden.add(anim["rook_from"])
        # A preview uses the BEFORE-board; hide its mover/victim/rook so they
        # are not drawn twice alongside their animated replacements.
        board = anim["board"] if anim else app.position.board
        for square, piece in enumerate(board):
            if piece != "." and square not in hidden:
                f, r = square % 8, square // 8
                figures.append(
                    (self.project(f, r, 0, flipped)[1], piece, f, r, 0, 1, 0)
                )
        if anim:
            values = pose(anim)
            move = anim["move"]
            progress = values["progress"]
            f, r = values["file"], values["rank"]
            figures.append(
                (
                    self.project(f, r, 0, flipped)[1] + 1,
                    anim["piece"],
                    f,
                    r,
                    values["lift"],
                    1,
                    0,
                )
            )
            if anim["captured"] != "." and values["victim_visible"]:
                cf, cr = anim["capture_sq"] % 8, anim["capture_sq"] // 8
                figures.append(
                    (
                        self.project(cf, cr, 0, flipped)[1],
                        anim["captured"],
                        cf,
                        cr,
                        0,
                        values["victim_scale"],
                        values["victim_lean"],
                    )
                )
            if move.castle:
                rf = (
                    anim["rook_from"] % 8
                    + (anim["rook_to"] % 8 - anim["rook_from"] % 8) * progress
                )
                rr = anim["rook_from"] // 8
                figures.append(
                    (
                        self.project(rf, rr, 0, flipped)[1],
                        "R" if anim["piece"].isupper() else "r",
                        rf,
                        rr,
                        0,
                        1,
                        0,
                    )
                )
        # Sort whole figures by projected ground depth after camera rotation.
        for _, piece, f, r, lift, scale, lean in sorted(
            figures, key=lambda item: item[0]
        ):
            moving = (
                anim
                and piece == anim["piece"]
                and (f, r) == (values["file"], values["rank"])
            )
            self.piece(
                piece,
                f,
                r,
                flipped,
                lift,
                scale,
                lean,
                values["facing"] if moving else None,
                values["attack"] if moving else 0,
                math.sin(values["progress"] * math.pi * 6) if moving else 0,
            )
        if anim:
            self.effect(anim, values, flipped)
            if anim["captured"] != ".":
                self.text(
                    STYLES[anim["piece"].lower()][0] + " / " + values["phase"],
                    (440, 100),
                    GOLD,
                    self.small,
                    True,
                )
        self.canvas.set_clip(None)
        if self.view == "3d":
            # Right-aligned on the subtitle row, clear of subtitle and board.
            for key, label, rect in [
                ("zoom_out", "−", (620, 67, 38, 26)),
                ("zoom_in", "+", (666, 67, 38, 26)),
                ("camera_reset", "Reset view", (712, 67, 100, 26)),
            ]:
                self.button(key, label, rect)
        self.text(
            "Click square bases to select and move. Green tiles show legal destinations.",
            (440, 765),
            MUTED,
            self.small,
            True,
        )
        self.text(
            "Ivory = White    •    Steel blue = Black    •    N = knight",
            (440, 786),
            MUTED,
            self.small,
            True,
        )
        self.text(
            "V: 2D/3D | Wheel: zoom | Left-drag: orbit",
            (610, 40),
            MUTED,
            self.small,
            True,
        )

        pygame.draw.line(self.canvas, (66, 82, 105), (874, 25), (874, 775))
        mode = "Human vs computer" if app.ai_enabled else "Two local players"
        self.text(mode, (900, 30), GOLD)
        self.text(
            ("White" if app.position.side == "w" else "Black") + " to move", (900, 68)
        )
        y = self.wrap(app.status, 900, 112, 310, GOLD)
        for key, label, rect, active in [
            ("new", "New game [R]", (900, 208, 305, 40), False),
            ("mode", "Vs AI / two players", (900, 258, 305, 40), app.ai_enabled),
            (
                "side",
                "Human: " + ("White" if app.human_side == "w" else "Black"),
                (900, 308, 305, 40),
                False,
            ),
            ("level", "AI: " + app.level.title(), (900, 358, 305, 40), False),
            ("undo", "Undo [U]", (900, 408, 145, 40), False),
            ("hint", "Hint [H]", (1060, 408, 145, 40), app.hint_move is not None),
            ("flip", "Flip board [F]", (900, 458, 145, 40), app.flipped),
            ("sound", "Sound [M]", (1060, 458, 145, 40), app.sounds.enabled),
        ]:
            self.button(key, label, rect, active)
        self.button(
            "view",
            "View: " + app.view.upper() + " [V]",
            (900, 510, 305, 38),
            app.view == "3d",
        )
        if app.promotion:
            self.text("Promote to:", (900, 562), GOLD)
            for i, piece in enumerate("qrbn"):
                self.button(
                    "promote_" + piece, piece.upper(), (900 + i * 77, 589, 68, 36)
                )
        else:
            self.wrap(
                "AI levels change search time/depth, not an Elo rating. Side or mode changes start a fresh game.",
                900,
                560,
                305,
                MUTED,
            )
        self.text("Recent moves (coordinate notation)", (900, 658), MUTED, self.small)
        recent = app.moves[-8:]
        for i in range(0, len(recent), 2):
            self.text(
                "   ".join(recent[i : i + 2]),
                (900, 684 + (i // 2) * 24),
                font=self.small,
            )
        return self.canvas
