"""Khởi chạy ứng dụng DaVinci Resolve (Windows)."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


def find_resolve_exe() -> Path | None:
    """Tìm Resolve.exe trong Program Files (và x86)."""
    for key in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(key)
        if not base:
            continue
        candidate = Path(base) / "Blackmagic Design" / "DaVinci Resolve" / "Resolve.exe"
        if candidate.is_file():
            return candidate
    return None


def launch_resolve(
    executable: Path | str | None = None,
    *,
    wait_after: float = 2.0,
) -> bool:
    """
    Chạy DaVinci Resolve.
    Trả về True nếu đã spawn process (không đảm bảo Resolve đã sẵn sàng cho API).
    """
    exe = Path(executable) if executable else find_resolve_exe()
    if exe is None or not exe.is_file():
        return False
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        [str(exe)],
        cwd=str(exe.parent),
        close_fds=True,
        creationflags=creationflags,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if wait_after > 0:
        time.sleep(wait_after)
    return True


def wait_for_resolve(
    get_resolve_fn,
    *,
    timeout: float = 90.0,
    interval: float = 1.0,
):
    """
    Gọi get_resolve_fn() lặp lại cho đến khi khác None hoặc hết timeout.
    get_resolve_fn: thường là get_resolve (import từ resolve_app).
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        resolve = get_resolve_fn()
        if resolve is not None:
            return resolve
        time.sleep(interval)
    return None
