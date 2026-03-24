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
from pathlib import PureWindowsPath
import pyperclip
import threading
_stop = threading.Event()

def _on_esc():
    _stop.set()
    print("\nĐã nhận Esc — sẽ dừng sau khi bước hiện tại xong.", file=sys.stderr)

BACKUP_LOCATION = r"C:\\Toan\\Project\\Davinci Restore\\Resolve Project Backups"
ORIGINAL_LOCATION = r"C:\\Toan\\Project\\Davinci Resolve\\davinci-resolve-restore\\original"
RESTORE_LOCATION = r"C:\\Toan\\Project\\Davinci Resolve\\davinci-resolve-restore\\restore"
OUTPUT_LOCATION = r"C:\\Toan\\Project\\Davinci Resolve\\davinci-resolve-restore\\output"

import sys
import pandas as pd
import pyautogui
import keyboard
import os
from utils import configure_resolve_paths, get_resolve, launch_resolve, wait_for_resolve
import json
import time
import shutil
from pathlib import Path

def get_data_from_excel():
    df = pd.read_excel( os.path.join(OUTPUT_LOCATION, 'data.xlsx'), sheet_name=None)
    # Convert to JSON
    return df

def click_on_decoy_timeline():
    pyautogui.click(-1478, 152)
    # pyautogui.click(-2216, 156)

def format_data_for_restore(data):
    data_list = []
    data_restore = []
    for sheet_name, df in data.items():
        for index, row in df.iterrows():
            # Ô trống trong Excel → float('nan'), không phải None — dùng pd.isna
            tn = row["Timeline Name"]
            timeline_name = "" if pd.isna(tn) else str(tn).strip()
            data_list.append({
                "folder": row['Folder'],
                "backup_name": row['Backup Name'],
                "timeline_name": timeline_name,
            })
    # Get data from json
    with open(os.path.join(OUTPUT_LOCATION, 'restore_data.json'), 'r') as f:
        data_restore = json.load(f)
    # Filter data_list not in data_restore
    filtered_data_list = []
    for item in data_list:
        all_same = False
        for restore_item in data_restore:
            if item["folder"] == restore_item["folder"] and item["backup_name"] == restore_item["backup_name"]:
                all_same = True
                break
        if all_same:
            continue
        filtered_data_list.append(item)
    return filtered_data_list

def open_davinci_resolve():
    configure_resolve_paths()
    resolve = get_resolve()
    if resolve is None:
        print("Không tìm thấy Resolve.exe (cài đặt chuẩn trong Program Files).")
        return 1
    return resolve

def open_davinci_resolve_and_load_project_restore():
    configure_resolve_paths()
    resolve = get_resolve()
    if resolve is None:
        print("Đang thử mở DaVinci Resolve…")
        if not launch_resolve():
            print("Không tìm thấy Resolve.exe (cài đặt chuẩn trong Program Files).")
            return 1
        resolve = wait_for_resolve(get_resolve, timeout=120.0, interval=0.1)
    if resolve is None:
        print("DaVinci Resolve không phản hồi scripting — mở app thủ công rồi chạy lại.")
        return 1
    project = resolve.GetProjectManager().GetCurrentProject()
    if project is None:
        print("Không tìm thấy project")
        return 1
    pm = resolve.GetProjectManager()
    pm.LoadProject("Restore")
    return resolve, project, pm

def create_new_timeline_backup(name):
    click_on_decoy_timeline()
    pyautogui.hotkey("ctrl", "alt", "s")
    time.sleep(0.1)
    pyautogui.typewrite(name)
    pyautogui.press("enter")
    time.sleep(0.1)

def close_davinci_resolve():
    pyautogui.click(-21, 15)

def iter_files(root: Path, recursive: bool) -> list[Path]:
    if not root.is_dir():
        return []
    if recursive:
        return sorted(p for p in root.rglob("*") if p.is_file())
    return sorted(p for p in root.iterdir() if p.is_file())

def replace_timeline_backup(item, name_backup):
    files_backup = iter_files(Path(BACKUP_LOCATION), recursive=True)
    original_file = os.path.abspath(os.path.join(ORIGINAL_LOCATION, item["folder"], item["backup_name"]))
    for file in files_backup:
        if name_backup in file.name:
            shutil.copy(original_file, file)
            break

def clean_up_backup_folder():
    for file in os.listdir(BACKUP_LOCATION):
        path = os.path.join(BACKUP_LOCATION, file)
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

def get_list_timeline():
    configure_resolve_paths()
    resolve = get_resolve()
    if resolve is None:
        print("Không tìm thấy Resolve.exe (cài đặt chuẩn trong Program Files).")
        return 1
    project = resolve.GetProjectManager().GetCurrentProject()
    mp = project.GetMediaPool()
    if project is None:
        print("Không tìm thấy project")
        return 1
    count_timeline = project.GetTimelineCount()
    list_timeline = []
    for i in range(1, count_timeline + 1):
        current_timeline = project.GetTimelineByIndex(i)
        current_timeline_name = current_timeline.GetName()
        list_timeline.append(current_timeline_name)
    return list_timeline
    

def restore_timeline_backup():
    pyautogui.rightClick(-1478, 152)
    # Auto control restore
    # Type down arrow 9 times
    for i in range(9):
        pyautogui.press("down")
    pyautogui.press("right")
    pyautogui.press("enter")

    # Copy name of the timeline
    list_timeline = get_list_timeline()
    # Remove timeline is 000000000000000-Decoy
    list_timeline = [timeline for timeline in list_timeline if "000000000000000-Decoy" not in timeline]
    return list_timeline[0]

def export_timeline_backup(name_timeline, name_timeline_file, item):
    # Use davinci resolve to export timeline backup
    configure_resolve_paths()
    resolve = get_resolve()
    if resolve is None:
        print("Không tìm thấy Resolve.exe (cài đặt chuẩn trong Program Files).")
        return 1
    project = resolve.GetProjectManager().GetCurrentProject()
    mp = project.GetMediaPool()
    if project is None:
        print("Không tìm thấy project")
        return 1
    count_timeline = project.GetTimelineCount()
    for i in range(1, count_timeline + 1):
        current_timeline = project.GetTimelineByIndex(i)
        current_timeline_name = current_timeline.GetName()
        if current_timeline_name == name_timeline:
            output_path = os.path.join(RESTORE_LOCATION, item["folder"], name_timeline_file)
            current_timeline.Export(output_path, resolve.EXPORT_DRT)
            mp.DeleteTimelines([current_timeline])
            break

def update_result_json(name_timeline_file, item):
    with open(os.path.join(OUTPUT_LOCATION, 'restore_data.json'), 'r') as f:
        data = json.load(f)
    data.append({
        "folder": item["folder"],
        "backup_name": item["backup_name"],
        "timeline_name": name_timeline_file,
    })
    with open(os.path.join(OUTPUT_LOCATION, 'restore_data.json'), 'w') as f:
        json.dump(data, f, indent=4)

def restore_workflow(item):
    # Remove all files in BACKUP_LOCATION
    clean_up_backup_folder()
    # open_davinci_resolve_and_load_project_restore()
    p = PureWindowsPath(item["folder"])
    name_backup = f"{p.name} - {item["backup_name"]} Backup"

    # Create new timeline backup and close app
    create_new_timeline_backup(name_backup)
    # close_davinci_resolve()

    # Replace timeline backup
    replace_timeline_backup(item, name_backup)
    time.sleep(1)
    # resolve, project, pm = open_davinci_resolve_and_load_project_restore()

    name_timeline = restore_timeline_backup()
    name_timeline_file = f'{name_timeline}-{item["backup_name"]}.drt'
    export_timeline_backup(name_timeline, name_timeline_file, item)
    # time.sleep(0.5)
    # close_davinci_resolve()
    # time.sleep(0.5)
    # pyautogui.press("enter")
    print('update result json: ', name_timeline_file)
    update_result_json(name_timeline_file, item)


def kill_resolve_process():
    configure_resolve_paths()
    resolve = get_resolve()
    if resolve is None:
        print("Không tìm thấy Resolve.exe (cài đặt chuẩn trong Program Files).")
        return 1
    resolve.Exit()
    # Kill all process of resolve

def main() -> int:
    data = get_data_from_excel()
    data_list = format_data_for_restore(data)
    keyboard.add_hotkey("esc", _on_esc)

    for item in data_list:
        if _stop.is_set():
            print("Đã dừng theo Esc.", file=sys.stderr)
            break

        print('start restore: ', item)
        restore_workflow(item)
        time.sleep(1)

if __name__ == "__main__":
    raise SystemExit(main())
    # while True:
    #     try:
    #         code = main()
    #         if code != 0:
    #             print(
    #                 f"[retry] main() trả về {code}, chạy lại sau 2 giây…",
    #                 file=sys.stderr,
    #             )
    #             # Kill resolve process
    #             kill_resolve_process()
    #             time.sleep(2)
    #             continue
    #         raise SystemExit(0)
    #     except KeyboardInterrupt:
    #         print("\nĐã dừng (KeyboardInterrupt).", file=sys.stderr)
    #         raise SystemExit(130) from None
    #     except Exception:
    #         print(
    #             "[retry] Lỗi không mong đợi, chạy lại main() sau 2 giây…",
    #             file=sys.stderr,
    #         )
    #         import traceback
    #         traceback.print_exc()
    #         time.sleep(2)
