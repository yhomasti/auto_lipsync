"""Reads Rhubarb's JSON and converts its timings to Maya frames."""
import json

from maya.api import OpenMaya as om


def seconds_to_frame(seconds):
    """Convert seconds to frames using the scene's current frame rate."""
    return om.MTime(seconds, om.MTime.kSeconds).asUnits(om.MTime.uiUnit())


def load_cues(json_path, start_frame=0.0, min_frames=1.0, lead_frames=1.0):
    """Return a list of {"start", "end", "shape"} dicts in frames.

    start_frame: frame where the audio begins in your scene.
    min_frames:  cues shorter than this get absorbed into the previous one
                 (cuts down on chattering).
    lead_frames: shift every shape slightly earlier; mouths move a bit
                 before the sound is heard.
    """
    with open(json_path) as f:
        data = json.load(f)

    offset = start_frame - lead_frames
    cues = []
    for cue in data["mouthCues"]:
        start = round(seconds_to_frame(cue["start"]) + offset)
        end = round(seconds_to_frame(cue["end"]) + offset)

        if cues and (end - start) < min_frames:
            cues[-1]["end"] = end
            continue

        cues.append({"start": start, "end": end, "shape": cue["value"]})
    return cues
