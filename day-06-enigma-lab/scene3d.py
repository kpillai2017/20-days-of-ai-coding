"""Procedural OpenGL Enigma-inspired model plus dependency-free camera maths.

OpenGL imports occur only when constructing a renderer, so the cipher, tests
and 2D interface still run without a GPU. This uses a compatibility OpenGL
context for small, readable teaching primitives, not a modern shader engine.
"""

import math
from enigma import ALPHABET

ROWS = ("QWERTZUIO", "ASDFGHJK", "PYXCVBNML")


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def unit(v):
    length = math.sqrt(dot(v, v))
    return tuple(x / length for x in v)


def keys():
    """World-space centres: x across, y height, z toward the operator."""
    return {
        letter: ((col - (len(row) - 1) / 2) * 0.87, 0.86, 1.15 + r * 0.83)
        for r, row in enumerate(ROWS)
        for col, letter in enumerate(row)
    }


class Camera:
    def __init__(self):
        self.reset()

    def reset(self):
        self.yaw, self.pitch, self.distance = 0, 49, 15

    def orbit(self, dx, dy):
        self.yaw = (self.yaw - dx * 0.4) % 360
        # Orbit all the way around horizontally; avoid camera pole singularities.
        self.pitch = max(-75, min(85, self.pitch + dy * 0.35))

    def zoom(self, amount):
        self.distance = max(9, min(25, self.distance - amount * 0.8))

    def basis(self):
        yaw, pitch = map(math.radians, (self.yaw, self.pitch))
        eye = (
            self.distance * math.sin(yaw) * math.cos(pitch),
            0.3 + self.distance * math.sin(pitch),
            self.distance * math.cos(yaw) * math.cos(pitch),
        )
        forward = unit(tuple(t - e for t, e in zip((0, 0.3, 0), eye)))
        right = unit(cross(forward, (0, 1, 0)))
        up = cross(right, forward)
        return eye, forward, right, up

    def project(self, point, viewport):
        """Project for picking with the SAME camera/frustum used by OpenGL."""
        x, y, w, h = viewport
        eye, forward, right, up = self.basis()
        relative = tuple(p - e for p, e in zip(point, eye))
        depth = dot(relative, forward)
        if depth <= 0.1:
            return None
        focal = h / (2 * math.tan(math.radians(40) / 2))
        return (
            x + w / 2 + dot(relative, right) * focal / depth,
            y + h / 2 - dot(relative, up) * focal / depth,
            focal / depth,
        )

    def pick(self, pos, viewport):
        """Nearest projected circular key; board-facing side only, not through case."""
        eye, *_ = self.basis()
        if eye[1] < 1 or eye[2] < 0:
            return None
        choices = []
        for letter, center in keys().items():
            p = self.project(center, viewport)
            if p and math.dist(pos, p[:2]) <= 0.34 * p[2]:
                choices.append((math.dist(pos, p[:2]), letter))
        return min(choices)[1] if choices else None


class Renderer:
    """Meshes, lights and cached glyph textures; no external images or models."""

    def __init__(self, size):
        from OpenGL import GL, GLU
        import pygame

        self.gl, self.glu, self.pygame = GL, GLU, pygame
        self.size = size
        self.camera = Camera()
        self.viewport = (20, 225, size[0] - 40, 455)
        self.textures = {}
        self.overlay_texture = GL.glGenTextures(1)
        self.quadric = GLU.gluNewQuadric()
        self.font = pygame.font.Font(None, 64)
        GL.glClearColor(0.045, 0.06, 0.065, 1)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_NORMALIZE)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glColorMaterial(GL.GL_FRONT_AND_BACK, GL.GL_AMBIENT_AND_DIFFUSE)
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, (0.9, 0.85, 0.72, 1))
        GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, (0.3, 0.3, 0.32, 1))
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, GL.GL_SPECULAR, (0.5, 0.5, 0.45, 1))
        GL.glMaterialf(GL.GL_FRONT_AND_BACK, GL.GL_SHININESS, 45)

    def box(self, center, dimensions, color):
        g = self.gl
        x, y, z = center
        a, b, c = (v / 2 for v in dimensions)
        g.glColor3f(*color)
        g.glPushMatrix()
        g.glTranslatef(x, y, z)
        g.glScalef(a, b, c)
        faces = [
            ((0, 1, 0), [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)]),
            ((0, -1, 0), [(-1, -1, 1), (-1, -1, -1), (1, -1, -1), (1, -1, 1)]),
            ((0, 0, 1), [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]),
            ((0, 0, -1), [(1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1)]),
            ((1, 0, 0), [(1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1)]),
            ((-1, 0, 0), [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)]),
        ]
        g.glBegin(g.GL_QUADS)
        for normal, vertices in faces:
            g.glNormal3f(*normal)
            for vertex in vertices:
                g.glVertex3f(*vertex)
        g.glEnd()
        g.glPopMatrix()

    def cylinder(self, center, radius, height, color, axis_x=False):
        """GLU cylinders start on z; turn them upright on y (or along x)."""
        g, u = self.gl, self.glu
        g.glColor3f(*color)
        g.glPushMatrix()
        g.glTranslatef(*center)
        g.glRotatef(90, 0, 1, 0) if axis_x else g.glRotatef(-90, 1, 0, 0)
        u.gluCylinder(self.quadric, radius, radius, height, 24, 1)
        u.gluDisk(self.quadric, 0, radius, 24, 1)
        g.glTranslatef(0, 0, height)
        u.gluDisk(self.quadric, 0, radius, 24, 1)
        g.glPopMatrix()

    def glyph(self, value, center, width=0.43, color=(0.13, 0.14, 0.11)):
        """Rasterise a letter once, then map its alpha texture onto a top plaque."""
        g = self.gl
        if value not in self.textures:
            surface = self.font.render(value, True, (255, 255, 255))
            texture = g.glGenTextures(1)
            self.textures[value] = texture
            g.glBindTexture(g.GL_TEXTURE_2D, texture)
            g.glTexParameteri(g.GL_TEXTURE_2D, g.GL_TEXTURE_MIN_FILTER, g.GL_LINEAR)
            g.glTexParameteri(g.GL_TEXTURE_2D, g.GL_TEXTURE_MAG_FILTER, g.GL_LINEAR)
            g.glTexImage2D(
                g.GL_TEXTURE_2D,
                0,
                g.GL_RGBA,
                *surface.get_size(),
                0,
                g.GL_RGBA,
                g.GL_UNSIGNED_BYTE,
                self.pygame.image.tostring(surface, "RGBA", True),
            )
        x, y, z = center
        g.glDisable(g.GL_LIGHTING)
        g.glEnable(g.GL_TEXTURE_2D)
        g.glEnable(g.GL_BLEND)
        g.glBlendFunc(g.GL_SRC_ALPHA, g.GL_ONE_MINUS_SRC_ALPHA)
        g.glBindTexture(g.GL_TEXTURE_2D, self.textures[value])
        g.glColor3f(*color)
        g.glBegin(g.GL_QUADS)
        for uv, vertex in [
            ((0, 0), (x - width / 2, y, z + width / 2)),
            ((1, 0), (x + width / 2, y, z + width / 2)),
            ((1, 1), (x + width / 2, y, z - width / 2)),
            ((0, 1), (x - width / 2, y, z - width / 2)),
        ]:
            g.glTexCoord2f(*uv)
            g.glVertex3f(*vertex)
        g.glEnd()
        g.glDisable(g.GL_BLEND)
        g.glDisable(g.GL_TEXTURE_2D)
        g.glEnable(g.GL_LIGHTING)

    def draw_machine(self, lab):
        g = self.gl
        progress, depressed, brightness = lab.animation()
        self.box((0, -0.45, 0), (10, 0.65, 8), (0.28, 0.15, 0.07))
        for x in (-4.8, 4.8):
            self.box((x, 0.05, 0), (0.4, 0.9, 8), (0.42, 0.24, 0.1))
        for z in (-3.8, 3.8):
            self.box((0, 0.05, z), (9.3, 0.9, 0.4), (0.38, 0.2, 0.08))
        self.box((0, 0.12, 0), (9.25, 0.45, 7.2), (0.09, 0.11, 0.1))
        # Open lid, metal inserts and hinges establish actual spatial thickness.
        self.box((0, 2.1, -4.05), (9.7, 3.3, 0.25), (0.32, 0.18, 0.08))
        self.box((0, 2.1, -3.89), (8.9, 2.6, 0.04), (0.12, 0.15, 0.13))
        for x in (-3, 3):
            self.cylinder((x, 0.1, -3.75), 0.15, 0.8, (0.55, 0.42, 0.18), True)
        for letter, (x, y, z) in keys().items():
            down = depressed and lab.pressed_key == letter
            h = 0.12 if down else 0.3
            self.cylinder((x, 0.35, z), 0.11, h, (0.38, 0.39, 0.33))
            self.cylinder((x, 0.35 + h, z), 0.33, 0.12, (0.75, 0.7, 0.53))
            self.glyph(letter, (x, 0.35 + h + 0.125, z))
            lamp_z = z - 2.5
            self.cylinder((x, 0.37, lamp_z), 0.31, 0.1, (0.27, 0.29, 0.24))
            lit = brightness if lab.lamp == letter else 0
            g.glMaterialfv(
                g.GL_FRONT_AND_BACK,
                g.GL_EMISSION,
                (lit * 0.55, lit * 0.3, lit * 0.04, 1),
            )
            self.cylinder(
                (x, 0.47, lamp_z),
                0.26,
                0.055,
                (0.18 + lit * 0.7, 0.21 + lit * 0.5, 0.15 + lit * 0.12),
            )
            g.glMaterialfv(g.GL_FRONT_AND_BACK, g.GL_EMISSION, (0, 0, 0, 1))
            self.glyph(
                letter,
                (x, 0.53, lamp_z),
                0.34,
                (0.9, 0.85, 0.61) if not lit else (0.18, 0.13, 0.04),
            )
        # Rotor bodies roll about their real axle direction (x). Rings and
        # knurled ridges are geometry; the top letter plaques aid readability.
        for i, name in enumerate(lab.machine.rotor_names):
            x = (i - 1) * 1.35
            old = ALPHABET.index(lab.old_positions[i])
            new = ALPHABET.index(lab.machine.positions[i])
            step = (new - old) % 26
            angle = (old + step * (progress * progress * (3 - 2 * progress))) * 360 / 26
            self.cylinder((x - 0.43, 0.88, -2.8), 0.64, 0.86, (0.32, 0.32, 0.25), True)
            for ridge in range(26):
                theta = math.radians(ridge * 360 / 26 + angle)
                self.box(
                    (
                        x + 0.46,
                        0.88 + 0.65 * math.cos(theta),
                        -2.8 + 0.65 * math.sin(theta),
                    ),
                    (0.1, 0.09, 0.09),
                    (0.6, 0.56, 0.36),
                )
            # Printed alphabet ring rotates with the wheel, not just its ridges.
            # Each textured letter is tangent to the cylinder surface.
            for n, letter in enumerate(ALPHABET):
                g.glPushMatrix()
                g.glTranslatef(x, 0.88, -2.8)
                g.glRotatef(n * 360 / 26 + angle, 1, 0, 0)
                self.glyph(letter, (0, 0.655, 0), 0.12, (0.92, 0.87, 0.68))
                g.glPopMatrix()
            self.box((x, 1.58, -2.8), (0.62, 0.06, 0.58), (0.78, 0.76, 0.6))
            self.glyph(lab.machine.positions[i], (x, 1.615, -2.8), 0.4)
            self.glyph(name, (x, 0.4, -3.5), 0.42, (0.85, 0.77, 0.5))
        # Simple plugboard sockets on the front fascia; configuration stays in UI.
        for i in range(13):
            self.cylinder(((i - 6) * 0.56, 0.36, 3.25), 0.08, 0.04, (0.42, 0.35, 0.2))

    def render(self, lab, overlay):
        g, u = self.gl, self.glu
        width, height = self.size
        g.glClear(g.GL_COLOR_BUFFER_BIT | g.GL_DEPTH_BUFFER_BIT)
        x, y, w, h = self.viewport
        g.glViewport(x, height - y - h, w, h)
        g.glMatrixMode(g.GL_PROJECTION)
        g.glLoadIdentity()
        u.gluPerspective(40, w / h, 0.1, 100)
        g.glMatrixMode(g.GL_MODELVIEW)
        g.glLoadIdentity()
        eye, *_ = self.camera.basis()
        u.gluLookAt(*eye, 0, 0.3, 0, 0, 1, 0)
        g.glEnable(g.GL_DEPTH_TEST)
        g.glEnable(g.GL_LIGHTING)
        g.glLightfv(g.GL_LIGHT0, g.GL_POSITION, (-5, 9, 7, 1))
        self.draw_machine(lab)
        # Existing 2D controls become one alpha overlay texture. Cipher forms,
        # study traces and transcripts remain usable without duplicating logic.
        g.glViewport(0, 0, width, height)
        g.glDisable(g.GL_DEPTH_TEST)
        g.glDisable(g.GL_LIGHTING)
        g.glMatrixMode(g.GL_PROJECTION)
        g.glLoadIdentity()
        g.glOrtho(0, width, height, 0, -1, 1)
        g.glMatrixMode(g.GL_MODELVIEW)
        g.glLoadIdentity()
        g.glEnable(g.GL_TEXTURE_2D)
        g.glBindTexture(g.GL_TEXTURE_2D, self.overlay_texture)
        g.glTexParameteri(g.GL_TEXTURE_2D, g.GL_TEXTURE_MIN_FILTER, g.GL_LINEAR)
        g.glTexParameteri(g.GL_TEXTURE_2D, g.GL_TEXTURE_MAG_FILTER, g.GL_LINEAR)
        g.glTexImage2D(
            g.GL_TEXTURE_2D,
            0,
            g.GL_RGBA,
            width,
            height,
            0,
            g.GL_RGBA,
            g.GL_UNSIGNED_BYTE,
            self.pygame.image.tostring(overlay, "RGBA", True),
        )
        g.glEnable(g.GL_BLEND)
        g.glBlendFunc(g.GL_SRC_ALPHA, g.GL_ONE_MINUS_SRC_ALPHA)
        g.glColor4f(1, 1, 1, 1)
        g.glBegin(g.GL_QUADS)
        for uv, v in [
            ((0, 1), (0, 0)),
            ((1, 1), (width, 0)),
            ((1, 0), (width, height)),
            ((0, 0), (0, height)),
        ]:
            g.glTexCoord2f(*uv)
            g.glVertex2f(*v)
        g.glEnd()
        g.glDisable(g.GL_BLEND)
        g.glDisable(g.GL_TEXTURE_2D)

    def close(self):
        g = self.gl
        if self.textures:
            g.glDeleteTextures(list(self.textures.values()))
        g.glDeleteTextures([self.overlay_texture])
        self.glu.gluDeleteQuadric(self.quadric)
