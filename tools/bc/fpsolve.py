"""Solve bone transforms so an item lands at a chosen spot on the first-person screen.

The first-person arm pose is the one Mojang uses for the right arm
(rotation [95, -45, 115], position [13.5, -10, 12] plus rightItem [0, 0, -1]).
In that space the camera sits near (0, 22, 0) and looks along display +Z;
screen-right is display -X.
"""
from __future__ import annotations

import math

import numpy as np

from . import render

FP_POSE = {'rightarm': {'rotation': [95, -45, 115], 'position': [13.5, -10, 12]}, 'rightitem': {'position': [0, 0, -1]}}
CAMERA = np.array([0.0, 22.0, 0.0])

_SKELETON = {
    'description': {'texture_width': 16, 'texture_height': 16},
    'bones': [
        {'name': 'root', 'pivot': [0, 0, 0]},
        {'name': 'waist', 'parent': 'root', 'pivot': [0, 12, 0]},
        {'name': 'body', 'parent': 'waist', 'pivot': [0, 24, 0]},
        {'name': 'rightArm', 'parent': 'body', 'pivot': [-5, 22, 0]},
        {'name': 'rightItem', 'parent': 'rightArm', 'pivot': [-6, 15, 1]},
    ],
}


def bone_world(name='rightitem', pose=None):
    m = render.Model({'minecraft:geometry': [_SKELETON]}, np.zeros((16, 16, 4), np.float32))
    return m.world_mats(pose or FP_POSE)[name]


def hand_point():
    """Display-space position of the fist (bottom centre of the arm) in first person."""
    M = bone_world('rightarm')
    return (M @ np.array([6.0, 12.5, 0.0, 1.0]))[:3]  # file (-6, 12.5, 0) -> display x=+6


def basis(y_axis, z_hint):
    y = np.asarray(y_axis, float)
    y /= np.linalg.norm(y)
    z = np.asarray(z_hint, float)
    z = z - y * (z @ y)
    z /= np.linalg.norm(z)
    x = np.cross(y, z)
    R = np.eye(4)
    R[:3, 0], R[:3, 1], R[:3, 2] = x, y, z
    return R


def to_bedrock(L):
    """Decompose display-space local matrix (T*R*S, pivot 0) into Bedrock position/rotation/scale."""
    t = L[:3, 3]
    M = L[:3, :3]
    s = np.linalg.norm(M[:, 0])
    R = M / s
    b = -math.asin(max(-1.0, min(1.0, R[2, 0])))
    a = math.atan2(R[1, 0], R[0, 0])
    c = math.atan2(R[2, 1], R[2, 2])
    rx, ry, rz = -math.degrees(c), -math.degrees(b), math.degrees(a)
    pos = [-t[0], t[1], t[2]]
    return [round(v, 2) for v in pos], [round(v, 2) for v in (rx, ry, rz)], round(s, 3)


def solve(target_disp, R_disp, scale=1.0, local_anchor=(0, 0, 0), parent='rightitem'):
    """Find bone pos/rot so that `local_anchor` (file coords in the bone) lands on target."""
    P = bone_world(parent)
    anc = np.array([-local_anchor[0], local_anchor[1], local_anchor[2]], float)
    D = np.eye(4)
    D[:3, :3] = R_disp[:3, :3] * scale
    D[:3, 3] = np.asarray(target_disp, float) - D[:3, :3] @ anc
    L = np.linalg.inv(P) @ D
    return to_bedrock(L)
