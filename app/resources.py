"""Resource path helper that works both in development and inside a
PyInstaller-built executable."""

import os
import sys


def resource_path(relative: str) -> str:
    """Return an absolute path to a bundled resource file.

    In a PyInstaller one-file build, data files are extracted into
    `sys._MEIPASS`. In a normal dev run, resources live next to the
    project root (the parent of this file's directory).
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, relative)
    # app/ -> project root
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(here)
    return os.path.join(project_root, relative)
