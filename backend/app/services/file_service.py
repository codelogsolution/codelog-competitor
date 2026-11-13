from pathlib import Path
from uuid import uuid4

from app.core.config import settings


class FileService:

    ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

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

        backend_dir = Path(__file__).resolve().parents[2]
        upload_dir = (backend_dir / settings.UPLOAD_DIR).resolve()

        upload_dir.mkdir(parents=True, exist_ok=True)

        extension = Path(filename).suffix.lower()
        stored_filename = f"{uuid4().hex}{extension}"

        file_path = upload_dir / stored_filename
        file_path.write_bytes(content)

        return stored_filename