"""Auto lip sync for control-based Maya face rigs."""
from .cues import load_cues
from .keyer import key_lipsync
from .poses import PoseLibrary
from .rhubarb import run_rhubarb


def run(wav_path, pose_library_path, dialog_path=None, start_frame=0, **cue_options):
    """Full pass: analyze audio, load poses, key the rig."""
    json_path = run_rhubarb(wav_path, dialog_path=dialog_path)
    cues = load_cues(json_path, start_frame=start_frame, **cue_options)
    library = PoseLibrary.load(pose_library_path)
    key_lipsync(cues, library)
    return cues
