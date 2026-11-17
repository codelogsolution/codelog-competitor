from types import SimpleNamespace

import pytest

from app.services.file_service import FileService
from vercel.blob import sync as blob_sdk


def test_private_blob_round_trip_uses_private_access(monkeypatch):
    calls = []
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "test-token")
    monkeypatch.setattr(
        blob_sdk,
        "put_blob",
        lambda *args, **kwargs: calls.append(("put", args, kwargs)),
    )
    monkeypatch.setattr(
        blob_sdk,
        "get_blob",
        lambda *args, **kwargs: (
            calls.append(("get", args, kwargs))
            or SimpleNamespace(body=b"stored content")
        ),
    )
    monkeypatch.setattr(
        blob_sdk,
        "delete_blob",
        lambda *args, **kwargs: calls.append(("delete", args, kwargs)),
    )

    filename = FileService.save_file("report.csv", b"stored content")

    assert FileService.read_file(filename) == b"stored content"
    FileService.delete_file(filename)

    assert calls[0][0:2] == ("put", (filename, b"stored content"))
    assert calls[0][2]["access"] == "private"
    assert calls[1] == ("get", (filename,), {"access": "private"})
    assert calls[2] == ("delete", (filename,), {})


def test_missing_private_blob_is_reported_as_missing_file(monkeypatch):
    monkeypatch.setenv("BLOB_READ_WRITE_TOKEN", "test-token")

    def missing_blob(*args, **kwargs):
        raise blob_sdk.BlobNotFoundError("missing")

    monkeypatch.setattr(blob_sdk, "get_blob", missing_blob)

    with pytest.raises(FileNotFoundError, match="no longer available"):
        FileService.read_file("a" * 32 + ".csv")
