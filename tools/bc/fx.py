"""Particle textures + particle effect definitions."""
from __future__ import annotations

import math

import numpy as np

from . import tex
from .out import RP, write_json, write_png

T = 'textures/particle/bc/'


# ======================================================================================
# textures
# ======================================================================================
def _radial(n, power=2.0):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (n / 2)
    return np.clip(1 - d, 0, 1) ** power


def tex_glow(n=32):
    a = tex.new(n, n, tex.rgb('ffffff'))
    a[..., 3] = _radial(n, 1.8) * 255
    return a


def tex_spark(n=32):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    dx, dy = np.abs(xx - c) / (n / 2), np.abs(yy - c) / (n / 2)
    star = np.clip(1 - (dx * 6 + 0.0) - dy, 0, 1) + np.clip(1 - (dy * 6) - dx, 0, 1)
    core = _radial(n, 3) * 1.2
    a = tex.new(n, n, tex.rgb('ffffff'))
    a[..., 3] = np.clip(star + core, 0, 1) * 255
    return a


def tex_circle(n=128):
    a = tex.rune_ring(n, n, (255, 255, 255, 255), 77, ss=4, thickness=1.2, rings=2, glyphs=16)
    inner = tex.draw_layer(n, n, lambda d, s: tex.clover_shape(d, n * s / 2, n * s / 2, n * s * 0.12, 4, (255, 255, 255, 255), stem=False), 4)
    tex.alpha_over(a, inner)
    return tex.glow(a, 1.5, 0.6)


def tex_ring(n=64):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2
    d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (n / 2)
    v = np.exp(-((d - 0.88) ** 2) / 0.004) + np.exp(-((d - 0.8) ** 2) / 0.02) * 0.35
    a = tex.new(n, n, tex.rgb('ffffff'))
    a[..., 3] = np.clip(v, 0, 1) * 255
    return a


def tex_flipbook(kind, n=32, frames=4, seed=1):
    a = tex.new(n * frames, n)
    rng = np.random.default_rng(seed)
    for f in range(frames):
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        c = (n - 1) / 2
        if kind == 'flame':
            # teardrop flame that shrinks over frames
            sc = 1.0 - f * 0.18
            nx = (xx - c) / (n * 0.32 * sc)
            ny = (yy - n * 0.62) / (n * 0.42 * sc)
            body = 1 - (nx ** 2 + np.where(ny < 0, (ny * 0.55) ** 2, ny ** 2))
            body += tex.value_noise(n, n, 3, seed + f) * 0.35
            v = np.clip(body, 0, 1)
            col = tex.smooth_ramp(tex.ramp('ff8a2a', 'ffd36a', 'fff7d0', 'ffffff'), v)
        else:  # smoke
            sc = 0.7 + f * 0.12
            d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (n * 0.45 * sc)
            v = np.clip(1 - d + tex.value_noise(n, n, 4, seed + f) * 0.45, 0, 1) * (1 - f * 0.15)
            col = tex.smooth_ramp(tex.ramp('9a9a9a', 'd8d8d8', 'ffffff'), v)
        layer = col.copy()
        layer[..., 3] = (np.clip(v * 1.6, 0, 1) ** 1.2) * 255
        a[f * n:(f + 1) * n] = layer
    return a


def tex_bolt(w=32, h=128, seed=4):
    rng = np.random.default_rng(seed)

    def fn(d, s):
        x = w * s / 2
        pts = [(x, 0)]
        for i in range(1, 12):
            x = w * s / 2 + rng.uniform(-w * s * 0.3, w * s * 0.3)
            pts.append((x, h * s * i / 11))
        d.line(pts, fill=(255, 255, 255, 255), width=int(2.2 * s), joint='curve')
        # branches
        for _ in range(3):
            i = int(rng.integers(2, 9))
            bx, by = pts[i]
            d.line([(bx, by), (bx + rng.uniform(-w * s * 0.4, w * s * 0.4), by + h * s * 0.12)], fill=(255, 255, 255, 220), width=int(1.2 * s))
    a = tex.draw_layer(h, w, fn, 4)
    return tex.glow(a, 2.0, 0.9)


def tex_slash(w=64, h=32):
    def fn(d, s):
        for k, (wid, alpha) in enumerate(((8, 90), (5, 170), (2.5, 255))):
            d.arc([w * s * 0.05, h * s * 0.1, w * s * 0.95, h * s * 1.9], 200, 340, fill=(255, 255, 255, alpha), width=int(wid * s))
    return tex.draw_layer(h, w, fn, 4)


def tex_swirl(n=32):
    def fn(d, s):
        d.arc([n * s * 0.1, n * s * 0.1, n * s * 0.9, n * s * 0.9], 20, 250, fill=(255, 255, 255, 255), width=int(2 * s))
        d.arc([n * s * 0.3, n * s * 0.3, n * s * 0.7, n * s * 0.7], 200, 400, fill=(255, 255, 255, 160), width=int(1.4 * s))
    return tex.draw_layer(n, n, fn, 4)


def tex_small(kind):
    n = 16

    def fn(d, s):
        c = n * s / 2
        if kind == 'shard':
            d.polygon([(c, 1 * s), (c + 3 * s, c), (c, n * s - 1 * s), (c - 3 * s, c)], fill=(255, 255, 255, 255))
        elif kind == 'bubble':
            d.ellipse([2 * s, 2 * s, n * s - 2 * s, n * s - 2 * s], outline=(255, 255, 255, 255), width=int(1.4 * s))
            d.ellipse([5 * s, 4 * s, 7 * s, 6 * s], fill=(255, 255, 255, 255))
        elif kind == 'snow':
            for k in range(3):
                ang = k * math.pi / 3
                dx, dy = math.cos(ang) * (c - s), math.sin(ang) * (c - s)
                d.line([(c - dx, c - dy), (c + dx, c + dy)], fill=(255, 255, 255, 255), width=int(1.3 * s))
        elif kind == 'drop':
            d.ellipse([4 * s, 6 * s, 12 * s, 14 * s], fill=(255, 255, 255, 255))
            d.polygon([(8 * s, 1 * s), (11.5 * s, 9 * s), (4.5 * s, 9 * s)], fill=(255, 255, 255, 255))
        elif kind == 'clover':
            tex.clover_shape(d, c, c - s, 6 * s, 3, (90, 200, 90, 255), stem=True)
        elif kind == 'plus':
            d.rectangle([6 * s, 2 * s, 10 * s, 14 * s], fill=(255, 255, 255, 255))
            d.rectangle([2 * s, 6 * s, 14 * s, 10 * s], fill=(255, 255, 255, 255))
    a = tex.draw_layer(n, n, fn, 4)
    if kind == 'clover':
        a[..., :3] = np.where(a[..., 3:4] > 0, a[..., :3], 0)
        tex.outline(a, tex.rgb('0b2412'))
    return a


def gen_textures():
    write_png(RP, T + 'glow.png', tex_glow())
    write_png(RP, T + 'spark.png', tex_spark())
    write_png(RP, T + 'circle.png', tex_circle())
    write_png(RP, T + 'ring.png', tex_ring())
    write_png(RP, T + 'flame.png', tex_flipbook('flame'))
    write_png(RP, T + 'smoke.png', tex_flipbook('smoke', seed=9))
    write_png(RP, T + 'bolt.png', tex_bolt())
    write_png(RP, T + 'slash.png', tex_slash())
    write_png(RP, T + 'swirl.png', tex_swirl())
    for k in ('shard', 'bubble', 'snow', 'drop', 'clover', 'plus'):
        write_png(RP, T + f'{k}.png', tex_small(k))


# ======================================================================================
# particle definitions
# ======================================================================================
def hexrgb(h):
    h = h.lstrip('#')
    return [round(int(h[i:i + 2], 16) / 255, 3) for i in (0, 2, 4)]


def uv(texture, w, h, flip=None):
    if flip:
        frames, fps, stretch = flip
        return {'texture_width': w, 'texture_height': h * frames,
                'flipbook': {'base_UV': [0, 0], 'size_UV': [w, h], 'step_UV': [0, h], 'frames_per_second': fps,
                             'max_frame': frames, 'stretch_to_lifetime': stretch, 'loop': not stretch}}
    return {'texture_width': w, 'texture_height': h, 'uv': [0, 0], 'uv_size': [w, h]}


SIZES = {'glow': (32, 32), 'spark': (32, 32), 'circle': (128, 128), 'ring': (64, 64), 'flame': (32, 32), 'smoke': (32, 32),
         'bolt': (32, 128), 'slash': (64, 32), 'swirl': (32, 32), 'shard': (16, 16), 'bubble': (16, 16), 'snow': (16, 16),
         'drop': (16, 16), 'clover': (16, 16), 'plus': (16, 16)}


def P(ident, texture, material, comps):
    return ident, {
        'format_version': '1.10.0',
        'particle_effect': {
            'description': {'identifier': ident, 'basic_render_parameters': {'material': material, 'texture': T + texture}},
            'components': comps,
        },
    }


def billboard(texture, size, mode='rotate_xyz', flip=None, direction=None):
    w, h = SIZES[texture]
    b = {'size': size, 'facing_camera_mode': mode, 'uv': uv(texture, w, h, flip)}
    if direction:
        b['direction'] = {'mode': 'custom', 'custom_direction': direction}
    return b


def color_var(alpha='1.0', default=('1.0', '1.0', '1.0'), boost=1.0):
    r, g, b = default
    return {'color': [f'(v.color.r ?? {r}) * {boost}', f'(v.color.g ?? {g}) * {boost}', f'(v.color.b ?? {b}) * {boost}', alpha]}


FADE = 'math.clamp(v.particle_age * 8.0, 0.0, 1.0) * math.clamp((v.particle_lifetime - v.particle_age) * 4.0, 0.0, 1.0)'
FADE_OUT = '1.0 - v.particle_age / v.particle_lifetime'


def argb(h):
    """'#AARRGGBB' -> [r, g, b, a] floats (unambiguous for the engine)."""
    h = h.lstrip('#')
    a, r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4, 6))
    return [round(r, 3), round(g, 3), round(b, 3), round(a, 3)]


def gradient(stops):
    return {'color': {'gradient': {k: argb(v) for k, v in stops.items()}, 'interpolant': 'v.particle_age / v.particle_lifetime'}}


def once(n):
    return {'minecraft:emitter_rate_instant': {'num_particles': n}, 'minecraft:emitter_lifetime_once': {'active_time': 0.05}}


def steady(rate, mx, forever=True, active=1.0):
    d = {'minecraft:emitter_rate_steady': {'spawn_rate': rate, 'max_particles': mx}}
    if forever:
        d['minecraft:emitter_lifetime_expression'] = {'activation_expression': 1, 'expiration_expression': 0}
    else:
        d['minecraft:emitter_lifetime_once'] = {'active_time': active}
    return d


TRAILS = {
    # name: (texture, material, colour stops, size, rate, lifetime, extras)
    'wind': ('swirl', 'particles_add', {'0.0': '#FFC9FFE0', '1.0': '#003FAA6A'}, 0.45, 40, 0.5, {'spin': 600}),
    'flame': ('flame', 'particles_add', {'0.0': '#FFFFE6A0', '0.4': '#FFFF8A2A', '1.0': '#00A01806'}, 0.45, 60, 0.45, {'flip': True, 'rise': 1.0}),
    'flame_big': ('flame', 'particles_add', {'0.0': '#FFFFF0B0', '0.4': '#FFFF7A1A', '1.0': '#00801004'}, 0.9, 90, 0.6, {'flip': True, 'rise': 1.5, 'radius': 0.6}),
    'water': ('drop', 'particles_add', {'0.0': '#FFC8ECFF', '1.0': '#002A62B6'}, 0.18, 40, 0.6, {'gravity': -9}),
    'water_big': ('bubble', 'particles_add', {'0.0': '#FFC8ECFF', '1.0': '#001F6FD0'}, 0.3, 70, 0.8, {'gravity': 1.5, 'radius': 0.7}),
    'lightning': ('spark', 'particles_add', {'0.0': '#FFFFFDE0', '0.5': '#FFFFE23D', '1.0': '#00B58300'}, 0.35, 70, 0.25, {'jitter': 4}),
    'light': ('spark', 'particles_add', {'0.0': '#FFFFFFFF', '1.0': '#00F2CD5A'}, 0.3, 50, 0.6, {}),
    'dark': ('smoke', 'particles_blend', {'0.0': '#E03B1860', '0.5': '#A0240F3A', '1.0': '#0005030A'}, 0.5, 50, 0.7, {'flip': True}),
    'ice': ('snow', 'particles_add', {'0.0': '#FFF2FDFF', '1.0': '#004FB0D8'}, 0.2, 40, 0.7, {'gravity': -3, 'spin': 200}),
    'anti': ('bolt', 'particles_blend', {'0.0': '#FF000000', '0.6': '#E0100808', '1.0': '#00000000'}, 0.5, 60, 0.18, {'stretch': 2.2}),
    'devil': ('smoke', 'particles_blend', {'0.0': '#F0300408', '0.5': '#B0120204', '1.0': '#00000000'}, 0.6, 50, 0.7, {'flip': True}),
}


def trail_particle(name, spec):
    texture, mat, stops, size, rate, life, ex = spec
    comps = steady(rate, int(rate * life * 2) + 10)
    comps['minecraft:emitter_local_space'] = {'position': False, 'rotation': False}
    comps['minecraft:emitter_shape_sphere'] = {'radius': ex.get('radius', 0.25), 'direction': 'outwards'}
    comps['minecraft:particle_lifetime_expression'] = {'max_lifetime': f'{life} * (0.7 + v.particle_random_1 * 0.6)'}
    comps['minecraft:particle_initial_speed'] = ex.get('jitter', 0.4)
    accel = [0, ex.get('rise', 0) + ex.get('gravity', 0), 0]
    comps['minecraft:particle_motion_dynamic'] = {'linear_acceleration': accel, 'linear_drag_coefficient': 2.0}
    if ex.get('spin'):
        comps['minecraft:particle_initial_spin'] = {'rotation': 'math.random(0, 360)', 'rotation_rate': ex['spin']}
    s = f'{size} * (1.0 - v.particle_age / v.particle_lifetime * 0.6)'
    sy = s if not ex.get('stretch') else f'{size} * {ex["stretch"]}'
    flip = (4, 8, True) if ex.get('flip') else None
    comps['minecraft:particle_appearance_billboard'] = billboard(texture, [s, sy], flip=flip)
    comps['minecraft:particle_appearance_tinting'] = gradient(stops)
    return P(f'bc:trail_{name}', texture, mat, comps)


def particles():
    out = []
    # ------------------------------------------------------------------ magic circles
    circle = {
        'minecraft:emitter_initialization': {'creation_expression': 'v.sz = v.size ?? 1.6;'},
        **once(1),
        'minecraft:emitter_shape_point': {},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 'v.life ?? 0.9'},
        'minecraft:particle_initial_spin': {'rotation': 0, 'rotation_rate': 120},
        'minecraft:particle_motion_dynamic': {},
        'minecraft:particle_appearance_billboard': billboard('circle', ['v.sz * (0.4 + 0.6 * math.min(v.particle_age * 7.0, 1.0))',
                                                                       'v.sz * (0.4 + 0.6 * math.min(v.particle_age * 7.0, 1.0))'], 'direction_z',
                                                             direction=['v.dir.x ?? 0', 'v.dir.y ?? 0', 'v.dir.z ?? 1']),
        'minecraft:particle_appearance_tinting': color_var(FADE),
    }
    out.append(P('bc:magic_circle', 'circle', 'particles_add', circle))
    ground = dict(circle)
    ground['minecraft:emitter_shape_point'] = {'offset': [0, 0.05, 0]}
    ground['minecraft:particle_appearance_billboard'] = billboard('circle', ['v.sz * (0.3 + 0.7 * math.min(v.particle_age * 4.0, 1.0))',
                                                                          'v.sz * (0.3 + 0.7 * math.min(v.particle_age * 4.0, 1.0))'], 'emitter_transform_xz')
    ground['minecraft:particle_initial_spin'] = {'rotation': 0, 'rotation_rate': 60}
    out.append(P('bc:magic_circle_ground', 'circle', 'particles_add', ground))
    dark_ground = dict(ground)
    dark_ground['minecraft:particle_appearance_tinting'] = color_var(FADE, ('0.05', '0.0', '0.02'))
    out.append(P('bc:magic_circle_dark', 'circle', 'particles_blend', dark_ground))
    warn = dict(ground)
    warn['minecraft:particle_appearance_tinting'] = {'color': ['1.0', '0.15', '0.1', f'({FADE}) * (0.6 + math.sin(v.particle_age * 1400.0) * 0.4)']}
    out.append(P('bc:warning_circle', 'circle', 'particles_add', warn))

    # ------------------------------------------------------------------ bursts
    def burst(ident, texture, material, n, speed, life, size, tint, gravity=0.0, drag=3.0, flip=None, radius=0.2, spin=0):
        c = {
            'minecraft:emitter_initialization': {'creation_expression': 'v.sc = v.scale ?? 1.0;'},
            **once(n),
            'minecraft:emitter_shape_sphere': {'radius': f'{radius} * v.sc', 'direction': 'outwards'},
            'minecraft:particle_lifetime_expression': {'max_lifetime': f'{life} * (0.6 + v.particle_random_1 * 0.8)'},
            'minecraft:particle_initial_speed': f'({speed}) * v.sc * (0.5 + v.particle_random_2)',
            'minecraft:particle_motion_dynamic': {'linear_acceleration': [0, gravity, 0], 'linear_drag_coefficient': drag},
            'minecraft:particle_appearance_billboard': billboard(texture, [f'{size} * v.sc * (1.0 - v.particle_age / v.particle_lifetime * 0.7)'] * 2, flip=flip),
            'minecraft:particle_appearance_tinting': tint,
        }
        if spin:
            c['minecraft:particle_initial_spin'] = {'rotation': 'math.random(0,360)', 'rotation_rate': spin}
        return P(ident, texture, material, c)

    out.append(burst('bc:burst', 'glow', 'particles_add', 30, 7, 0.6, 0.35, color_var(FADE_OUT)))
    out.append(burst('bc:burst_spark', 'spark', 'particles_add', 16, 10, 0.4, 0.5, color_var(FADE_OUT, boost=1.2), spin=300))
    out.append(burst('bc:burst_dark', 'smoke', 'particles_blend', 26, 5, 0.9, 0.9, color_var(f'0.9 * ({FADE_OUT})', ('0.05', '0.0', '0.05')), flip=(4, 6, True)))
    out.append(burst('bc:flame_burst', 'flame', 'particles_add', 40, 8, 0.7, 0.9,
                     gradient({'0.0': '#FFFFF0B0', '0.35': '#FFFF7A1A', '1.0': '#00601004'}), gravity=2, flip=(4, 8, True), radius=0.4))
    out.append(burst('bc:smoke_burst', 'smoke', 'particles_blend', 20, 3, 1.4, 1.2,
                     gradient({'0.0': '#B0303030', '1.0': '#00101010'}), gravity=1.2, flip=(4, 4, True), radius=0.6))
    out.append(burst('bc:water_splash', 'drop', 'particles_add', 40, 8, 0.9, 0.22,
                     gradient({'0.0': '#FFE0F4FF', '1.0': '#003C9CF0'}), gravity=-14, drag=1.0))
    out.append(burst('bc:ice_shatter', 'shard', 'particles_add', 28, 8, 1.0, 0.3,
                     gradient({'0.0': '#FFF2FDFF', '1.0': '#008AD8F0'}), gravity=-16, drag=0.8, spin=400))
    out.append(burst('bc:light_burst', 'spark', 'particles_add', 30, 9, 0.7, 0.55,
                     gradient({'0.0': '#FFFFFFFF', '0.5': '#FFFFE9A0', '1.0': '#00C99A2E'}), spin=200))
    out.append(burst('bc:anti_burst', 'bolt', 'particles_blend', 18, 6, 0.3, 0.8,
                     gradient({'0.0': '#FF000000', '0.7': '#C0200404', '1.0': '#00000000'})))
    out.append(burst('bc:anti_sparks', 'spark', 'particles_add', 14, 8, 0.35, 0.35,
                     gradient({'0.0': '#FFFF4A4A', '1.0': '#00600000'}), spin=500))
    out.append(burst('bc:clover_leaves', 'clover', 'particles_alpha', 24, 3, 2.2, 0.3,
                     {'color': [1, 1, 1, 1]}, gravity=-0.6, drag=1.5, spin=180, radius=0.6))
    out.append(burst('bc:heal', 'plus', 'particles_add', 16, 1.5, 1.2, 0.25,
                     gradient({'0.0': '#FFB8FFC8', '1.0': '#0030D070'}), gravity=1.5, drag=1.0, radius=0.8))

    # ------------------------------------------------------------------ rising auras / columns
    def column(ident, texture, material, rate, active, life, size, tint, radius, rise, flip=None, spin=0, n_max=200, local=False):
        c = {
            'minecraft:emitter_initialization': {'creation_expression': 'v.sc = v.scale ?? 1.0;'},
            **steady(rate, n_max, forever=False, active=active),
            'minecraft:emitter_shape_disc': {'radius': f'{radius} * v.sc', 'plane_normal': 'y', 'direction': [0, 1, 0]},
            'minecraft:particle_lifetime_expression': {'max_lifetime': f'{life} * (0.7 + v.particle_random_1 * 0.6)'},
            'minecraft:particle_initial_speed': f'{rise} * (0.6 + v.particle_random_2 * 0.8)',
            'minecraft:particle_motion_dynamic': {'linear_drag_coefficient': 0.8},
            'minecraft:particle_appearance_billboard': billboard(texture, [f'{size} * (1.0 - v.particle_age / v.particle_lifetime * 0.5)'] * 2, flip=flip),
            'minecraft:particle_appearance_tinting': tint,
        }
        if spin:
            c['minecraft:particle_initial_spin'] = {'rotation': 'math.random(0,360)', 'rotation_rate': spin}
        return P(ident, texture, material, c)

    out.append(column('bc:mana_aura', 'glow', 'particles_add', 40, 0.25, 0.9, 0.18, color_var(FADE), 0.6, 1.2))
    out.append(column('bc:flame_pillar', 'flame', 'particles_add', 220, 0.6, 0.8, 1.1,
                      gradient({'0.0': '#FFFFF0B0', '0.3': '#FFFF8A2A', '1.0': '#00701004'}), 0.8, 9, flip=(4, 8, True)))
    out.append(column('bc:level_up', 'spark', 'particles_add', 80, 0.8, 1.2, 0.3,
                      gradient({'0.0': '#FFFFFFFF', '0.5': '#FFFFE58A', '1.0': '#00D39A2C'}), 0.8, 3, spin=200))
    out.append(column('bc:black_aura', 'smoke', 'particles_blend', 60, 0.3, 0.8, 0.7,
                      gradient({'0.0': '#E0000000', '0.6': '#90100406', '1.0': '#00000000'}), 0.5, 2.2, flip=(4, 6, True)))
    out.append(column('bc:dark_mist', 'smoke', 'particles_blend', 70, 0.5, 1.4, 1.1,
                      gradient({'0.0': '#C0281040', '1.0': '#00080210'}), 1.0, 0.6, flip=(4, 4, True)))
    out.append(column('bc:snowstorm', 'snow', 'particles_add', 200, 1.0, 1.6, 0.22,
                      gradient({'0.0': '#FFFFFFFF', '1.0': '#008AD8F0'}), '(v.radius ?? 6.0)', 0.3, spin=300, n_max=400))

    # ------------------------------------------------------------------ shockwave ring
    out.append(P('bc:shockwave', 'ring', 'particles_add', {
        'minecraft:emitter_initialization': {'creation_expression': 'v.r = v.radius ?? 5.0;'},
        **once(1),
        'minecraft:emitter_shape_point': {'offset': [0, 0.2, 0]},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 0.55},
        'minecraft:particle_appearance_billboard': billboard('ring', ['v.r * 2.0 * math.sqrt(v.particle_age / v.particle_lifetime)'] * 2, 'emitter_transform_xz'),
        'minecraft:particle_appearance_tinting': color_var(FADE_OUT, boost=1.0),
    }))
    out.append(P('bc:shockwave_dark', 'ring', 'particles_blend', {
        'minecraft:emitter_initialization': {'creation_expression': 'v.r = v.radius ?? 5.0;'},
        **once(1),
        'minecraft:emitter_shape_point': {'offset': [0, 0.2, 0]},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 0.6},
        'minecraft:particle_appearance_billboard': billboard('ring', ['v.r * 2.0 * math.sqrt(v.particle_age / v.particle_lifetime)'] * 2, 'emitter_transform_xz'),
        'minecraft:particle_appearance_tinting': {'color': [0.02, 0.0, 0.0, FADE_OUT]},
    }))

    # ------------------------------------------------------------------ lightning bolts from the sky
    for ident, mat, tint in (('bc:lightning_bolt', 'particles_add', color_var('math.sin(v.particle_age * 3000.0) * 0.3 + 0.7', ('1.0', '0.95', '0.6'))),
                             ('bc:dark_lightning', 'particles_blend', {'color': [0.0, 0.0, 0.0, 'math.sin(v.particle_age * 3000.0) * 0.2 + 0.8']})):
        out.append(P(ident, 'bolt', mat, {
            **once(2),
            'minecraft:emitter_shape_point': {'offset': [0, 7, 0]},
            'minecraft:particle_lifetime_expression': {'max_lifetime': 0.3},
            'minecraft:particle_appearance_billboard': billboard('bolt', [1.8, 14], 'lookat_y'),
            'minecraft:particle_appearance_tinting': tint,
        }))

    # ------------------------------------------------------------------ beam dots & sparks (spawned in lines by script)
    out.append(P('bc:beam_dot', 'glow', 'particles_add', {
        **once(1),
        'minecraft:emitter_shape_point': {},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 'v.life ?? 0.35'},
        'minecraft:particle_appearance_billboard': billboard('glow', ['(v.size ?? 0.6) * (1.0 - v.particle_age / v.particle_lifetime * 0.6)'] * 2),
        'minecraft:particle_appearance_tinting': color_var(FADE_OUT, boost=1.0),
    }))
    out.append(P('bc:spark', 'spark', 'particles_add', {
        **once(2),
        'minecraft:emitter_shape_sphere': {'radius': 0.15, 'direction': 'outwards'},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 0.2},
        'minecraft:particle_initial_speed': 2,
        'minecraft:particle_initial_spin': {'rotation': 'math.random(0,360)', 'rotation_rate': 900},
        'minecraft:particle_motion_dynamic': {'linear_drag_coefficient': 4},
        'minecraft:particle_appearance_billboard': billboard('spark', [0.35, 0.35]),
        'minecraft:particle_appearance_tinting': color_var(FADE_OUT, ('1.0', '0.95', '0.5')),
    }))
    out.append(P('bc:anti_crackle', 'bolt', 'particles_blend', {
        **once(3),
        'minecraft:emitter_shape_sphere': {'radius': '(v.radius ?? 0.9)', 'surface_only': True, 'direction': 'outwards'},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 0.18},
        'minecraft:particle_initial_spin': {'rotation': 'math.random(0,360)', 'rotation_rate': 0},
        'minecraft:particle_appearance_billboard': billboard('bolt', [0.35, 1.1]),
        'minecraft:particle_appearance_tinting': {'color': [0.0, 0.0, 0.0, 0.95]},
    }))
    out.append(P('bc:slash_fx', 'slash', 'particles_blend', {
        **once(1),
        'minecraft:emitter_shape_point': {},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 0.25},
        'minecraft:particle_initial_spin': {'rotation': 'v.rot ?? math.random(-40, 40)', 'rotation_rate': 0},
        'minecraft:particle_appearance_billboard': billboard('slash', ['(v.size ?? 3.0) * (0.8 + v.particle_age * 2.0)', '(v.size ?? 3.0) * 0.5 * (0.8 + v.particle_age * 2.0)']),
        'minecraft:particle_appearance_tinting': color_var(FADE_OUT, ('0.0', '0.0', '0.0')),
    }))
    out.append(P('bc:wind_burst', 'swirl', 'particles_add', {
        'minecraft:emitter_initialization': {'creation_expression': 'v.sc = v.scale ?? 1.0;'},
        **once(40),
        'minecraft:emitter_shape_disc': {'radius': '0.6 * v.sc', 'plane_normal': 'y', 'direction': 'outwards'},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 0.7},
        'minecraft:particle_initial_speed': '12 * v.sc',
        'minecraft:particle_initial_spin': {'rotation': 'math.random(0,360)', 'rotation_rate': 720},
        'minecraft:particle_motion_dynamic': {'linear_acceleration': [0, 2, 0], 'linear_drag_coefficient': 3},
        'minecraft:particle_appearance_billboard': billboard('swirl', [0.9, 0.9]),
        'minecraft:particle_appearance_tinting': gradient({'0.0': '#FFE0FFEC', '1.0': '#004FC884'}),
    }))

    # ------------------------------------------------------------------ entity-bound looping effects
    for name, spec in TRAILS.items():
        out.append(trail_particle(name, spec))
    out.append(P('bc:tornado_fx', 'swirl', 'particles_add', {
        **steady(90, 220),
        'minecraft:emitter_local_space': {'position': True, 'rotation': False},
        'minecraft:emitter_shape_disc': {'radius': 1.2, 'plane_normal': 'y', 'direction': [0, 1, 0]},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 1.2},
        'minecraft:particle_initial_speed': 3.0,
        'minecraft:particle_motion_parametric': {'relative_position': [
            'math.cos(v.particle_age * 600.0 + v.particle_random_1 * 360.0) * (0.8 + v.particle_age * 1.8)',
            'v.particle_age * 3.0',
            'math.sin(v.particle_age * 600.0 + v.particle_random_1 * 360.0) * (0.8 + v.particle_age * 1.8)']},
        'minecraft:particle_initial_spin': {'rotation': 'math.random(0,360)', 'rotation_rate': 600},
        'minecraft:particle_appearance_billboard': billboard('swirl', [0.7, 0.7]),
        'minecraft:particle_appearance_tinting': gradient({'0.0': '#FFF0FFF4', '1.0': '#003FAA6A'}),
    }))
    out.append(P('bc:black_hole_fx', 'glow', 'particles_add', {
        **steady(80, 200),
        'minecraft:emitter_local_space': {'position': True, 'rotation': False},
        'minecraft:emitter_shape_sphere': {'offset': [0, 0.75, 0], 'radius': 4.0, 'surface_only': True, 'direction': 'inwards'},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 0.8},
        'minecraft:particle_initial_speed': 5.0,
        'minecraft:particle_motion_dynamic': {'linear_drag_coefficient': 0.5},
        'minecraft:particle_appearance_billboard': billboard('glow', [0.25, 0.25]),
        'minecraft:particle_appearance_tinting': gradient({'0.0': '#008A46C8', '0.3': '#FFC08CFF', '1.0': '#FF240F3A'}),
    }))
    out.append(P('bc:snow_fall', 'snow', 'particles_add', {
        **steady(25, 60),
        'minecraft:emitter_local_space': {'position': True, 'rotation': False},
        'minecraft:emitter_shape_disc': {'offset': [0, 1.8, 0], 'radius': 1.2, 'plane_normal': 'y'},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 1.4},
        'minecraft:particle_initial_speed': 0.3,
        'minecraft:particle_motion_dynamic': {'linear_acceleration': [0, -1.2, 0]},
        'minecraft:particle_initial_spin': {'rotation': 'math.random(0,360)', 'rotation_rate': 90},
        'minecraft:particle_appearance_billboard': billboard('snow', [0.16, 0.16]),
        'minecraft:particle_appearance_tinting': {'color': [0.85, 0.97, 1.0, FADE]},
    }))
    out.append(P('bc:disciple_aura', 'smoke', 'particles_blend', {
        **steady(6, 20),
        'minecraft:emitter_local_space': {'position': False, 'rotation': False},
        'minecraft:emitter_shape_disc': {'offset': [0, 0.1, 0], 'radius': 0.5, 'plane_normal': 'y'},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 1.6},
        'minecraft:particle_initial_speed': 0.4,
        'minecraft:particle_motion_dynamic': {'linear_acceleration': [0, 0.3, 0], 'linear_drag_coefficient': 1},
        'minecraft:particle_appearance_billboard': billboard('smoke', [0.6, 0.6], flip=(4, 3, True)),
        'minecraft:particle_appearance_tinting': gradient({'0.0': '#00281040', '0.3': '#90281040', '1.0': '#00080210'}),
    }))
    out.append(P('bc:devil_aura', 'smoke', 'particles_blend', {
        **steady(24, 80),
        'minecraft:emitter_local_space': {'position': False, 'rotation': False},
        'minecraft:emitter_shape_box': {'offset': [0, 1.8, 0], 'half_dimensions': [0.8, 1.4, 0.6], 'direction': [0, 1, 0]},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 1.2},
        'minecraft:particle_initial_speed': 0.6,
        'minecraft:particle_motion_dynamic': {'linear_acceleration': [0, 0.8, 0], 'linear_drag_coefficient': 1},
        'minecraft:particle_appearance_billboard': billboard('smoke', [0.8, 0.8], flip=(4, 4, True)),
        'minecraft:particle_appearance_tinting': gradient({'0.0': '#00300408', '0.3': '#C0300408', '1.0': '#00000000'}),
    }))
    return out


def sea_particles():
    out = []
    TRAILS_SEA = {
        'dust': ('smoke', 'particles_blend', {'0.0': '#A0857A6A', '1.0': '#00403A30'}, 0.45, 40, 0.6, {'flip': True}),
    }
    for name, spec in TRAILS_SEA.items():
        out.append(trail_particle(name, spec))

    def oneshot(ident, texture, material, n, speed, life, size, tint, gravity=0.0, drag=2.0, spin=0, radius=0.3, collide=False, flip=None):
        c = {
            'minecraft:emitter_initialization': {'creation_expression': 'v.sc = v.scale ?? 1.0;'},
            **once(n),
            'minecraft:emitter_shape_sphere': {'radius': f'{radius} * v.sc', 'direction': 'outwards'},
            'minecraft:particle_lifetime_expression': {'max_lifetime': f'{life} * (0.6 + v.particle_random_1 * 0.8)'},
            'minecraft:particle_initial_speed': f'({speed}) * v.sc * (0.5 + v.particle_random_2)',
            'minecraft:particle_motion_dynamic': {'linear_acceleration': [0, gravity, 0], 'linear_drag_coefficient': drag},
            'minecraft:particle_appearance_billboard': billboard(texture, [f'{size} * (1.0 - v.particle_age / v.particle_lifetime * 0.5)'] * 2, flip=flip),
            'minecraft:particle_appearance_tinting': tint,
        }
        if spin:
            c['minecraft:particle_initial_spin'] = {'rotation': 'math.random(0,360)', 'rotation_rate': spin}
        if collide:
            c['minecraft:particle_motion_collision'] = {'collision_radius': 0.1, 'coefficient_of_restitution': 0.3, 'collision_drag': 4}
            c['minecraft:particle_appearance_lighting'] = {}
        return P(ident, texture, material, c)

    out.append(oneshot('bc:rock_debris', 'shard', 'particles_alpha', 26, 7, 1.4, 0.32,
                       gradient({'0.0': '#FF7E766A', '1.0': '#FF3D3933'}), gravity=-18, drag=0.6, spin=360, collide=True))
    out.append(oneshot('bc:leaf_burst', 'clover', 'particles_alpha', 22, 4, 2.0, 0.3, {'color': [1, 1, 1, 1]}, gravity=-1.2, drag=1.6, spin=200, radius=0.8))
    out.append(oneshot('bc:shard_burst', 'shard', 'particles_add', 24, 9, 0.8, 0.3, color_var(FADE_OUT), gravity=-10, drag=1.0, spin=500))
    out.append(oneshot('bc:will_spark', 'spark', 'particles_add', 18, 6, 0.4, 0.45,
                       gradient({'0.0': '#FFE8D8FF', '0.4': '#FF8A46FF', '1.0': '#00240F3A'}), spin=600))
    out.append(P('bc:ship_wake', 'bubble', 'particles_alpha', {
        **steady(14, 40),
        'minecraft:emitter_local_space': {'position': False, 'rotation': False},
        'minecraft:emitter_shape_box': {'offset': [0, 0.35, 0], 'half_dimensions': [1.4, 0.05, 1.8], 'surface_only': True, 'direction': 'outwards'},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 1.4},
        'minecraft:particle_initial_speed': 0.4,
        'minecraft:particle_motion_dynamic': {'linear_drag_coefficient': 2},
        'minecraft:particle_appearance_billboard': billboard('bubble', ['0.3 + v.particle_age * 0.2'] * 2, 'emitter_transform_xz'),
        'minecraft:particle_appearance_tinting': {'color': [0.92, 0.97, 1.0, FADE_OUT]},
    }))
    out.append(P('bc:leviathan_bubbles', 'bubble', 'particles_add', {
        **steady(20, 60),
        'minecraft:emitter_local_space': {'position': False, 'rotation': False},
        'minecraft:emitter_shape_box': {'offset': [0, 1.5, 0], 'half_dimensions': [1.5, 1.0, 3.0], 'direction': [0, 1, 0]},
        'minecraft:particle_lifetime_expression': {'max_lifetime': 1.6},
        'minecraft:particle_initial_speed': 1.2,
        'minecraft:particle_motion_dynamic': {'linear_acceleration': [0, 1.5, 0], 'linear_drag_coefficient': 1.5},
        'minecraft:particle_appearance_billboard': billboard('bubble', [0.22, 0.22]),
        'minecraft:particle_appearance_tinting': {'color': [0.6, 1.0, 0.95, FADE_OUT]},
    }))
    return out


def build():
    gen_textures()
    for ident, data in particles() + sea_particles():
        write_json(RP, f"particles/bc/{ident.split(':')[1]}.particle.json", data)
