
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.schemas.upload import UploadResponse
from app.services.file_service import FileService
from app.services.validation_service import ValidationService

router = APIRouter()

@router.post("", response_model=UploadResponse)
async def upload_competitor_file(
    file: UploadFile = File(...),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    try:

        # 1. Check file size
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        content = await file.read(max_size + 1)

        if len(content) > max_size:
            raise ValueError(
                f"File exceeds maximum size of "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        # 2. Validate file extension
        FileService.validate_file(file.filename)

        # 3. Validate uploaded file content
        report = ValidationService.validate_file(
            filename=file.filename,
            content=content,
        )

        # 4. Save uploaded file
        stored_filename = FileService.save_file(
            filename=file.filename,
            content=content,
        )

        # 5. Return API response
        return UploadResponse(
            original_filename=file.filename,
            stored_filename=stored_filename,
            **report,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    finally:

        await file.close()
