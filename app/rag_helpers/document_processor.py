from uuid import UUID

from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader
from app.rag_helpers.vectorstore import vector_store,vector_store_for_namespace

from typing import List, Literal
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, TokenTextSplitter
import tempfile
import hashlib
import os


from app.db.schemas.document import DocumentMetadata

"""page_content: a string representing the content;
    metadata: a dict containing arbitrary metadata;
    id: (optional) a string identifier for the document"""
def generate_file_id(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def attach_metadata(docs: List[Document],session_id: UUID,file_id: str) -> List[Document]:
    meta = DocumentMetadata(session_id=str(session_id), file_id=file_id)

    for doc in docs:

        doc.metadata.update(meta.model_dump(mode="json"))

    return docs


async def to_doc(file: UploadFile) -> List[Document]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
    finally:
        os.remove(tmp_path)  # cleanup

    return docs


async def split_documents(docs: List[Document],splitter_type: Literal["recursive", "token"] = "recursive") -> List[Document]:

    if splitter_type == "recursive":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True
        )
    elif splitter_type == "token":
        splitter = TokenTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    else:
        raise ValueError("Invalid splitter type")

    return splitter.split_documents(docs)


async def process_documents(
    file: UploadFile,
    session_id: UUID,
    splitter_type,
    pinecone_namespace: str | None = None,
):
    content = await file.read()
    file_id = generate_file_id(content)
    await file.seek(0)
    docs = await to_doc(file)
    docs = attach_metadata(docs, session_id, file_id)
    split_docs = await split_documents(docs, splitter_type)
    store = vector_store_for_namespace(pinecone_namespace) # if the user is ingesting the holiday destinations catalog, use the destinations namespace in Pinecone.
    vector_ids = store.add_documents(split_docs)
    return vector_ids, file_id, session_id



"""Document(
    page_content="some chunk...",
    metadata={
        "page": 2,
        "session_id": "abc123",
        "file_id": "9f8a7c...",
        "start_index": 400
    }
)"""













