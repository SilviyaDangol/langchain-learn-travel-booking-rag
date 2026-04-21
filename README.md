# Travel booking rag

This is a langchain project that can:

- ingest `.pdf` files into Pinecone
- create chat sessions
- answer user messages with an AI agent
- store persistant data in PostgreSQL, uses Pinecone as vectorDB

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Pinecone account
- OpenAI API key

## Setup

1. Install dependencies:


uv sync
```

2. Create your environment file:

```bash
cp .env.example .env
```

3
## Run locally

Start the API:

```bash
uv run fastapi dev main.py --host 0.0.0.0 --port 8000
```

API docs:
- Swagger UI: `http://localhost:8000/docs`

## Run with Docker

```bash
docker compose up --build
```

## Main endpoints

- `POST /ingest`
  - Upload a file (`.pdf` )
  - has options to ingest a travel guide
  - tools use the docs to give recommendations regarding travel spots
  
- `POST /chat/new`
  - Create a new conversation
  - (creates a conversation id )
  - 
- `POST /chat/{conversation_id}`
  - Send a message in a conversation,
  - continues from the conversation id generated from /chat/new
  - remembers preferences and conversation history
- `POST /ask/`
  - Quick chat flow (creates a conversation automatically), has no memory 

## Notes
- Make sure your database is running before starting the app.
- use pdf in travel_guide example or similar to get agent to recommend destination accordingly