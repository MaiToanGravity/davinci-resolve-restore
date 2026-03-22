#!/usr/bin/env python3
"""
Tạo cây bin trong Media Pool theo path trong output/data.json (trường "name").

Ví dụ name: Nichols\\Studio\\<uuid>\\<uuid>  → tạo lồng Nichols → Studio → …

Path cha đã có trong Media Pool (hoặc đã tạo ở dòng JSON trước) được tái sử dụng; chỉ tạo thêm
các cấp còn thiếu bên trong folder cha đó.

Sau mỗi path, trong folder lá sẽ tạo một timeline trống (tên mặc định = phần cuối path), trừ khi
đã có timeline trùng tên trong project hoặc dùng --skip-timeline.

Yêu cầu: DaVinci Resolve Studio đang chạy và một dự án đang mở.

  python davinci-resolve-automate-bins.py
  python davinci-resolve-automate-bins.py --json output/data.json --limit 5
  python davinci-resolve-automate-bins.py --skip-timeline
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from utils import get_resolve


def _configure_stdio_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if reconf is None:
            continue
        try:
            reconf(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def _path_to_segments(rel_path: str) -> list[str]:
    s = (rel_path or "").replace("/", "\\")
    parts = [p.strip() for p in s.split("\\")]
    return [p for p in parts if p]


def _iter_subfolders(parent):
    subs = parent.GetSubFolders()
    if subs is None:
        return []
    if isinstance(subs, (list, tuple)):
        return list(subs)
    try:
        return list(subs)
    except TypeError:
        return [subs]


def _subfolder_named(parent, segment: str):
    for folder in _iter_subfolders(parent):
        try:
            if folder.GetName() == segment:
                return folder
        except Exception:
            continue
    return None


def ensure_bin_path(
    mp,
    root,
    segments: list[str],
    folder_cache: dict[tuple[str, ...], object],
) -> object | None:
    """
    Đi từng cấp: nếu bin con đã có (trong Resolve hoặc đã gặp ở dòng JSON trước) thì vào đó;
    chỉ AddSubFolder cho các cấp chưa có.
    """
    current = root
    for depth, part in enumerate(segments):
        key: tuple[str, ...] = tuple(segments[: depth + 1])
        cached = folder_cache.get(key)
        if cached is not None:
            current = cached
            continue

        nxt = _subfolder_named(current, part)
        if nxt is None:
            nxt = mp.AddSubFolder(current, part)
            if nxt is None:
                return None

        folder_cache[key] = nxt
        current = nxt
    return current


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


def _project_has_timeline_named(project, name: str) -> bool:
    try:
        n = project.GetTimelineCount()
    except Exception:
        return False
    for i in range(1, int(n) + 1):
        try:
            tl = project.GetTimelineByIndex(i)
            if tl is not None and tl.GetName() == name:
                return True
        except Exception:
            continue
    return False


def _create_timeline_in_leaf_bin(mp, project, leaf, timeline_name: str) -> bool:
    if _project_has_timeline_named(project, timeline_name):
        return True
    if not mp.SetCurrentFolder(leaf):
        print(
            f"[automate-bins] Không SetCurrentFolder cho bin lá — bỏ tạo timeline {timeline_name!r}.",
            file=sys.stderr,
        )
        return False
    tl = mp.CreateEmptyTimeline(timeline_name)
    if tl is None:
        print(
            f"[automate-bins] CreateEmptyTimeline({timeline_name!r}) thất bại.",
            file=sys.stderr,
        )
        return False
    return True


def create_bins_from_json(
    data_path: Path,
    limit: int | None,
    *,
    skip_timeline: bool = False,
) -> int:
    project = get_current_project()
    if project is None:
        return 1

    mp = project.GetMediaPool()
    if mp is None:
        print("[automate-bins] Không lấy được Media Pool.", file=sys.stderr)
        return 1

    root = mp.GetRootFolder()
    if root is None:
        print("[automate-bins] Không lấy được thư mục gốc Media Pool.", file=sys.stderr)
        return 1

    with data_path.open(encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("[automate-bins] JSON phải là mảng các object.", file=sys.stderr)
        return 1

    ok_count = 0
    fail_count = 0
    timeline_ok = 0
    timeline_fail = 0
    folder_cache: dict[tuple[str, ...], object] = {}

    for i, item in enumerate(data):
        if limit is not None and i >= limit:
            break
        if not isinstance(item, dict):
            print(f"[automate-bins] Bỏ qua phần tử #{i}: không phải object.", file=sys.stderr)
            fail_count += 1
            continue
        rel = item.get("name")
        if not rel or not isinstance(rel, str):
            print(f"[automate-bins] Bỏ qua phần tử #{i}: thiếu hoặc sai 'name'.", file=sys.stderr)
            fail_count += 1
            continue

        segments = _path_to_segments(rel)
        if not segments:
            print(f"[automate-bins] Bỏ qua phần tử #{i}: path rỗng.", file=sys.stderr)
            fail_count += 1
            continue

        leaf = ensure_bin_path(mp, root, segments, folder_cache)
        print(item["name"])
        if leaf is None:
            print(
                f"[automate-bins] Lỗi tạo path: {rel!r}",
                file=sys.stderr,
            )
            fail_count += 1
        else:
            ok_count += 1
            if not skip_timeline:
                for file in item["files"]:
                    timeline_name = file
                    if _create_timeline_in_leaf_bin(mp, project, leaf, timeline_name):
                        timeline_ok += 1
                    else:
                        timeline_fail += 1

    if not mp.SetCurrentFolder(root):
        print(
            "[automate-bins] Cảnh báo: SetCurrentFolder(root) không thành công.",
            file=sys.stderr,
        )

    msg = f"[automate-bins] Xong: {ok_count} path OK, {fail_count} lỗi/bỏ qua."
    if not skip_timeline:
        msg += f" Timeline: {timeline_ok} OK, {timeline_fail} lỗi."
    print(msg)
    if fail_count or timeline_fail:
        return 1
    return 0


def main() -> int:
    _configure_stdio_utf8()
    script_dir = Path(__file__).resolve().parent
    default_json = script_dir / "output" / "data.json"

    parser = argparse.ArgumentParser(
        description="Tạo cây bin trong Media Pool theo trường 'name' trong JSON.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=default_json,
        metavar="PATH",
        help=f"File JSON (mặc định: {default_json})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Chỉ xử lý N phần tử đầu (thử nhanh).",
    )
    parser.add_argument(
        "--skip-timeline",
        action="store_true",
        help="Chỉ tạo bin, không tạo timeline trống trong folder lá.",
    )
    args = parser.parse_args()

    data_path = args.json.resolve()
    if not data_path.is_file():
        print(f"[automate-bins] Không tìm thấy file: {data_path}", file=sys.stderr)
        return 1

    return create_bins_from_json(
        data_path,
        args.limit,
        skip_timeline=args.skip_timeline,
    )


if __name__ == "__main__":
    raise SystemExit(main())
