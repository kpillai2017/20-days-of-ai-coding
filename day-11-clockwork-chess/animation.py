"""Original piece-specific choreography, independent of Pygame and chess rules.

All timing comes from elapsed time, never frame counts. Shared poses work in
both views, so switching views mid-move never restarts or commits a chess move.
"""
import math

STYLES = {
    'p': ('Shield bash', 1.70, 'bash'),
    'n': ('Mounted charge', 1.85, 'charge'),
    'b': ('Staff spell', 1.85, 'spell'),
    'r': ('Siege ram', 1.75, 'rumble'),
    'q': ('Royal lightning', 1.95, 'lightning'),
    'k': ('Sword salute', 1.85, 'sword'),
}
IMPACT = .60


def pose(animation):
    """Return presentation values only; this function cannot change the board."""
    t = max(0., min(1., animation['time'] / animation['duration']))
    move = animation['move']
    kind = animation['piece'].lower()
    capture = animation['captured'] != '.'
    # Captures stop SHORT of the victim during the wind-up. Impact precedes
    # moving onto its square, unlike sliding two sculptures through each other.
    if capture:
        if t < .40:
            progress = .72 * smooth(t / .40)
        elif t < .75:
            progress = .72
        else:
            progress = .72 + .28 * smooth((t - .75) / .25)
        attack = math.sin(max(0, min(1, (t-.40)/.30)) * math.pi)
    else:
        progress = smooth(t)
        attack = 0.
    start_f, start_r = move.from_sq % 8, move.from_sq // 8
    dx, dy = move.to_sq % 8 - start_f, move.to_sq // 8 - start_r
    stride = math.sin(progress * math.pi * (6 if kind == 'p' else 4))
    lift = abs(stride)*.055 if kind in 'pbqk' else 0
    if kind == 'n': lift = math.sin(progress*math.pi)*.85
    if kind == 'r': lift = abs(stride)*.025
    recoil = (-.12*attack if kind in 'bq' else .13*attack)
    length = math.hypot(dx,dy) or 1
    fall = max(0,min(1,(t-IMPACT)/.25)) if capture else 0
    return {
        't':t, 'progress':progress,
        'file':start_f+dx*progress+dx/length*recoil,
        'rank':start_r+dy*progress+dy/length*recoil,
        'lift':lift, 'attack':attack,
        'facing':math.atan2(dy,dx),
        'victim_scale':1-fall*.93,
        'victim_lean':fall*1.25,
        'victim_visible':t < .88,
        'effect':capture and .45 < t < .88,
        'phase': 'Approach' if t < .40 else 'Wind-up' if t < IMPACT else 'Impact' if t < .75 else 'Recover',
    }


def smooth(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)
