"""Runs Rhubarb Lip Sync on an audio file and returns the path to its JSON output."""
import os
import subprocess

# Set RHUBARB_PATH in your environment (or Maya.env), or pass exe= directly.
RHUBARB_EXE = os.environ.get("RHUBARB_PATH", "rhubarb")


def run_rhubarb(wav_path, out_json=None, dialog_path=None, exe=None):
    """Analyze a WAV/OGG file. dialog_path is an optional .txt of the lyrics,
    which helps a lot with singing."""
    exe = exe or RHUBARB_EXE
    out_json = out_json or os.path.splitext(wav_path)[0] + "_cues.json"

    cmd = [exe, "-f", "json", "-o", out_json]
    if dialog_path:
        cmd += ["-d", dialog_path]
    cmd.append(wav_path)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Rhubarb failed:\n{result.stderr}")
    return out_json
