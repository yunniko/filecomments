import errno
import os
import platform

_IS_WINDOWS = platform.system() == "Windows"
_XATTR_KEY = "user.comment"
_ADS_STREAM = ":filecomment"

if not _IS_WINDOWS:
    _ENOATTR = getattr(errno, "ENOATTR", errno.ENODATA)


def set_comment(path: str, comment: str) -> None:
    if _IS_WINDOWS:
        with open(path + _ADS_STREAM, "w", encoding="utf-8") as f:
            f.write(comment)
    else:
        os.setxattr(path, _XATTR_KEY, comment.encode("utf-8"))


def get_comment(path: str) -> str | None:
    if _IS_WINDOWS:
        try:
            with open(path + _ADS_STREAM, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None
    else:
        try:
            return os.getxattr(path, _XATTR_KEY).decode("utf-8")
        except OSError as e:
            if e.errno == _ENOATTR:
                return None
            raise


def remove_comment(path: str) -> bool:
    if _IS_WINDOWS:
        try:
            os.remove(path + _ADS_STREAM)
            return True
        except FileNotFoundError:
            return False
    else:
        try:
            os.removexattr(path, _XATTR_KEY)
            return True
        except OSError as e:
            if e.errno == _ENOATTR:
                return False
            raise


def list_comments(directory: str = ".") -> dict[str, str]:
    result: dict[str, str] = {}
    with os.scandir(directory) as scanner:
        for entry in scanner:
            try:
                comment = get_comment(entry.path)
            except OSError:
                continue
            if comment is not None:
                result[entry.name] = comment
    return result
