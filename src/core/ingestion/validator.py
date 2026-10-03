from fastapi import HTTPException, UploadFile


async def validate_pdf(upload: UploadFile, max_upload_mb: int) -> None:
    if not upload.filename or not upload.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported.")
    header = await upload.read(5)
    await upload.seek(0)
    if header != b"%PDF-":
        raise HTTPException(status_code=415, detail="Invalid PDF signature.")
    if upload.size and upload.size > max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"PDF exceeds {max_upload_mb} MB limit.")
