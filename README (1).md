# autolipsync

Audio → Rhubarb → viseme cues → keyframes on a joint/control face rig.

## Layout

```
maya-autolipsync/
  autolipsync.mod          # tells Maya where the package lives
  scripts/autolipsync/     # the Python package (Maya adds scripts/ to sys.path)
    rhubarb.py             # runs Rhubarb, returns JSON path
    cues.py                # JSON -> frame-based cues, cleanup
    poses.py               # capture/save/load viseme poses per character
    keyer.py               # cues + poses -> keys on an additive anim layer
  poses/                   # pose library JSONs, one per character
```

## Setup

1. Put this folder somewhere permanent and fix the path in `autolipsync.mod`.
2. Copy `autolipsync.mod` into `Documents/maya/modules/` (create it if missing). Restart Maya.
3. Download Rhubarb Lip Sync and set `RHUBARB_PATH` to the executable
   (via `Maya.env` or your system environment).
4. Audio must be WAV or OGG.

## Shelf button (dev version, reloads on every click)

```python
import importlib
import autolipsync
from autolipsync import rhubarb, cues, poses, keyer
for m in (rhubarb, cues, poses, keyer, autolipsync):
    importlib.reload(m)

autolipsync.run(
    "C:/proj/audio/vocals.wav",
    "C:/dev/maya-autolipsync/poses/singer.json",
    dialog_path="C:/proj/audio/lyrics.txt",
    start_frame=1,
)
```
