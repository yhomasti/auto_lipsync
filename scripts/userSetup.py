"""Runs at Maya startup (this folder is on the path via autolipsync.mod)."""
import maya.utils


def _install_autolipsync_shelf():
    try:
        import autolipsync.shelf
        autolipsync.shelf.install()
    except Exception as e:  # never block Maya startup over a shelf
        print(f"[autolipsync] Shelf install skipped: {e}")


maya.utils.executeDeferred(_install_autolipsync_shelf)
