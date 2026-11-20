"""Turns cues + a pose library into keyframes on the rig."""
import maya.cmds as cmds


def key_lipsync(cues, library, anim_layer="lipsync_LYR", tangent="auto"):
    """Key every pose attribute at each cue's start frame.

    With an anim_layer (default), keys are pure offsets on an additive layer,
    so lip sync sits on top of body/expression animation without fighting it.
    Pass anim_layer=None to key absolute values on the base layer instead.
    Shapes with no captured pose (including X, unless you capture it) key to rest.
    """
    attrs = library.attrs
    if not attrs:
        raise RuntimeError("Pose library has no neutral pose.")

    missing = {c["shape"] for c in cues} - set(library.visemes) - {"X"}
    if missing:
        cmds.warning(f"No pose captured for {sorted(missing)}; using rest pose.")

    cmds.undoInfo(openChunk=True, chunkName="autolipsync")
    try:
        if anim_layer:
            if not cmds.animLayer(anim_layer, query=True, exists=True):
                cmds.animLayer(anim_layer)
            cmds.animLayer(anim_layer, edit=True, attribute=attrs)

        for cue in cues:
            offsets = library.visemes.get(cue["shape"], {})
            for attr in attrs:
                offset = offsets.get(attr, 0.0)
                kwargs = {
                    "time": cue["start"],
                    "value": offset if anim_layer else library.neutral[attr] + offset,
                    "inTangentType": tangent,
                    "outTangentType": tangent,
                }
                if anim_layer:
                    kwargs["animLayer"] = anim_layer
                cmds.setKeyframe(attr, **kwargs)
    finally:
        cmds.undoInfo(closeChunk=True)
