"""Display-mode adapter: 2D remains a working fallback, not a second cipher."""

import math
import pygame
from scene3d import Renderer

TOGGLE = pygame.Rect(738, 17, 151, 38)
RESET_VIEW = pygame.Rect(901, 17, 155, 38)


class View:
    def __init__(self, size):
        self.size = size
        self.renderer = None
        self.drag = None
        self.window = pygame.display.set_mode(size)
        self.note = ""

    def toggle(self):
        """Release GPU resources before destroying the associated GL context."""
        if self.renderer:
            self.renderer.close()
            self.renderer = None
            self.window = pygame.display.set_mode(self.size)
            self.note = "2D study view."
            return
        try:
            pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
            pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
            self.window = pygame.display.set_mode(
                self.size, pygame.OPENGL | pygame.DOUBLEBUF
            )
            self.renderer = Renderer(self.size)
            self.note = "3D: drag to orbit, wheel to zoom; short click presses a key."
        except Exception as error:
            # Driver/context availability is a platform property. A failure must
            # leave a usable 2D machine rather than terminate the application.
            self.renderer = None
            self.window = pygame.display.set_mode(self.size)
            self.note = f"3D unavailable: {error}. Using 2D."

    def event(self, event, lab):
        """Return True if handled; do not forward camera drags to 2D key hitboxes."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if TOGGLE.collidepoint(event.pos):
                lab.release()
                self.toggle()
                lab.message = self.note
                return True
            if RESET_VIEW.collidepoint(event.pos):
                if self.renderer:
                    self.renderer.camera.reset()
                return True
        if not self.renderer:
            return False
        viewport = pygame.Rect(self.renderer.viewport)
        if event.type == pygame.MOUSEWHEEL:
            self.renderer.camera.zoom(event.y)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and viewport.collidepoint(event.pos):
            if event.button in (4, 5):
                self.renderer.camera.zoom(1 if event.button == 4 else -1)
            elif event.button == 1:
                self.drag = {"start": event.pos, "last": event.pos, "active": False}
            return True
        if event.type == pygame.MOUSEMOTION and self.drag:
            if math.dist(event.pos, self.drag["start"]) > 6:
                self.drag["active"] = True
            if self.drag["active"]:
                last = self.drag["last"]
                self.renderer.camera.orbit(
                    event.pos[0] - last[0], event.pos[1] - last[1]
                )
            self.drag["last"] = event.pos
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag:
            drag, self.drag = self.drag, None
            if not drag["active"] and lab.active_field is None:
                key = self.renderer.camera.pick(event.pos, self.renderer.viewport)
                if key:
                    lab.press(key)  # a short mouse click gets the visual pulse
            return True
        if event.type == pygame.WINDOWFOCUSLOST:
            self.drag = None
            lab.release()
        return False

    def draw(self, lab, fonts, draw_2d):
        canvas = pygame.Surface(self.size, pygame.SRCALPHA)
        draw_2d(canvas, lab, fonts)
        if self.renderer:
            # Keep configuration header + bottom signal trace, clear the 2D face.
            pygame.draw.rect(canvas, (0, 0, 0, 0), (0, 145, self.size[0], 550))
            for rect, label in (
                (pygame.Rect(24, 174, 212, 28), "Keyboard mode"),
                (pygame.Rect(872, 174, 184, 28), "Reset message"),
            ):
                pygame.draw.rect(canvas, (36, 51, 62), rect, border_radius=5)
                canvas.blit(
                    fonts[0].render(label, True, (237, 243, 250)), rect.move(10, 4)
                )
            instruction = fonts[0].render(
                "Drag: orbit  /  Wheel: zoom  /  Short click: key  /  Reset 3D view: camera",
                True,
                (237, 243, 250),
            )
            canvas.blit(instruction, (24, 680))
            # A compact transcript strip sits outside the 3D viewport.
            pygame.draw.rect(canvas, (13, 19, 28), (24, 202, 1032, 23))
            image = fonts[0].render(
                f"IN {lab.plain[-30:]}   OUT {lab.cipher[-30:]}   WINDOWS {lab.machine.positions}",
                True,
                (237, 243, 250),
            )
            canvas.blit(image, (24, 202))
        for rect, label in (
            (TOGGLE, "2D view" if self.renderer else "3D view"),
            (RESET_VIEW, "Reset 3D view"),
        ):
            pygame.draw.rect(canvas, (36, 51, 62), rect, border_radius=6)
            canvas.blit(fonts[0].render(label, True, (237, 243, 250)), rect.move(12, 8))
        if self.renderer:
            self.renderer.render(lab, canvas)
        else:
            self.window.blit(canvas, (0, 0))

    def close(self):
        if self.renderer:
            self.renderer.close()
