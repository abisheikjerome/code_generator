# code_generator
# Code Generator

FastAPI service for AI-assisted code generation, review, and research. The app uses LangGraph/LangChain agents, Amazon Bedrock for the LLM, PostgreSQL checkpoints for agent state, and optional MCP tools for review/research workflows.

## Features

- Classifies each user query as code generation, code review, research, or invalid.
- Generates code through a LangChain agent.
- Reviews generated or submitted code and can route fixes back through the generator.
- Supports research/explanation responses.
- Stores LangGraph checkpoints in PostgreSQL.
- Exposes a FastAPI endpoint with Swagger docs.

## Project Structure

```text
dev/
  pyproject.toml
  uv.lock
  src/
    app.py
    settings.py
    agent/
      code_builder.py
      code_researcher.py
      code_reviewer.py
      prompt.py
    models/
    routes/
    service/
    utils/
```

## Requirements

- Python 3.12 or newer
- uv
- PostgreSQL
- AWS credentials with access to Amazon Bedrock Runtime
- Bedrock model ID, for example an Amazon provider model supported by your account/region
- Optional MCP servers:
  - reviewer MCP server at `http://127.0.0.1:8001/sse`
  - researcher MCP server at `http://127.0.0.1:8002/mcp`

## Setup

From the repository root:

```powershell
cd dev
uv sync
```

Create a `.env` file inside `dev/`:

```env
REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
MODEL_ID=your_bedrock_model_id

DB_HOST=localhost
DB_PORT=5432
DB_NAME=code_analyzer
DB_USERNAME=postgres
DB_PASSWORD=your_password

HOST=0.0.0.0
PORT=8081
LOG_LEVEL=INFO
```

Make sure the PostgreSQL database exists:

```sql
CREATE DATABASE code_analyzer;
```

## Run

```powershell
cd dev/src
uv run python app.py
```

The API runs on:

```text
http://127.0.0.1:8081
```

Swagger docs:

```text
http://127.0.0.1:8081/docs
```

## API

### Generate, Review, Or Research Code

```http
POST /api/v1/coder
Content-Type: application/json
```

Request:

```json
{
  "user_id": "user-123",
  "query": "Create a Python FastAPI endpoint for uploading a file"
}
```

Example response:

```json
{
  "data": {
    "code": "...",
    "review": "..."
  },
  "errors": null,
  "code": 200
}
```

## Notes

- The app currently starts Uvicorn from `src/app.py` on port `8081`.
- PostgreSQL is required because the agents use `AsyncPostgresSaver`.
- The reviewer agent expects an MCP SSE server at `http://127.0.0.1:8001/sse`.
- The researcher agent currently creates an MCP client config, but uses no MCP tools in the active code path.
- Do not commit `.env`, `.venv`, logs, or local uv cache folders.

## Useful Commands

Compile-check the source:

```powershell
cd dev
uv run python -m compileall src
```

Run the app:

```powershell
cd dev/src
uv run python app.py
```

Check Git status:

```powershell
git status
```
