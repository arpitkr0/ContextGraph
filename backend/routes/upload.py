from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.ingestion.file_manager import list_sources, remove_upload, save_upload


router = APIRouter()


@router.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    try:
        return save_upload(file.filename or "", await file.read())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/upload/{filename}")
def delete_upload(filename: str) -> dict:
    try:
        return remove_upload(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/sources")
def sources() -> dict:
    return {"files": list_sources()}
