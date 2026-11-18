"""Output helpers for writing pack files."""
from __future__ import annotations

import json
import os
import uuid

from . import tex

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BP = os.path.join(ROOT, 'packs', 'BlackClover_BP')
RP = os.path.join(ROOT, 'packs', 'BlackClover_RP')

_NS = uuid.UUID('7d1c6a52-0b5e-4f1e-9a0b-6c10b1ac0c10')


def uid(name: str) -> str:
    return str(uuid.uuid5(_NS, name))


def _path(base, rel):
    p = os.path.join(base, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def write_json(base, rel, obj):
    with open(_path(base, rel), 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write('\n')


def write_text(base, rel, text):
    with open(_path(base, rel), 'w', encoding='utf-8') as fh:
        fh.write(text)


def write_png(base, rel, arr):
    tex.save(arr, _path(base, rel))


def path(base, rel):
    return _path(base, rel)
