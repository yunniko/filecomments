import argparse
import json
import shutil
import signal
import sys
from pathlib import Path

from .store import get_comment, list_comments, remove_comment, set_comment


def _resolve(path: str) -> str:
    return str(Path(path).resolve())


def _dst_path(src: str, dst: str) -> str:
    """Resolve the actual destination path when dst may be a directory."""
    return str(Path(dst) / Path(src).name) if Path(dst).is_dir() else dst


def _read_comment(path: str, label: str) -> str | None:
    """Read comment, warning but not aborting if unreadable."""
    try:
        return get_comment(path)
    except OSError as e:
        print(f"cmt: warning: could not read comment from {label}: {e.strerror}", file=sys.stderr)
        return None


def _write_comment(path: str, label: str, comment: str) -> None:
    """Write comment, warning but not aborting if unwritable."""
    try:
        set_comment(path, comment)
    except OSError as e:
        print(f"cmt: warning: could not set comment on {label}: {e.strerror}", file=sys.stderr)


def cmd_set(args: argparse.Namespace) -> int:
    try:
        set_comment(_resolve(args.path), args.comment)
    except OSError as e:
        print(f"cmt: {args.path}: {e.strerror}", file=sys.stderr)
        return 1
    print(f"comment set on {args.path}")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    try:
        comment = get_comment(_resolve(args.path))
    except OSError as e:
        print(f"cmt: {args.path}: {e.strerror}", file=sys.stderr)
        return 1
    if comment is None:
        print(f"cmt: {args.path}: no comment set", file=sys.stderr)
        return 1
    print(comment)
    return 0


def cmd_rm(args: argparse.Namespace) -> int:
    try:
        removed = remove_comment(_resolve(args.path))
    except OSError as e:
        print(f"cmt: {args.path}: {e.strerror}", file=sys.stderr)
        return 1
    if not removed:
        print(f"cmt: {args.path}: no comment set", file=sys.stderr)
        return 1
    print(f"comment removed from {args.path}")
    return 0


def cmd_ls(args: argparse.Namespace) -> int:
    try:
        comments = list_comments(_resolve(args.dir))
    except OSError as e:
        print(f"cmt: {args.dir}: {e.strerror}", file=sys.stderr)
        return 1
    if not comments:
        return 0
    if args.json:
        print(json.dumps(comments, ensure_ascii=False, indent=2))
    else:
        for name, comment in sorted(comments.items()):
            print(f"{name}\t{comment}")
    return 0


def cmd_cp(args: argparse.Namespace) -> int:
    src, dst = args.src, args.dst
    comment = _read_comment(src, src)
    try:
        shutil.copy2(src, dst)
    except OSError as e:
        print(f"cmt: cp {src} -> {dst}: {e.strerror}", file=sys.stderr)
        return 1
    if comment:
        _write_comment(_dst_path(src, dst), dst, comment)
    return 0


def cmd_mv(args: argparse.Namespace) -> int:
    src, dst = args.src, args.dst
    comment = _read_comment(src, src)
    actual_dst = _dst_path(src, dst)
    try:
        shutil.move(src, dst)
    except OSError as e:
        print(f"cmt: mv {src} -> {dst}: {e.strerror}", file=sys.stderr)
        return 1
    if comment:
        _write_comment(actual_dst, dst, comment)
    return 0


_SUBCOMMANDS = {"set", "get", "rm", "ls", "cp", "mv"}


def main() -> None:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    if len(sys.argv) > 1 and sys.argv[1] not in _SUBCOMMANDS and not sys.argv[1].startswith("-"):
        sys.argv.insert(1, "set")

    parser = argparse.ArgumentParser(
        prog="cmt",
        description="Set, get, or remove comments on files and directories",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_set = sub.add_parser("set", help="set a comment")
    p_set.add_argument("path")
    p_set.add_argument("comment")

    p_get = sub.add_parser("get", help="print a comment")
    p_get.add_argument("path")

    p_rm = sub.add_parser("rm", help="remove a comment")
    p_rm.add_argument("path")

    p_ls = sub.add_parser("ls", help="list all comments in a directory")
    p_ls.add_argument("dir", nargs="?", default=".")
    p_ls.add_argument("--json", action="store_true", help="output as JSON")

    p_cp = sub.add_parser("cp", help="copy a file and its comment")
    p_cp.add_argument("src")
    p_cp.add_argument("dst")

    p_mv = sub.add_parser("mv", help="move a file and its comment")
    p_mv.add_argument("src")
    p_mv.add_argument("dst")

    args = parser.parse_args()
    dispatch = {
        "set": cmd_set, "get": cmd_get, "rm": cmd_rm, "ls": cmd_ls,
        "cp": cmd_cp, "mv": cmd_mv,
    }
    sys.exit(dispatch[args.cmd](args))
