from urllib.parse import urlparse


def is_safe_http_url(value: str | None) -> bool:
    """Return True only for absolute HTTP(S) URLs with a hostname.

    This validates link shape; it does not fetch the URL or guarantee that the
    destination is trustworthy.
    """
    if not value:
        return False
    try:
        parsed = urlparse(str(value).strip())
        return (
            parsed.scheme.lower() in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False
