from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

from langchain_openai import OpenAIEmbeddings

from app.config import Config


pc = Pinecone(Config.PINECONE_DEFAULT_API)
index = pc.Index(Config.PINECONE_INDEX_NAME)

embeddings = OpenAIEmbeddings(model ="text-embedding-3-small" )
vector_store = PineconeVectorStore(embedding=embeddings, index=index)


def vector_store_for_namespace(namespace: str | None) -> PineconeVectorStore:
    if not namespace:
        return vector_store
    return PineconeVectorStore(embedding=embeddings, index=index, namespace=namespace)


destination_vector_store = vector_store_for_namespace(
    Config.PINECONE_DESTINATIONS_NAMESPACE
)