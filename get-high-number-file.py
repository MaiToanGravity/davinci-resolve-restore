#!/usr/bin/env python3
"""
Liệt kê file hoặc thư mục con trong `original` (mặc định: ./original so với thư mục chứa script).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def iter_files(root: Path, recursive: bool) -> list[Path]:
    """Trả về danh sách file (không gồm thư mục), sắp xếp theo đường dẫn."""
    if not root.is_dir():
        return []
    if recursive:
        paths = sorted(p for p in root.rglob("*") if p.is_file())
    else:
        paths = sorted(p for p in root.iterdir() if p.is_file())
    return paths


def iter_dirs(root: Path, recursive: bool) -> list[Path]:
    """Trả về danh sách thư mục con (không gồm file), sắp xếp theo đường dẫn."""
    if not root.is_dir():
        return []
    if recursive:
        paths = sorted(p for p in root.rglob("*") if p.is_dir())
    else:
        paths = sorted(p for p in root.iterdir() if p.is_dir())
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lấy danh sách file hoặc thư mục con trong thư mục original."
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Đường dẫn thư mục (mặc định: thư_mục_script/original)",
    )
    parser.add_argument(
        "--folders",
        action="store_true",
        help="Liệt kê thư mục con thay vì file",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Đệ quy: gồm cả nội dung trong thư mục con",
    )
    parser.add_argument(
        "-a",
        "--absolute",
        action="store_true",
        help="In đường dẫn tuyệt đối",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    root = Path(args.folder).expanduser() if args.folder else script_dir / "original"
    root = root.resolve()

    if not root.is_dir():
        print(f"Không tìm thấy thư mục: {root}", file=sys.stderr)
        print("Tạo thư mục `original` cạnh script hoặc truyền đường dẫn.", file=sys.stderr)
        return 1

    items = (
        iter_dirs(root, args.recursive)
        if args.folders
        else iter_files(root, args.recursive)
    )
    high_number_files = 0
    high_number_folder = ""
    numbers_files = 0
    for p in items:
        path = p.resolve() if args.absolute else p.relative_to(root)
        # Only return path have 4 parts
        # if len(path.parts) != 4:
        #     continue
        if len(path.parts) == 4:
            # Get list files in folder
            files = iter_files(p, args.recursive)
            if len(files) > high_number_files:
                high_number_files = len(files)
                high_number_folder = path
            numbers_files += len(files)
            continue
    print(f"High number files: {high_number_files} in folder: {high_number_folder}")
    print(f"Total files: {numbers_files}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
