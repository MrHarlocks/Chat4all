from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.services.file_service import FileService

router = APIRouter()

class UploadUrlRequest(BaseModel):
    filename: str
    mime_type: str
    size: int

class UploadUrlResponse(BaseModel):
    upload_url: str
    file_id: str
    public_url: str
    object_name: str

@router.post("/upload-url", response_model=UploadUrlResponse)
async def get_upload_url(
    request: UploadUrlRequest,
    service: FileService = Depends(FileService)
):
    try:
        result = await service.generate_upload_url(
            filename=request.filename,
            mime_type=request.mime_type,
            size=request.size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
