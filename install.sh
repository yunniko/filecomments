#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

echo "checking requirements..."

# Linux
if [[ "$(uname -s)" != "Linux" ]]; then
    echo "error: filecomments requires Linux (xattr is Linux-only)"
    exit 1
fi
echo "  os: ok (Linux)"

# Python 3.10+
if ! command -v python3 &>/dev/null; then
    echo "error: python3 not found — install Python 3.10 or newer"
    exit 1
fi
if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "error: Python 3.10+ required, found Python $PY_VER"
    exit 1
fi
echo "  python: ok ($(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"))"

# xattr support on home filesystem
TMPFILE=$(mktemp "$HOME/.xattr_check_XXXXXX")
if ! python3 -c "import os; os.setxattr('$TMPFILE', 'user.test', b'1')" 2>/dev/null; then
    rm -f "$TMPFILE"
    echo "error: your home filesystem does not support extended attributes"
    echo "       filecomments requires ext4, btrfs, or xfs — tmpfs and FAT32 are not supported"
    exit 1
fi
python3 -c "import os; os.removexattr('$TMPFILE', 'user.test')" 2>/dev/null || true
rm -f "$TMPFILE"
echo "  xattr: ok"

echo ""

# Install commands
mkdir -p "$BIN_DIR"

write_script() {
    local cmd="$1"
    local module="$2"
    cat > "$BIN_DIR/$cmd" << SCRIPT
#!/usr/bin/env python3
import sys
sys.path.insert(0, "$PROJECT_DIR")
from filecomments.$module import main
main()
SCRIPT
    chmod +x "$BIN_DIR/$cmd"
    echo "installed: $BIN_DIR/$cmd"
}

write_script cmt cli
write_script lsc cls

echo ""
read -r -p "add 'cp --preserve=xattr' to ~/.bashrc? [y/N] " reply
if [[ "${reply,,}" == "y" ]]; then
    MARKER="# filecomments: cp --preserve=xattr"
    if grep -qF "$MARKER" "$HOME/.bashrc" 2>/dev/null; then
        echo "already present in ~/.bashrc, skipping"
    else
        cat >> "$HOME/.bashrc" << 'BASHRC'

# filecomments: cp --preserve=xattr
cp() { command cp --preserve=xattr "$@"; }
BASHRC
        echo "added to ~/.bashrc — run 'source ~/.bashrc' or open a new shell to activate"
    fi
fi

echo ""
echo "done — re-run this script if you move the project directory"
