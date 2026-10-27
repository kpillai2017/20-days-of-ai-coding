"""Original vector symbols for familiar board-space concepts.

These are our own simple silhouettes, not scanned or traced Monopoly artwork.
Draw at a fixed reference size, then smoothly shrink into a reserved icon box.
The transparent surface guarantees symbols cannot paint over adjacent labels.
"""
import pygame


def icon_kind(index, kind):
    """Return a semantic symbol name, or None for an ordinary street."""
    if index in (0, 10, 20, 30):
        return {0: 'go', 10: 'jail', 20: 'parking', 30: 'to_jail'}[index]
    if kind == 'utility':
        return 'bulb' if index == 12 else 'tap'
    if kind == 'tax':
        return 'tax'
    return kind if kind in ('station', 'chance', 'chest') else None


def draw_icon(target, kind, rect):
    """Draw a small, consistently weighted icon inside the supplied rectangle."""
    rect = pygame.Rect(rect)
    image = pygame.Surface((64, 64), pygame.SRCALPHA)
    ink = (44, 64, 67)
    red = (174, 67, 61)
    gold = (164, 115, 40)
    # Coordinate helpers keep the primitive descriptions readable for learners.
    def line(points, color=ink, width=4):
        """Join points on the icon's local 64-by-64 drawing surface."""
        pygame.draw.lines(image, color, False, points, width)

    if kind == 'go':
        # GO is at bottom-right; play proceeds left towards Old Kent Road.
        line([(10, 33), (56, 33)], red, 8)
        pygame.draw.polygon(image, red, [(10, 33), (27, 16), (27, 50)])
    elif kind == 'chance':
        pygame.draw.arc(image, gold, (16, 8, 32, 30), -.5, 3.5, 7)
        line([(44, 29), (32, 39), (32, 44)], gold, 6)
        pygame.draw.circle(image, gold, (32, 55), 4)
    elif kind == 'chest':
        pygame.draw.rect(image, gold, (8, 23, 48, 31), border_radius=4)
        pygame.draw.arc(image, ink, (8, 8, 48, 35), 0, 3.15, 4)
        line([(8, 32), (56, 32)])
        pygame.draw.rect(image, ink, (29, 28, 7, 13), border_radius=2)
    elif kind == 'station':
        pygame.draw.rect(image, ink, (11, 27, 42, 22), border_radius=3)
        pygame.draw.rect(image, ink, (33, 14, 19, 22), border_radius=2)
        pygame.draw.rect(image, ink, (15, 17, 8, 14))
        pygame.draw.rect(image, (235, 231, 215), (38, 19, 9, 9))
        for x in (20, 43):
            pygame.draw.circle(image, ink, (x, 51), 8)
            pygame.draw.circle(image, (235, 231, 215), (x, 51), 3)
        line([(8, 60), (57, 60)], ink, 3)
    elif kind == 'bulb':
        pygame.draw.circle(image, gold, (32, 24), 17, 4)
        line([(21, 36), (24, 47), (40, 47), (43, 36)], gold)
        line([(24, 53), (40, 53)])
        line([(28, 59), (36, 59)])
        for a, b in [((32, 0), (32, 4)), ((4, 24), (9, 24)), ((55, 24), (60, 24))]:
            line([a, b], gold, 3)
    elif kind == 'tap':
        line([(10, 18), (41, 18), (41, 30), (55, 30), (55, 40)], ink, 8)
        line([(24, 8), (24, 26)])
        line([(14, 8), (34, 8)])
        pygame.draw.polygon(image, (55, 128, 157), [(53, 44), (46, 56), (60, 56)])
        pygame.draw.circle(image, (55, 128, 157), (53, 56), 7)
    elif kind in ('jail', 'to_jail'):
        pygame.draw.rect(image, ink, (10, 8, 44, 49), 4, border_radius=3)
        for x in (21, 32, 43):
            line([(x, 12), (x, 54)], ink, 3)
        if kind == 'to_jail':
            pygame.draw.polygon(image, red, [(4, 34), (36, 34), (36, 24), (57, 42), (36, 60), (36, 49), (4, 49)])
    elif kind == 'parking':
        pygame.draw.rect(image, red, (9, 25, 46, 23), border_radius=6)
        pygame.draw.polygon(image, red, [(17, 26), (23, 13), (43, 13), (51, 26)])
        pygame.draw.polygon(image, (235, 231, 215), [(23, 24), (27, 17), (39, 17), (44, 24)])
        for x in (19, 46):
            pygame.draw.circle(image, ink, (x, 48), 7)
    elif kind == 'tax':
        pygame.draw.polygon(image, gold, [(32, 7), (52, 26), (32, 56), (12, 26)], 4)
        line([(12, 26), (52, 26)], gold, 3)
        line([(23, 12), (26, 26), (32, 56), (38, 26), (41, 12)], gold, 2)
    target.blit(pygame.transform.smoothscale(image, rect.size), rect)
