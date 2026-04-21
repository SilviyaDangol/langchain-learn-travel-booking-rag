from fastapi import UploadFile, File
from pydantic import BaseModel, Field
from uuid import uuid4, UUID
from typing import Literal
class DocumentMetadata(BaseModel):
    session_id: UUID|str
    file_id: str

# class IngestDocumentRequest(BaseModel):
#     file: UploadFile
#     splitter_type: Literal["recursive", "token"]|None= "recursive"
#     session_id: UUID= Field(default_factory=uuid4)
#
#     @classmethod
#     def as_form(
#         cls,
#         file: UploadFile = File(...)
#     ):
#         return cls(file=file)

