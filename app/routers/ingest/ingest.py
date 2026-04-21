import uuid
from typing import Literal
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form
from fastapi.responses import JSONResponse

from app.db.db import DBSessionDep
from app.db.models.user_metadata import FileSession
from app.config import Config
from app.rag_helpers.document_processor import process_documents

router: APIRouter = APIRouter(tags=["Part 1 INGEST"])
@router.post("/ingest")
async def ingest_document(db: DBSessionDep, file: UploadFile, splitter_type: Literal["recursive", "token"] | None, destination_catalog: bool = Form(False),) -> JSONResponse:
    """
    Ingests a file and saves it to the pinecone vector database
    """
    logging.warning("WARNING TEST")
    session_id = uuid.uuid4()
    if file.filename == '':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file uploaded")
    if not (file.filename.endswith('.pdf') or file.filename.endswith('.txt')):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")

    # If the user is ingesting the holiday destinations catalog, use the destinations namespace in Pinecone.
    catalog_ns = Config.PINECONE_DESTINATIONS_NAMESPACE if destination_catalog else None
    process_pdf = await process_documents(
        file, session_id, splitter_type, pinecone_namespace=catalog_ns
    )
    if not process_pdf:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to process file")



    db.add(FileSession(
        filename=file.filename,
        file_id=process_pdf[2],
        split_type=splitter_type,

    ))
    db.commit()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "File ingested successfully",
            "file_id": str(process_pdf[2]),
        },
    )
