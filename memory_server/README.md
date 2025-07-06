# Mem0 REST API Server

Mem0 provides a REST API server (written using FastAPI). Users can perform all operations through REST endpoints. The API also includes OpenAPI documentation, accessible at `/docs` when the server is running.

## Features

- **Create memories:** Create memories based on messages for a user, agent, or run.
- **Retrieve memories:** Get all memories for a given user, agent, or run.
- **Search memories:** Search stored memories based on a query.
- **Update memories:** Update an existing memory.
- **Delete memories:** Delete a specific memory or all memories for a user, agent, or run.
- **Reset memories:** Reset all memories for a user, agent, or run.
- **OpenAPI Documentation:** Accessible via `/docs` endpoint.

## Running the server

Follow the instructions in the [docs](https://docs.mem0.ai/open-source/features/rest-api) to run the server.

## First start up

The first time ollama docker file starts up it needs to download the models used by the mem0 server.
The mem0 may need to be restarted after the models are finished downloaded.

We also need to create the database on the qdrant server. To create a database run the following command:

```bash
curl -X PUT "http://localhost:6333/collections/test" -H "accept: application/json" -H "Content-Type: application/json" -d '{"vectors":{"size":768,"distance":"Cosine"}}'
```

To list the collections
```bash
curl -X GET "http://localhost:6333/collections" -H "accept: application/json"
```