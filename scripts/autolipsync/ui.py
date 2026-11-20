"""Auto Lip Sync window.

    import autolipsync.ui
    autolipsync.ui.show()

Built with maya.cmds (no Qt), so it works the same across Maya versions and OSes.
Last-used paths are remembered per machine via Maya optionVars.
"""
import os

import maya.cmds as cmds
import maya.mel as mel

# Module references (not `from x import y`) so the dev reload button picks up edits.
from . import cues, keyer, poses, rhubarb

WINDOW = "autolipsyncWin"
LAYER = "lipsync_LYR"
SOUND_NODE = "lipsync_audio"
OPT_PREFIX = "autolipsync_"

SHAPES = [
    ("A", "closed (M, B, P)"),
    ("B", "slightly open"),
    ("C", "open (EH)"),
    ("D", "wide open (AA)"),
    ("E", "rounded (O)"),
    ("F", "puckered (OO, W)"),
    ("G", "teeth on lip (F, V)"),
    ("H", "tongue up (L)"),
    ("X", "rest / idle"),
]


# ---------------------------------------------------------------- prefs
def _get_opt(key, default=""):
    name = OPT_PREFIX + key
    return cmds.optionVar(query=name) if cmds.optionVar(exists=name) else default


def _set_opt(key, value):
    cmds.optionVar(stringValue=(OPT_PREFIX + key, value))


# ---------------------------------------------------------------- window
class LipSyncWindow:
    def __init__(self):
        self.library = poses.PoseLibrary()
        self.ui = {}

    # ---------- layout helpers
    def _path_row(self, label, key, file_filter, mode, start_dir=""):
        """Label + text field + browse button. mode: 0 = any file, 1 = existing file."""
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnWidth3=(70, 260, 30))
        cmds.text(label=label, align="right")
        field = cmds.textField(text=_get_opt(key))
        cmds.textField(field, edit=True, changeCommand=lambda v, k=key: _set_opt(k, v))
        cmds.button(
            label="...",
            command=lambda *_: self._browse(field, key, file_filter, mode, start_dir),
        )
        cmds.setParent("..")
        return field

    def _browse(self, field, key, file_filter, mode, start_dir):
        current = cmds.textField(field, query=True, text=True)
        directory = os.path.dirname(current) if current else start_dir
        result = cmds.fileDialog2(
            fileMode=mode, fileFilter=file_filter, startingDirectory=directory or None
        )
        if result:
            cmds.textField(field, edit=True, text=result[0])
            _set_opt(key, result[0])

    def _status(self, message, warn=False):
        cmds.text(self.ui["status"], edit=True, label=message)
        (cmds.warning if warn else print)(f"[autolipsync] {message}")

    # ---------- build
    def build(self):
        if cmds.window(WINDOW, exists=True):
            cmds.deleteUI(WINDOW)
        cmds.window(WINDOW, title="Auto Lip Sync", widthHeight=(440, 640))
        cmds.scrollLayout(childResizable=True)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=6)

        # 1. Pose library
        cmds.frameLayout(label="1. Pose Library", collapsable=True, marginWidth=6, marginHeight=6)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
        self.ui["pose_path"] = self._path_row(
            "Library", "pose_path", "Pose library (*.json)", 0, poses.POSES_DIR
        )
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAttach2=("both", "both"))
        cmds.button(label="Load", command=lambda *_: self.load_library())
        cmds.button(label="Save", command=lambda *_: self.save_library())
        cmds.setParent("..")

        cmds.separator(height=8, style="in")
        cmds.button(
            label="Capture Neutral (select face controls at rest)",
            height=28,
            command=lambda *_: self.capture_neutral(),
        )
        self.ui["neutral_label"] = cmds.text(label="No neutral pose", align="left")

        cmds.rowColumnLayout(
            numberOfColumns=4,
            columnWidth=[(1, 170), (2, 70), (3, 80), (4, 80)],
            columnSpacing=[(2, 4), (3, 4), (4, 4)],
            rowSpacing=(1, 2),
        )
        self.ui["shape_status"] = {}
        for shape, desc in SHAPES:
            cmds.text(label=f"{shape}   {desc}", align="left")
            self.ui["shape_status"][shape] = cmds.text(label="--")
            cmds.button(label="Capture", command=lambda *_, s=shape: self.capture_viseme(s))
            cmds.button(label="Preview", command=lambda *_, s=shape: self.preview(s))
        cmds.setParent("..")
        cmds.button(label="Return to Rest", command=lambda *_: self.preview(None))
        cmds.setParent("..")
        cmds.setParent("..")

        # 2. Audio
        cmds.frameLayout(label="2. Audio", collapsable=True, marginWidth=6, marginHeight=6)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
        self.ui["audio_path"] = self._path_row("Audio", "audio_path", "Audio (*.wav *.ogg)", 1)
        self.ui["lyrics_path"] = self._path_row("Lyrics", "lyrics_path", "Text (*.txt)", 1)
        start = int(cmds.playbackOptions(query=True, minTime=True))
        self.ui["start_frame"] = cmds.intFieldGrp(label="Start frame", value1=start, columnWidth2=(80, 60))
        self.ui["min_frames"] = cmds.floatFieldGrp(
            label="Min shape length", value1=1.0, precision=1, columnWidth2=(80, 60)
        )
        self.ui["lead_frames"] = cmds.floatFieldGrp(
            label="Lead frames", value1=1.0, precision=1, columnWidth2=(80, 60)
        )
        self.ui["reuse_json"] = cmds.checkBox(
            label="Reuse existing cue JSON (skip re-analyzing audio)", value=True
        )
        self.ui["load_sound"] = cmds.checkBox(label="Load audio into timeline", value=True)
        cmds.setParent("..")
        cmds.setParent("..")

        # 3. Settings
        cmds.frameLayout(
            label="Settings", collapsable=True, collapse=True, marginWidth=6, marginHeight=6
        )
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
        self.ui["rhubarb_path"] = self._path_row("Rhubarb", "rhubarb_path", "All files (*.*)", 1)
        cmds.text(label="Leave blank to use RHUBARB_PATH or rhubarb on PATH.", align="left")
        cmds.setParent("..")
        cmds.setParent("..")

        # Actions
        cmds.separator(height=10, style="none")
        cmds.button(
            label="Generate Lip Sync",
            height=40,
            backgroundColor=(0.35, 0.55, 0.40),
            command=lambda *_: self.generate(),
        )
        cmds.button(label="Remove Lip Sync Layer", command=lambda *_: self.remove_layer())
        self.ui["status"] = cmds.text(label="Ready", align="left")

        cmds.showWindow(WINDOW)

        # Reopen the last library automatically if it still exists.
        last = _get_opt("pose_path")
        if last and os.path.isfile(last):
            self.load_library(quiet=True)

    # ---------- pose library
    def _refresh_pose_status(self):
        count = len(self.library.controls)
        text = f"Neutral: {count} controls" if self.library.neutral else "No neutral pose"
        cmds.text(self.ui["neutral_label"], edit=True, label=text)
        for shape, label in self.ui["shape_status"].items():
            cmds.text(label, edit=True, label="captured" if shape in self.library.visemes else "--")

    def load_library(self, quiet=False):
        path = cmds.textField(self.ui["pose_path"], query=True, text=True)
        if not os.path.isfile(path):
            self._status("Pose library file not found.", warn=True)
            return
        self.library = poses.PoseLibrary.load(path)
        self._refresh_pose_status()
        if not quiet:
            self._status(f"Loaded {os.path.basename(path)}")

    def save_library(self):
        path = cmds.textField(self.ui["pose_path"], query=True, text=True)
        if not path:
            self._browse(
                self.ui["pose_path"], "pose_path", "Pose library (*.json)", 0, poses.POSES_DIR
            )
            path = cmds.textField(self.ui["pose_path"], query=True, text=True)
            if not path:
                return
        self.library.save(path)
        _set_opt("pose_path", path)
        self._status(f"Saved {os.path.basename(path)}")

    def capture_neutral(self):
        try:
            self.library.capture_neutral()
        except RuntimeError as e:
            self._status(str(e), warn=True)
            return
        self.library.visemes = {}  # old offsets don't apply to a new neutral
        self._refresh_pose_status()
        self._status("Neutral captured. Pose each shape and click Capture.")

    def capture_viseme(self, shape):
        try:
            self.library.capture_viseme(shape)
        except RuntimeError as e:
            self._status(str(e), warn=True)
            return
        self._refresh_pose_status()
        self._status(f"Captured {shape} ({len(self.library.visemes[shape])} channels). Remember to Save.")

    def preview(self, shape):
        if not self.library.neutral:
            self._status("Capture or load a neutral pose first.", warn=True)
            return
        self.library.preview(shape)

    # ---------- generate
    def _load_sound(self, wav, start_frame):
        if cmds.objExists(SOUND_NODE):
            cmds.delete(SOUND_NODE)
        node = cmds.sound(file=wav, offset=start_frame, name=SOUND_NODE)
        slider = mel.eval("$tmp = $gPlayBackSlider")
        cmds.timeControl(slider, edit=True, sound=node, displaySound=True)

    def generate(self):
        if not self.library.neutral or not self.library.visemes:
            self._status("Load or capture a pose library first.", warn=True)
            return

        wav = cmds.textField(self.ui["audio_path"], query=True, text=True)
        if not os.path.isfile(wav) or os.path.splitext(wav)[1].lower() not in (".wav", ".ogg"):
            self._status("Pick a WAV or OGG audio file.", warn=True)
            return

        lyrics = cmds.textField(self.ui["lyrics_path"], query=True, text=True) or None
        if lyrics and not os.path.isfile(lyrics):
            self._status("Lyrics file not found; running without it.", warn=True)
            lyrics = None

        start = cmds.intFieldGrp(self.ui["start_frame"], query=True, value1=True)
        min_frames = cmds.floatFieldGrp(self.ui["min_frames"], query=True, value1=True)
        lead = cmds.floatFieldGrp(self.ui["lead_frames"], query=True, value1=True)
        exe = cmds.textField(self.ui["rhubarb_path"], query=True, text=True) or None

        json_path = os.path.splitext(wav)[0] + "_cues.json"
        reuse = cmds.checkBox(self.ui["reuse_json"], query=True, value=True)

        try:
            if not (reuse and os.path.isfile(json_path)):
                self._status("Analyzing audio with Rhubarb (can take a minute)...")
                cmds.refresh()
                cmds.waitCursor(state=True)
                try:
                    rhubarb.run_rhubarb(wav, out_json=json_path, dialog_path=lyrics, exe=exe)
                finally:
                    cmds.waitCursor(state=False)

            cue_list = cues.load_cues(
                json_path, start_frame=start, min_frames=min_frames, lead_frames=lead
            )
            keyer.key_lipsync(cue_list, self.library, anim_layer=LAYER)

            if cmds.checkBox(self.ui["load_sound"], query=True, value=True):
                self._load_sound(wav, start)
        except Exception as e:
            self._status(f"Failed: {e}", warn=True)
            raise

        self._status(f"Keyed {len(cue_list)} mouth shapes on {LAYER}.")

    def remove_layer(self):
        if cmds.animLayer(LAYER, query=True, exists=True):
            cmds.delete(LAYER)
            self._status("Removed lip sync layer.")
        else:
            self._status("No lip sync layer to remove.")


_window = None


def show():
    global _window
    _window = LipSyncWindow()
    _window.build()
    return _window
