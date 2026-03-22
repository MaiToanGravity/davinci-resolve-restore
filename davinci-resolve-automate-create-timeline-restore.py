from __future__ import annotations

import argparse
import sys
import time

import pyautogui
import keyboard

from utils import configure_resolve_paths, get_resolve

def get_current_project():
    resolve = get_resolve()
    if resolve is None:
        print("[automate-bins] Không lấy được Resolve.", file=sys.stderr)
        return None
    pm = resolve.GetProjectManager()
    if pm is None:
        print("[automate-bins] Không lấy được ProjectManager.", file=sys.stderr)
        return None
    project = pm.GetCurrentProject()
    if project is None:
        print(
            "[automate-bins] Chưa có dự án đang mở — mở một project rồi chạy lại.",
            file=sys.stderr,
        )
    return project
def create_new_timeline_backup(name):
    pyautogui.hotkey("ctrl", "alt", "s")
    time.sleep(0.1)
    pyautogui.typewrite(name)
    pyautogui.press("enter")
    time.sleep(0.1)

def iter_leaf_folders(folder):
    subs = folder.GetSubFolderList()
    if not subs:
        yield folder
        return
    for sub in subs:
        yield from iter_leaf_folders(sub)


def main() -> int:
    project = get_current_project()
    mp = project.GetMediaPool()
    parent = mp.GetRootFolder()

    for leaf in iter_leaf_folders(parent):
        mp.SetCurrentFolder(leaf)
        folder = mp.GetCurrentFolder()
        items = folder.GetClipList()
        index = 0
        time.sleep(0.1)
        for item in items:
            if index == 0:
                pyautogui.click(-1478, 152)
            print(item.GetName())
            create_new_timeline_backup(item.GetName())
            pyautogui.press("down")
            index += 1

    mp.SetCurrentFolder(parent)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
