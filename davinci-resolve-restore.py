#!/usr/bin/env python3
"""
Smoke test: Scripting API DaVinci Resolve, pyautogui, keyboard.

Chạy test mặc định:
  python davinci-resolve-restore.py

Bắt mọi sự kiện phím (keydown) cho đến khi nhấn phím thoát (mặc định esc):
  python davinci-resolve-restore.py --listen

Trên Windows, hook bàn phím toàn cục có thể cần chạy terminal với quyền Administrator.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import pyautogui
import keyboard


def _is_key_down_event(event: keyboard.KeyboardEvent) -> bool:
    kd = getattr(keyboard, "KEY_DOWN", None)
    if kd is not None:
        return event.event_type == kd
    return str(event.event_type).lower() in ("down", "key down")


def listen_keyboard_events(stop_key: str = "esc") -> None:
    """
    Gắn hook toàn cục: in mỗi lần nhấn phím (keydown) cho đến khi nhấn stop_key.
    """
    stop_key = stop_key.strip().lower() or "esc"

    def on_event(event: keyboard.KeyboardEvent) -> None:
        if not _is_key_down_event(event):
            return
        name = event.name or "?"
        print(f"[key] down name={name!r} scan={event.scan_code}", flush=True)

    print(
        f"Đang bắt sự kiện bàn phím — nhấn {stop_key!r} để thoát.",
        flush=True,
    )
    keyboard.hook(on_event)
    try:
        keyboard.wait(stop_key)
    finally:
        keyboard.unhook_all()


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


def test_pyautogui() -> bool:
    try:
        w, h = pyautogui.size()
        x, y = pyautogui.position()
        print(f"[pyautogui] Màn hình {w}x{h}, vị trí chuột ({x}, {y})")
        return True
    except Exception as e:
        print(f"[pyautogui] Lỗi: {e}", file=sys.stderr)
        return False


def test_keyboard() -> bool:
    try:
        print("[keyboard] Trong 4 giây tới, nhấn phím Space để xác nhận hook hoạt động…")
        deadline = time.monotonic() + 4.0
        while time.monotonic() < deadline:
            if keyboard.is_pressed("space"):
                print("[keyboard] Đã nhận Space — OK")
                return True
            time.sleep(0.05)
        print(
            "[keyboard] Không nhận Space (bỏ qua được). "
            "Nếu hook lỗi, thử chạy terminal/script với quyền Administrator.",
        )
        return True
    except Exception as e:
        print(f"[keyboard] Lỗi: {e}", file=sys.stderr)
        return False


def test_resolve() -> bool:
    resolve = get_resolve()
    if resolve is None:
        return False
    try:
        name = resolve.GetProductName()
        ver = resolve.GetVersionString()
        print(f"[resolve] {name} — {ver}")
        pm = resolve.GetProjectManager()
        proj = pm.GetCurrentProject() if pm else None
        if proj:
            print(f"[resolve] Dự án đang mở: {proj.GetName()}")
        else:
            print("[resolve] Chưa có dự án đang mở (vẫn coi là kết nối OK).")
        return True
    except Exception as e:
        print(f"[resolve] Lỗi gọi API: {e}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test Resolve / pyautogui / keyboard")
    parser.add_argument(
        "--listen",
        action="store_true",
        help="Chỉ chạy bắt sự kiện bàn phím (hook) cho đến khi nhấn phím thoát",
    )
    parser.add_argument(
        "--stop-key",
        default="esc",
        metavar="KEY",
        help="Phím dừng khi dùng --listen (mặc định: esc)",
    )
    parser.add_argument(
        "--skip-resolve",
        action="store_true",
        help="Bỏ qua test DaVinci Resolve API",
    )
    parser.add_argument(
        "--skip-ui",
        action="store_true",
        help="Bỏ qua test pyautogui và keyboard",
    )
    args = parser.parse_args()

    if args.listen:
        try:
            listen_keyboard_events(args.stop_key)
        except Exception as e:
            print(f"[keyboard] Lỗi hook: {e}", file=sys.stderr)
            return 1
        return 0

    ok = True
    if not args.skip_ui:
        ok = test_pyautogui() and ok
        ok = test_keyboard() and ok
    if not args.skip_resolve:
        ok = test_resolve() and ok

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
