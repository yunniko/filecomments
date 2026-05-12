import errno
import os

XATTR_KEY = "user.comment"
_ENOATTR = getattr(errno, "ENOATTR", errno.ENODATA)


def set_comment(path: str, comment: str) -> None:
    os.setxattr(path, XATTR_KEY, comment.encode("utf-8"))


def get_comment(path: str) -> str | None:
    try:
        return os.getxattr(path, XATTR_KEY).decode("utf-8")
    except OSError as e:
        if e.errno == _ENOATTR:
            return None
        raise


def remove_comment(path: str) -> bool:
    try:
        os.removexattr(path, XATTR_KEY)
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
