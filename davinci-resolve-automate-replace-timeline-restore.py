#!/usr/bin/env python3
"""
Liệt kê tất cả file trong thư mục `original` (mặc định: ./original cạnh script).

  python davinci-resolve-automate-replace-timeline-restore.py
  python davinci-resolve-automate-replace-timeline-restore.py --no-recursive
  python davinci-resolve-automate-replace-timeline-restore.py path/to/other -a
"""
from __future__ import annotations
from pathlib import PureWindowsPath
import argparse
import shutil
import sys
from pathlib import Path
import os

BACKUP_LOCATION = r"C:\\Toan\\Project\\Davinci Restore\\Resolve Project Backups"


def iter_files(root: Path, recursive: bool) -> list[Path]:
    if not root.is_dir():
        return []
    if recursive:
        return sorted(p for p in root.rglob("*") if p.is_file())
    return sorted(p for p in root.iterdir() if p.is_file())

def format_leaf_timeline_path(s: str) -> str:
    p = PureWindowsPath(s)
    parts = p.parts
    return  f"{parts[-2]} - {parts[-1]}"

def main() -> int:
    script_dir = Path(__file__).resolve().parent
    default_original = script_dir / "original"

    parser = argparse.ArgumentParser(
        description="Liệt kê tất cả file trong thư mục original (hoặc folder chỉ định).",
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help=f"Thư mục gốc (mặc định: {default_original})",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Chỉ file ngay trong folder, không đệ quy (mặc định: đệ quy toàn bộ cây).",
    )
    parser.add_argument(
        "-a",
        "--absolute",
        action="store_true",
        help="In đường dẫn tuyệt đối.",
    )
    args = parser.parse_args()

    root = Path(args.folder).expanduser() if args.folder else default_original
    root = root.resolve()

    if not root.is_dir():
        print(f"Không tìm thấy thư mục: {root}", file=sys.stderr)
        return 1

    files = iter_files(root, recursive=not args.no_recursive)
    all_files = []
    for p in files:
        out = p.resolve() if args.absolute else p.relative_to(root)
        formatted_name = format_leaf_timeline_path(out)
        all_files.append({"name": formatted_name, "path": out})
    
    files_backup = iter_files(Path(BACKUP_LOCATION), recursive=not args.no_recursive)
    for p in files_backup:
        filename = p.name
        # Find the file in all_files
        for file in all_files:
            # include the extension
            if file["name"] in filename:
                # Copy the file to the backup location
                # Get the directory of the file
                original_path = os.path.abspath(Path('original') / file["path"])
                backup_path = os.path.abspath(Path(BACKUP_LOCATION) / p)
                shutil.copy(original_path, backup_path)
                break


    return 0


if __name__ == "__main__":
    raise SystemExit(main())
