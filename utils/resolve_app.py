"""Kết nối tới DaVinci Resolve qua Scripting API."""

from __future__ import annotations

import sys

from .resolve_paths import configure_resolve_paths


def get_resolve():
    configure_resolve_paths()
    try:
        import DaVinciResolveScript as dvr_script  # type: ignore[import-untyped]
    except ImportError as e:
        print(f"[resolve] Import lỗi: {e}", file=sys.stderr)
        return None
    resolve = dvr_script.scriptapp("Resolve")
    if resolve is None:
        print(
            "[resolve] scriptapp('Resolve') = None — mở DaVinci Resolve rồi chạy lại.",
            file=sys.stderr,
        )
    return resolve
