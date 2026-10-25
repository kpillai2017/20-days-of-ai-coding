"""Original piece-specific choreography, independent of Pygame and chess rules.

All timing comes from elapsed time, never frame counts. Shared poses work in
both views, so switching views mid-move never restarts or commits a chess move.
"""

import math

# One recipe per ATTACKER type: (caption, seconds, synthesised sound key).
STYLES = {
    "p": ("Shield bash", 1.70, "bash"),
    "n": ("Mounted charge", 1.85, "charge"),
    "b": ("Staff spell", 1.85, "spell"),
    "r": ("Siege ram", 1.75, "rumble"),
    "q": ("Royal lightning", 1.95, "lightning"),
    "k": ("Sword salute", 1.85, "sword"),
}
# Impact is a fraction of the capture duration, not a fixed frame number.
IMPACT = 0.60


def pose(animation):
    """Return presentation values only; this function cannot change the board."""
    # Normalise elapsed seconds into a clamped 0..1 fraction.
    t = max(0.0, min(1.0, animation["time"] / animation["duration"]))
    move = animation["move"]
    kind = animation["piece"].lower()
    capture = animation["captured"] != "."
    # Captures stop SHORT of the victim during the wind-up. Impact precedes
    # moving onto its square, unlike sliding two sculptures through each other.
    if capture:
        if t < 0.40:
            progress = 0.72 * smooth(t / 0.40)
        elif t < 0.75:
            progress = 0.72
        else:
            progress = 0.72 + 0.28 * smooth((t - 0.75) / 0.25)
        attack = math.sin(max(0, min(1, (t - 0.40) / 0.30)) * math.pi)
    else:
        progress = smooth(t)
        attack = 0.0
    # A line segment interpolates the ground position; lift adds visual height.
    start_f, start_r = move.from_sq % 8, move.from_sq // 8
    dx, dy = move.to_sq % 8 - start_f, move.to_sq // 8 - start_r
    # Sinusoidal stride creates repeatable bobbing without storing joint history.
    stride = math.sin(progress * math.pi * (6 if kind == "p" else 4))
    lift = abs(stride) * 0.055 if kind in "pbqk" else 0
    if kind == "n":
        lift = math.sin(progress * math.pi) * 0.85
    if kind == "r":
        lift = abs(stride) * 0.025
    recoil = -0.12 * attack if kind in "bq" else 0.13 * attack
    # Divide by distance for a unit direction; the fallback prevents zero division.
    length = math.hypot(dx, dy) or 1
    fall = max(0, min(1, (t - IMPACT) / 0.25)) if capture else 0
    # The renderer consumes this pose; no board mutation is possible here.
    return {
        "t": t,
        "progress": progress,
        "file": start_f + dx * progress + dx / length * recoil,
        "rank": start_r + dy * progress + dy / length * recoil,
        "lift": lift,
        "attack": attack,
        "facing": math.atan2(dy, dx),
        "victim_scale": 1 - fall * 0.93,
        "victim_lean": fall * 1.25,
        "victim_visible": t < 0.88,
        "effect": capture and 0.45 < t < 0.88,
        "phase": (
            "Approach"
            if t < 0.40
            else "Wind-up" if t < IMPACT else "Impact" if t < 0.75 else "Recover"
        ),
    }


def smooth(t):
    """Clamp a fraction and ease its endpoints with smoothstep, t²(3−2t)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
