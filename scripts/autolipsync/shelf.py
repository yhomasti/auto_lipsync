"""Creates (or rebuilds) a 'LipSync' shelf. Called automatically by userSetup.py."""
import importlib
import sys

import maya.cmds as cmds
import maya.mel as mel

SHELF = "LipSync"


def reload_and_show():
    """Dev helper: reload every autolipsync module, then open a fresh window."""
    names = sorted((n for n in sys.modules if n.startswith("autolipsync")), reverse=True)
    for name in names:  # submodules first, package last
        importlib.reload(sys.modules[name])
    import autolipsync.ui
    autolipsync.ui.show()


def install():
    if cmds.about(batch=True):
        return

    top = mel.eval("$tmp = $gShelfTopLevel")
    if cmds.shelfLayout(SHELF, exists=True):
        # Rebuild contents so buttons never duplicate across sessions.
        for child in cmds.shelfLayout(SHELF, query=True, childArray=True) or []:
            cmds.deleteUI(child)
    else:
        cmds.shelfLayout(SHELF, parent=top)

    cmds.shelfButton(
        parent=SHELF,
        label="Lip Sync",
        annotation="Open the Auto Lip Sync window",
        image="commandButton.png",
        imageOverlayLabel="Lips",
        sourceType="python",
        command="import autolipsync.ui; autolipsync.ui.show()",
    )
    cmds.shelfButton(
        parent=SHELF,
        label="Reload",
        annotation="Dev: reload autolipsync code from disk and reopen the window",
        image="commandButton.png",
        imageOverlayLabel="Dev",
        sourceType="python",
        command="import autolipsync.shelf; autolipsync.shelf.reload_and_show()",
    )
