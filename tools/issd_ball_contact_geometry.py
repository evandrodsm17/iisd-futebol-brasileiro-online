"""Isolated 16-bit model of 84:E8B0; not the browser physics engine."""

def _axis(actor, ball, center, width):
    total = actor + center
    carry = int(total > 0xffff)
    value = total & 0xffff
    difference = value - ball - (1 - carry)
    carry = int(difference >= 0)
    value = difference & 0xffff
    return int(value >= width), carry


def contact_carry(actor_x, actor_y, actor_z, ball_x, ball_y, ball_z,
                  field_3e, field_68, global_11fa, actor_team, reference_team):
    """Return the original routine's carry (0 means accepted). All values are u16."""
    values = (actor_x, actor_y, actor_z, ball_x, ball_y, ball_z, field_3e,
              field_68, global_11fa, actor_team, reference_team)
    if any(not isinstance(v, int) or not 0 <= v <= 0xffff for v in values):
        raise ValueError('All inputs must be 16-bit unsigned words')
    if global_11fa & 0x8000 or field_3e:
        return 1
    if field_68 or actor_team == reference_team:
        if (actor_z - ball_z) & 0xffff >= 0x18:
            return 1
        cx, cy, wx, wy = 12, 8, 24, 16
    else:
        dz = (ball_z - actor_z) & 0xffff
        if dz and (not dz & 0x8000 or dz < 0xffd0):
            return 1
        cx, cy, wx, wy = 14, 10, 28, 20
    if _axis(actor_x, ball_x, cx, wx)[0]:
        return 1
    return _axis(actor_y, ball_y, cy, wy)[0]
