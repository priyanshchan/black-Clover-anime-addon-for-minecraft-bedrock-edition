"""v0.7.5 icons: potions, elixirs, the smoke bomb and the spell scroll. All designs are original."""
from __future__ import annotations

import numpy as np

from .. import tex
from ..tex import rgb


def _icon(fn, outline='0a0a0f'):
    a = tex.draw_layer(32, 32, fn, 4)
    a[..., 3] = np.where(a[..., 3] > 110, 255, 0)
    tex.outline(a, rgb(outline))
    return a


def _bottle(liquid, glow, big=False, cork=(150, 100, 50, 255)):
    def fn(d, s):
        w = 11 if big else 9
        d.rectangle([(16 - 2.5) * s, 3 * s, (16 + 2.5) * s, 7 * s], fill=cork)
        d.rectangle([(16 - 3) * s, 7 * s, (16 + 3) * s, 11 * s], fill=(200, 220, 230, 255))
        d.ellipse([(16 - w) * s, 10 * s, (16 + w) * s, 30 * s], fill=(200, 220, 230, 255))
        d.ellipse([(16 - w + 1.5) * s, 14 * s, (16 + w - 1.5) * s, 28.5 * s], fill=liquid)
        d.ellipse([(16 - w + 3) * s, 15 * s, (16 - w + 7) * s, 19 * s], fill=glow)
    return fn


def v75_icons():
    def smoke(d, s):
        d.ellipse([7 * s, 10 * s, 25 * s, 28 * s], fill=(50, 50, 58, 255))
        d.rectangle([14 * s, 5 * s, 18 * s, 11 * s], fill=(120, 90, 50, 255))
        d.line([(16 * s, 5 * s), (20 * s, 1.5 * s)], fill=(230, 160, 60, 255), width=int(1.4 * s))
        d.ellipse([10 * s, 14 * s, 15 * s, 19 * s], fill=(110, 110, 120, 255))

    def scroll(d, s):
        d.rectangle([7 * s, 6 * s, 25 * s, 26 * s], fill=(232, 216, 170, 255))
        d.ellipse([4 * s, 3 * s, 10 * s, 9 * s], fill=(200, 170, 110, 255))
        d.ellipse([22 * s, 23 * s, 28 * s, 29 * s], fill=(200, 170, 110, 255))
        for y in (11, 15, 19):
            d.line([(10 * s, y * s), (22 * s, y * s)], fill=(120, 60, 160, 255), width=int(1.2 * s))
        d.ellipse([18 * s, 19 * s, 24 * s, 25 * s], fill=(200, 40, 40, 255))
    return {
        'mana_potion': _icon(_bottle((60, 140, 255, 255), (200, 230, 255, 255))),
        'greater_mana_potion': _icon(_bottle((30, 60, 200, 255), (160, 200, 255, 255), big=True, cork=(220, 180, 60, 255))),
        'elixir_iron': _icon(_bottle((150, 150, 165, 255), (230, 230, 240, 255))),
        'elixir_haste': _icon(_bottle((80, 210, 90, 255), (210, 255, 200, 255))),
        'smoke_bomb': _icon(smoke),
        'spell_scroll': _icon(scroll),
    }
