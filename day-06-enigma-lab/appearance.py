"""Original procedural Enigma-inspired case, keys, lamps and rotor windows.

All art uses Pygame drawing primitives, not museum photos or commercial models.
This is an illustrative 2D machine face, not a dimensional mechanical replica.
"""

import pygame

WOOD = (99, 65, 40)
METAL = (37, 41, 39)
IVORY = (226, 216, 181)
BRASS = (169, 143, 88)


def blend(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def label(screen, font, value, center, color=IVORY):
    image = font.render(str(value), True, color)
    screen.blit(image, image.get_rect(center=center))


def machine_case(screen, small):
    """Layered edges and restrained grain suggest an open wooden carry case."""
    pygame.draw.rect(screen, (4, 7, 7), (237, 158, 614, 539), border_radius=23)
    pygame.draw.rect(screen, WOOD, (224, 149, 614, 539), border_radius=22)
    pygame.draw.rect(screen, (157, 111, 64), (227, 152, 608, 533), 3, border_radius=21)
    for x in (232, 824):
        for y in range(173, 652, 16):
            pygame.draw.line(screen, (117, 77, 44), (x, y), (x + 5, y + 9), 1)
    pygame.draw.rect(screen, (15, 20, 19), (244, 165, 574, 505), border_radius=14)
    pygame.draw.rect(screen, METAL, (249, 169, 564, 495), border_radius=12)
    pygame.draw.rect(screen, (79, 83, 73), (250, 169, 562, 494), 1, border_radius=12)
    for x, y in ((260, 181), (802, 181), (260, 639), (802, 639)):
        pygame.draw.circle(screen, (120, 119, 99), (x, y), 4)
        pygame.draw.line(screen, (37, 40, 36), (x - 2, y - 2), (x + 2, y + 2), 1)
    # Carry-case hinges: deliberately generic, no maker markings or insignia.
    for x in (295, 720):
        pygame.draw.rect(screen, BRASS, (x, 150, 41, 14), border_radius=3)
        pygame.draw.line(screen, (67, 58, 37), (x, 157), (x + 41, 157), 2)
    label(screen, small, "ENIGMA I  /  ROTOR MACHINE", (531, 278))
    pygame.draw.line(screen, (71, 75, 65), (269, 296), (794, 296), 1)
    pygame.draw.line(screen, (71, 75, 65), (269, 454), (794, 454), 1)
    label(screen, small, "LAMPBOARD", (531, 305), (153, 158, 139))
    label(screen, small, "KEYBOARD", (531, 532), (153, 158, 139))


def rotor(screen, center, old, new, progress, name, fonts):
    """Scroll one letter pitch only when this wheel actually advanced.

    A clipped moving alphabet strip makes turnover visible, including Z to A.
    Knurling moves with the same eased fraction. This is presentation only: the
    model already stepped before it computed the electrical signal.
    """
    small, normal, large = fonts
    x, y = center
    moved = old != new
    t = progress if moved else 1
    eased = t * t * (3 - 2 * t)
    label(screen, small, name, (x, y - 47), (181, 186, 162))
    wheel = pygame.Rect(x + 31, y - 33, 24, 76)
    pygame.draw.rect(screen, (83, 84, 73), wheel, border_radius=5)
    pygame.draw.rect(screen, BRASS, wheel, 1, border_radius=5)
    for offset in range(-10, 90, 7):
        yy = y - 33 + offset + round(eased * 7 if moved else 0)
        if wheel.top + 3 <= yy < wheel.bottom - 2:
            pygame.draw.line(screen, (164, 158, 126), (x + 34, yy), (x + 51, yy), 2)
    frame = pygame.Rect(x - 29, y - 33, 55, 72)
    pygame.draw.rect(screen, (126, 113, 78), frame, border_radius=7)
    pygame.draw.rect(screen, (8, 12, 11), frame.inflate(-7, -7), border_radius=4)
    window = frame.inflate(-13, -13)
    prior = screen.get_clip()
    screen.set_clip(window)
    pygame.draw.rect(screen, (218, 211, 176), window)
    if moved:
        pitch = 42
        # Current model is NEW; OLD and NEW strips slide as one physical ring.
        for letter, dy in ((old, -eased * pitch), (new, (1 - eased) * pitch)):
            label(screen, large, letter, (x - 1, y + 1 + round(dy)), (27, 35, 28))
    else:
        label(screen, large, new, (x - 1, y + 1), (27, 35, 28))
    screen.set_clip(prior)
    pygame.draw.line(screen, (115, 53, 41), (x - 27, y + 4), (x - 20, y + 4), 2)


def lamp(screen, rect, letter, brightness, font):
    """Warm additive halo and a glass reflection around a circular lamp lens."""
    center = rect.center
    if brightness > 0:
        glow = pygame.Surface((90, 90), pygame.SRCALPHA)
        for radius in range(40, 16, -2):
            alpha = round(brightness * 45 * (1 - (radius - 16) / 26))
            pygame.draw.circle(glow, (255, 190, 55, alpha), (45, 45), radius)
        screen.blit(glow, (center[0] - 45, center[1] - 45))
    pygame.draw.circle(screen, (7, 11, 10), center, 21)
    pygame.draw.circle(screen, (107, 109, 92), center, 19, 2)
    pygame.draw.circle(
        screen, blend((33, 39, 33), (248, 203, 91), brightness), center, 16
    )
    label(
        screen, font, letter, center, blend((164, 170, 147), (42, 33, 17), brightness)
    )
    pygame.draw.arc(
        screen, (141, 146, 126), (center[0] - 14, center[1] - 14, 28, 28), 0.6, 2.4, 1
    )


def key(screen, rect, letter, depressed, font):
    """Raised ivory typewriter key moves down onto its dark mechanical stem."""
    x, y = rect.center
    pygame.draw.circle(screen, (9, 13, 12), (x, y + 5), 22)
    pygame.draw.circle(screen, (79, 81, 68), (x, y + 2), 21)
    offset = 4 if depressed else -2
    pygame.draw.circle(screen, (178, 168, 132), (x, y + offset), 19)
    pygame.draw.circle(screen, (229, 221, 187), (x, y + offset - 1), 17)
    pygame.draw.circle(screen, (117, 112, 87), (x, y + offset), 18, 1)
    label(screen, font, letter, (x, y + offset), (33, 36, 29))
    if depressed:
        pygame.draw.circle(screen, (237, 187, 72), (x, y + offset), 21, 2)
