"""Viseme pose library for a control-based face rig.

Workflow:
    lib = PoseLibrary()
    # select the mouth/jaw controls with the face at rest
    lib.capture_neutral()
    # pose the rig into each shape, then:
    lib.capture_viseme("A")   # closed M/B/P
    ...
    lib.save(os.path.join(POSES_DIR, "singer.json"))
"""
import json
import os

import maya.cmds as cmds

# <repo>/poses, found relative to this file so it works on any machine.
POSES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "poses")
)

SKIP_ATTRS = {"visibility"}
EPSILON = 1e-4


def _keyable_attrs(controls):
    attrs = []
    for ctrl in controls:
        for attr in cmds.listAttr(ctrl, keyable=True, unlocked=True) or []:
            if attr not in SKIP_ATTRS:
                attrs.append(f"{ctrl}.{attr}")
    return attrs


class PoseLibrary:
    def __init__(self, controls=None, neutral=None, visemes=None):
        self.controls = controls or []
        self.neutral = neutral or {}   # attr -> rest value
        self.visemes = visemes or {}   # shape -> {attr: offset from rest}

    @property
    def attrs(self):
        return list(self.neutral.keys())

    def capture_neutral(self, controls=None):
        """Record rest values for the given (or selected) controls."""
        self.controls = controls or cmds.ls(selection=True)
        if not self.controls:
            raise RuntimeError("Select the face controls first.")
        self.neutral = {a: cmds.getAttr(a) for a in _keyable_attrs(self.controls)}

    def capture_viseme(self, shape):
        """Record the current rig pose as an offset from neutral."""
        if not self.neutral:
            raise RuntimeError("Capture the neutral pose first.")
        offsets = {}
        for attr, rest in self.neutral.items():
            delta = cmds.getAttr(attr) - rest
            if abs(delta) > EPSILON:
                offsets[attr] = delta
        self.visemes[shape] = offsets

    def preview(self, shape):
        """Snap the rig to a stored shape (no keys set)."""
        offsets = self.visemes.get(shape, {})
        for attr, rest in self.neutral.items():
            cmds.setAttr(attr, rest + offsets.get(attr, 0.0))

    def save(self, path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(
                {"controls": self.controls, "neutral": self.neutral, "visemes": self.visemes},
                f,
                indent=2,
            )

    @classmethod
    def load(cls, path):
        with open(path) as f:
            data = json.load(f)
        return cls(data["controls"], data["neutral"], data["visemes"])