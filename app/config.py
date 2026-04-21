from dotenv import load_dotenv
load_dotenv()
import os

class Config:
    PINECONE_DEFAULT_API = os.getenv('PINECONE_DEFAULT_API')
    PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME')
    # Pinecone namespace for holiday-catalog PDF chunks; user uploads stay in the default namespace.
    PINECONE_DESTINATIONS_NAMESPACE = os.getenv(
        'PINECONE_DESTINATIONS_NAMESPACE', 'holiday-destinations'
    )
    DB_URL = os.getenv('DATABASE_URL')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')