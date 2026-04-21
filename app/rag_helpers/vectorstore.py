from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone
from pinecone_text.hybrid import hybrid_convex_scale
from pinecone_text.sparse import BM25Encoder

from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from typing import Any
from uuid import uuid4

from app.config import Config


pc = Pinecone(Config.PINECONE_DEFAULT_API)
index = pc.Index(Config.PINECONE_INDEX_NAME)

embeddings = OpenAIEmbeddings(model ="text-embedding-3-small" )
vector_store = PineconeVectorStore(embedding=embeddings, index=index)
bm25_encoder = BM25Encoder.default()


def vector_store_for_namespace(namespace: str | None) -> PineconeVectorStore:
    if not namespace:
        return vector_store
    return PineconeVectorStore(embedding=embeddings, index=index, namespace=namespace)


destination_vector_store = vector_store_for_namespace(
    Config.PINECONE_DESTINATIONS_NAMESPACE
)


def add_documents_hybrid(
    documents: list[Document], namespace: str | None = None
) -> list[str]:
    contents = [doc.page_content for doc in documents]
    dense_vectors = embeddings.embed_documents(contents)
    sparse_vectors = bm25_encoder.encode_documents(contents)

    vectors: list[dict[str, Any]] = []
    vector_ids: list[str] = []
    for doc, dense, sparse in zip(documents, dense_vectors, sparse_vectors):
        doc_id = getattr(doc, "id", None) or str(uuid4())
        metadata = dict(doc.metadata)
        metadata["text"] = doc.page_content
        vectors.append(
            {
                "id": doc_id,
                "values": dense,
                "sparse_values": sparse,
                "metadata": metadata,
            }
        )
        vector_ids.append(doc_id)

    index.upsert(vectors=vectors, namespace=namespace)
    return vector_ids


def hybrid_search(
    query: str,
    k: int,
    namespace: str | None = None,
    alpha: float = 0.5,
) -> list[Document]:
    dense = embeddings.embed_query(query)
    sparse = bm25_encoder.encode_queries(query)
    dense, sparse = hybrid_convex_scale(dense, sparse, alpha=alpha)
    result = index.query(
        vector=dense,
        sparse_vector=sparse,
        top_k=k,
        namespace=namespace,
        include_metadata=True,
    )

    docs: list[Document] = []
    for match in result.matches:
        metadata = dict(match.metadata or {})
        page_content = str(metadata.pop("text", ""))
        docs.append(Document(page_content=page_content, metadata=metadata))
    return docs