# filecomments

Attach text comments to any file or directory on Linux. Comments are stored as extended attributes (`user.comment` xattr) and shown alongside `ls` output.

## Requirements

- Linux
- Python 3.10+
- Filesystem with xattr support: ext4, btrfs, xfs *(not tmpfs or FAT32)*

## Install

```bash
git clone <url>
cd filecomments
bash install.sh
```

The script checks all requirements, installs `cmt` and `cls` to `~/.local/bin`, and optionally patches `~/.bashrc` to make `cp` preserve xattrs by default.

Make sure `~/.local/bin` is in your `PATH` (it is by default on most modern distros).

## Usage

### cmt — manage comments

```bash
cmt <path> "text"          # set a comment (shorthand)
cmt set <path> "text"      # set a comment
cmt get <path>             # print a comment
cmt rm  <path>             # remove a comment
cmt ls  [dir]              # list all comments in a directory
cmt ls  [dir] --json       # same, as JSON
cmt cp  <src> <dst>        # copy file and carry its comment
cmt mv  <src> <dst>        # move file and carry its comment
```

### cls — ls with comments

```bash
cls [path...]              # long listing with comments shown in yellow
cls -a [path...]           # include hidden files
cls -H [path...]           # human-readable sizes
```

## Programmatic API

```python
import sys
sys.path.insert(0, "/path/to/filecomments")
import filecomments

filecomments.set_comment("/path/to/file", "my note")
filecomments.get_comment("/path/to/file")     # str | None
filecomments.remove_comment("/path/to/file")  # bool
filecomments.list_comments("/some/dir")       # dict[name, comment]
```

## How comments travel with files

| Operation | Comment preserved? |
|---|---|
| `mv` within same filesystem | yes — inode moves, xattr stays |
| `cmt mv src dst` | yes — works across filesystems too |
| `cmt cp src dst` | yes |
| `cp --preserve=xattr src dst` | yes |
| Plain `cp src dst` | no |
| `scp`, `git`, USB copy | no |

If you opted in during install, plain `cp` is aliased to `cp --preserve=xattr` in your shell.
