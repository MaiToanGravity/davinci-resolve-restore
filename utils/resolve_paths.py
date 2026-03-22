"""Thiết lập sys.path và biến môi trường cho DaVinci Resolve Scripting API."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def configure_resolve_paths() -> None:
    api = os.environ.get("RESOLVE_SCRIPT_API")
    if api:
        modules = Path(api) / "Modules"
        if modules.is_dir():
            s = str(modules.resolve())
            if s not in sys.path:
                sys.path.insert(0, s)

    if not os.environ.get("RESOLVE_SCRIPT_LIB") and sys.platform == "win32":
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        dll = Path(pf) / "Blackmagic Design" / "DaVinci Resolve" / "fusionscript.dll"
        if dll.is_file():
            os.environ["RESOLVE_SCRIPT_LIB"] = str(dll)

    if sys.platform == "win32" and not os.environ.get("RESOLVE_SCRIPT_API"):
        pd = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        mods = (
            Path(pd)
            / "Blackmagic Design"
            / "DaVinci Resolve"
            / "Support"
            / "Developer"
            / "Scripting"
            / "Modules"
        )
        if mods.is_dir():
            s = str(mods.resolve())
            if s not in sys.path:
                sys.path.insert(0, s)
