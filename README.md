# filecomments

Attach text comments to any file or directory. Comments are stored as filesystem metadata and shown alongside directory listings.

## Requirements

| | Linux | Windows |
|---|---|---|
| OS | any distro | Windows 10+ |
| Python | 3.10+ | 3.10+ |
| Filesystem | ext4, btrfs, xfs (xattr) | NTFS (ADS) |

Comments use **extended attributes** on Linux and **Alternate Data Streams** on Windows — both are filesystem-native metadata and don't affect file content.

## Install

**Linux:**
```bash
git clone <url>
cd filecomments
bash install.sh
```

**Windows (PowerShell):**
```powershell
git clone <url>
cd filecomments
.\install.ps1
```

Both scripts check requirements, install commands to `~/.local/bin`, and exit with a clear error if anything is missing.

## Commands

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

### lsc — directory listing with comments

```bash
lsc [path...]              # long listing with comments in yellow
lsc -a [path...]           # include hidden files
lsc -H [path...]           # human-readable sizes
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

| Operation | Linux | Windows |
|---|---|---|
| `mv` within same filesystem | yes | yes |
| `cmt mv src dst` | yes (cross-fs too) | yes (cross-drive too) |
| `cmt cp src dst` | yes | yes |
| `cp --preserve=xattr` | yes | n/a |
| `robocopy /COPYALL` | n/a | yes |
| Plain `cp` / Explorer copy | no | no |
| `scp`, `git`, USB copy | no | no |

Linux install optionally patches `~/.bashrc` so plain `cp` preserves xattrs automatically.
