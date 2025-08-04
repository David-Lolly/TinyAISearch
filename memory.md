# Project Understanding: TinyAISearch

## Overview
TinyAISearch is a lightweight AI search project implementing a complete RAG (Retrieval Augmented Generation) process. It features smart search planning, multiple retrieval strategies (V1 for traditional RAG and V2 for page-level retrieval), and is highly extensible, supporting any OpenAI API-compatible LLM. The project has a modern frontend built with Vue 3 + Vite, supporting multi-user and multi-session capabilities.

## Architecture

### Backend (Python)
*   **Framework:** FastAPI with Uvicorn.
*   **Main Entry:** `AISearchServer.py`.
*   **Core Modules (`utils/`):**
    *   `config_manager.py`: Handles application configuration.
    *   `crawl_web.py`: Web crawling functionality.
    *   `database.py`: Manages database interactions (likely SQLite for local persistence).
    *   `keywords_extract.py`: Extracts keywords and generates search plans.
    *   `pages_retrieve.py`: Implements V2 (page-level) retrieval.
    *   `response.py`: Generates LLM responses.
    *   `retrieval.py`: Implements V1 (traditional RAG) retrieval.
    *   `search_web.py`: Wraps search engine functionalities.
*   **Dependencies (inferred):** `fastapi`, `uvicorn`, `pydantic`, `langchain_core`, `openai`, `httpx`.
*   **Logging:** Logs to `./logs/app.log`.
*   **Database Initialization:** `db.create_tables()` is called during application startup (`lifespan` function).

### Frontend (Vue 3 + Vite)
*   **Location:** `frontend/` directory.
*   **Structure:** Contains reusable UI components (`components/`), API service wrappers (`services/`), and page-level components (`views/`).

## Deployment

*   **Local:** Requires Node.js (v18+), Python (v3.10), and Conda. Backend and frontend are run in separate terminals.
*   **Containerized:** Dockerfiles (`backend.Dockerfile`, `frontend.Dockerfile`) and `docker-compose.yml` are present, indicating support for Docker deployment.

## Problem Statement (Chat History Issue)

When deployed using Docker containers, the chat history is not displayed, and chat records are not retrieved, although new chat functionality works correctly. This suggests a problem with database persistence or access within the Docker environment.
