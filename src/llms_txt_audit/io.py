from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class InputError(RuntimeError):
    """Raised when the audit target cannot be read."""


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def read_target(target: str, *, timeout: float = 10.0, discover: bool = False) -> tuple[str, str]:
    if is_url(target):
        url = _discover_url(target) if discover else target
        return url, _read_url(url, timeout=timeout)

    path = Path(target)
    if path.is_dir():
        path = path / "llms.txt"
    if not path.exists():
        raise InputError(f"File not found: {path}")
    if not path.is_file():
        raise InputError(f"Not a file: {path}")
    return str(path), path.read_text(encoding="utf-8")


def _discover_url(target: str) -> str:
    parsed = urlparse(target)
    if parsed.path and parsed.path.rstrip("/").endswith("llms.txt"):
        return target
    return f"{parsed.scheme}://{parsed.netloc}/llms.txt"


def _read_url(url: str, *, timeout: float) -> str:
    request = Request(url, headers={"User-Agent": "llms-txt-audit/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except HTTPError as exc:
        raise InputError(f"HTTP {exc.code} while reading {url}") from exc
    except URLError as exc:
        raise InputError(f"Could not read {url}: {exc.reason}") from exc
