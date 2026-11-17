import pytest

from app.database.url import normalize_database_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "postgres://user:pass@db.example.test/komp",
            "postgresql+psycopg://user:pass@db.example.test/komp",
        ),
        (
            "postgresql://user:pass@db.example.test/komp",
            "postgresql+psycopg://user:pass@db.example.test/komp",
        ),
        (
            "postgresql+psycopg://user:pass@db.example.test/komp",
            "postgresql+psycopg://user:pass@db.example.test/komp",
        ),
        ("sqlite:////tmp/komp-ci.db", "sqlite:////tmp/komp-ci.db"),
    ],
)
def test_normalize_database_url(url: str, expected: str) -> None:
    assert normalize_database_url(url) == expected
