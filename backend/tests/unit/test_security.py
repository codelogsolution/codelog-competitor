import pytest

from app.core.security import is_safe_http_url


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com/path",
        "http://example.com",
    ],
)
def test_accepts_absolute_http_urls(value):
    assert is_safe_http_url(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "",
        None,
        "javascript:alert(1)",
        "file:///etc/passwd",
        "https://",
        "https://user:password@example.com",
        "//example.com/path",
    ],
)
def test_rejects_unsafe_or_incomplete_urls(value):
    assert is_safe_http_url(value) is False
