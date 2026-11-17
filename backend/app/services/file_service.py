import os
import re
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from vercel.blob import sync as blob_sdk


class FileService:

    ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

    @staticmethod
    def _uses_blob_store() -> bool:
        return bool(
            os.environ.get("BLOB_STORE_ID")
            or os.environ.get("BLOB_READ_WRITE_TOKEN")
        )

    @staticmethod
    def validate_file(filename: str) -> None:
        extension = Path(filename).suffix.lower()

        if extension not in FileService.ALLOWED_EXTENSIONS:
            raise ValueError(
                "Unsupported file format. Only CSV and XLSX are allowed."
            )

    @staticmethod
    def save_file(filename: str, content: bytes) -> str:
        FileService.validate_file(filename)

        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if len(content) > max_size:
            raise ValueError(
                f"File exceeds maximum size of "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        if not content:
            raise ValueError("Uploaded file is empty.")

        extension = Path(filename).suffix.lower()
        stored_filename = f"{uuid4().hex}{extension}"

        if FileService._uses_blob_store():
            content_type = (
                "text/csv"
                if extension == ".csv"
                else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            blob_sdk.put_blob(
                stored_filename,
                content,
                access="private",
                content_type=content_type,
            )
            return stored_filename

        backend_dir = Path(__file__).resolve().parents[2]
        upload_dir = (backend_dir / settings.UPLOAD_DIR).resolve()
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / stored_filename
        file_path.write_bytes(content)

        return stored_filename

    @staticmethod
    def read_file(stored_filename: str) -> bytes:
        if not re.fullmatch(r"[a-f0-9]{32}\.(csv|xlsx)", stored_filename or ""):
            raise ValueError("Stored source file reference is invalid.")
        if FileService._uses_blob_store():
            try:
                return blob_sdk.get_blob(stored_filename, access="private").body
            except blob_sdk.BlobNotFoundError as exc:
                raise FileNotFoundError(
                    "Uploaded source file is no longer available."
                ) from exc

        backend_dir = Path(__file__).resolve().parents[2]
        upload_dir = (backend_dir / settings.UPLOAD_DIR).resolve()
        file_path = (upload_dir / stored_filename).resolve()
        if file_path.parent != upload_dir or not file_path.is_file():
            raise FileNotFoundError("Uploaded source file is no longer available.")
        return file_path.read_bytes()

    @staticmethod
    def delete_file(stored_filename: str) -> None:
        if not re.fullmatch(r"[a-f0-9]{32}\.(csv|xlsx)", stored_filename or ""):
            raise ValueError("Stored source file reference is invalid.")
        if FileService._uses_blob_store():
            blob_sdk.delete_blob(stored_filename)
            return

        backend_dir = Path(__file__).resolve().parents[2]
        upload_dir = (backend_dir / settings.UPLOAD_DIR).resolve()
        file_path = (upload_dir / stored_filename).resolve()
        if file_path.parent != upload_dir:
            raise ValueError("Stored source file path is invalid.")
        file_path.unlink(missing_ok=True)
