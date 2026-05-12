import argparse
import os
import platform
import signal
import stat
import sys
import time

from .store import get_comment

_RESET = "\033[0m"
_BOLD = "\033[1m"
_BLUE = "\033[94m"
_CYAN = "\033[96m"
_GREEN = "\033[92m"
_YELLOW = "\033[33m"

# Enable ANSI color codes on Windows (Windows 10+)
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7
        )
    except Exception:
        pass

try:
    import grp as _grp
    import pwd as _pwd
    _HAS_PWD = True
except ImportError:
    _HAS_PWD = False


def _mode_str(mode: int) -> str:
    if stat.S_ISDIR(mode):
        lead = "d"
    elif stat.S_ISLNK(mode):
        lead = "l"
    elif stat.S_ISFIFO(mode):
        lead = "p"
    elif stat.S_ISSOCK(mode):
        lead = "s"
    elif stat.S_ISBLK(mode):
        lead = "b"
    elif stat.S_ISCHR(mode):
        lead = "c"
    else:
        lead = "-"
    bits = ""
    for r_bit, w_bit, x_bit in [
        (stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR),
        (stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP),
        (stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH),
    ]:
        bits += ("r" if mode & r_bit else "-")
        bits += ("w" if mode & w_bit else "-")
        bits += ("x" if mode & x_bit else "-")
    return lead + bits


def _human_size(size: int) -> str:
    for unit in ("", "K", "M", "G", "T", "P"):
        if abs(size) < 1024:
            return f"{size:.0f}{unit}" if unit == "" else f"{size:.1f}{unit}"
        size //= 1024  # type: ignore[assignment]
    return f"{size}E"


def _colorize(entry: os.DirEntry, name: str, use_color: bool) -> str:
    if not use_color:
        return name
    try:
        st = entry.stat(follow_symlinks=False)
    except OSError:
        return name
    if entry.is_symlink():
        return _CYAN + name + _RESET
    if stat.S_ISDIR(st.st_mode):
        return _BLUE + _BOLD + name + _RESET
    if st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        return _GREEN + name + _RESET
    return name


def _owner_group(st: os.stat_result) -> tuple[str, str]:
    if _HAS_PWD:
        try:
            owner = _pwd.getpwuid(st.st_uid).pw_name
        except KeyError:
            owner = str(st.st_uid)
        try:
            group = _grp.getgrgid(st.st_gid).gr_name
        except KeyError:
            group = str(st.st_gid)
    else:
        owner = str(st.st_uid)
        group = str(st.st_gid)
    return owner, group


def _list_long(entries: list[os.DirEntry], human: bool, use_color: bool) -> None:
    rows = []
    total_blocks = 0

    for entry in entries:
        try:
            st = entry.stat(follow_symlinks=False)
        except OSError:
            continue

        # st_blocks is Linux/macOS only; approximate from file size on Windows
        total_blocks += getattr(st, "st_blocks", (st.st_size + 511) // 512)

        owner, group = _owner_group(st)
        size_str = _human_size(st.st_size) if human else str(st.st_size)

        mtime = time.localtime(st.st_mtime)
        if mtime.tm_year == time.localtime().tm_year:
            date_str = time.strftime("%b %d %H:%M", mtime)
        else:
            date_str = time.strftime("%b %d  %Y", mtime)

        display = entry.name
        if stat.S_ISLNK(st.st_mode):
            try:
                display = f"{entry.name} -> {os.readlink(entry.path)}"
            except OSError:
                pass

        try:
            comment = get_comment(entry.path)
        except OSError:
            comment = None

        rows.append(
            dict(
                mode=_mode_str(st.st_mode),
                nlink=str(st.st_nlink),
                owner=owner,
                group=group,
                size=size_str,
                date=date_str,
                name=display,
                colored=_colorize(entry, display, use_color),
                comment=comment,
            )
        )

    print(f"total {total_blocks // 2}")
    if not rows:
        return

    nlink_w = max(len(r["nlink"]) for r in rows)
    owner_w = max(len(r["owner"]) for r in rows)
    group_w = max(len(r["group"]) for r in rows)
    size_w = max(len(r["size"]) for r in rows)
    name_w = max(len(r["name"]) for r in rows)

    for r in rows:
        line = (
            f"{r['mode']} "
            f"{r['nlink']:>{nlink_w}} "
            f"{r['owner']:<{owner_w}} "
            f"{r['group']:<{group_w}} "
            f"{r['size']:>{size_w}} "
            f"{r['date']} "
            f"{r['colored']}"
        )
        if r["comment"]:
            pad = " " * (name_w - len(r["name"]))
            tag = f"  # {r['comment']}"
            line += pad + (_YELLOW + tag + _RESET if use_color else tag)
        print(line)


def _scan(path: str, show_hidden: bool) -> list[os.DirEntry] | None:
    try:
        with os.scandir(path) as sc:
            entries = sorted(sc, key=lambda e: e.name.lower())
    except NotADirectoryError:
        print(f"cls: '{path}': Not a directory", file=sys.stderr)
        return None
    except OSError as e:
        print(f"cls: cannot open '{path}': {e.strerror}", file=sys.stderr)
        return None
    if not show_hidden:
        entries = [e for e in entries if not e.name.startswith(".")]
    return entries


def main() -> None:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    parser = argparse.ArgumentParser(
        prog="cls",
        description="ls with file/directory comments",
    )
    parser.add_argument("-a", dest="all", action="store_true", help="show hidden files")
    parser.add_argument("-H", "--human-readable", dest="human", action="store_true")
    parser.add_argument("--no-color", dest="no_color", action="store_true")
    parser.add_argument("paths", nargs="*", default=["."])
    args = parser.parse_args()

    use_color = not args.no_color and sys.stdout.isatty()

    rc = 0
    for i, path in enumerate(args.paths):
        if len(args.paths) > 1:
            if i:
                print()
            print(f"{path}:")
        entries = _scan(path, args.all)
        if entries is None:
            rc = 1
            continue
        _list_long(entries, args.human, use_color)
    sys.exit(rc)
