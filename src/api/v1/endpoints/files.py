from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.services.file_service import FileService
from uuid import UUID
from typing import Optional

router = APIRouter()

class UploadUrlRequest(BaseModel):
    filename: str
    mime_type: str
    size: int
    uploader_id: UUID
    conversation_id: Optional[UUID] = None
    checksum: Optional[str] = None

class UploadUrlResponse(BaseModel):
    upload_url: str
    file_id: str
    public_url: str
    object_name: str

class DownloadUrlResponse(BaseModel):
    download_url: str

@router.post("/upload-url", response_model=UploadUrlResponse, summary="Gerar URL de upload", description="Gera uma URL pré-assinada para upload direto de arquivos para o armazenamento (S3/MinIO).")
async def get_upload_url(
    request: UploadUrlRequest,
    service: FileService = Depends(FileService)
):
    """
    Solicita uma URL para upload de arquivo.
    
    - **filename**: Nome do arquivo
    - **mime_type**: Tipo MIME do arquivo
    - **size**: Tamanho em bytes
    - **uploader_id**: ID do usuário que está enviando
    - **conversation_id**: ID da conversa associada (opcional)
    - **checksum**: Hash do arquivo para verificação (opcional)
    """
    try:
        result = await service.generate_upload_url(
            filename=request.filename,
            mime_type=request.mime_type,
            size=request.size,
            uploader_id=request.uploader_id,
            conversation_id=request.conversation_id,
            checksum=request.checksum
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}/download-url", response_model=DownloadUrlResponse, summary="Gerar URL de download", description="Gera uma URL pré-assinada temporária para download de um arquivo.")
async def get_download_url(
    file_id: UUID,
    service: FileService = Depends(FileService)
):
    """
    Solicita uma URL para download de arquivo.
    """
    try:
        url = await service.generate_download_url(file_id)
        if not url:
            raise HTTPException(status_code=404, detail="File not found")
        return {"download_url": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

