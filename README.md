# FastAPI AI Service

FastAPI microservice with OpenAI GPT integration, API key management, usage tracking, rate limiting, and structured logging.

## Features

- **OpenAI GPT Integration** - Chat, summarization, and translation with GPT-3.5/GPT-4
- **Streaming Responses** - Real-time token streaming with Server-Sent Events (SSE)
- **API Key Management** - Create, manage, and revoke API keys
- **Usage Tracking** - Track API usage per key with detailed metrics
- **PostgreSQL Database** - Persistent storage with async SQLAlchemy
- **Rate Limiting** - Prevent abuse with configurable limits per API key
- **Structured Logging** - JSON logs in production, readable in dev
- **Pydantic Validation** - Request/response validation
- **Docker Support** - Production-ready containerization

## Quick Start

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Create .env file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start PostgreSQL
docker compose up -d db

# Run migrations
alembic upgrade head

# Run the app
uvicorn app.main:app --reload --port 8001
```

### Docker

```bash
# Create .env with your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run
docker compose up --build
```

App available at http://localhost:8001

## API Endpoints

### AI Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/chat` | Chat completion |
| POST | `/api/v1/chat/stream` | Streaming chat (SSE) |
| POST | `/api/v1/summarize` | Text summarization |
| POST | `/api/v1/translate` | Text translation |

### API Key Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/api-keys` | Create new API key |
| GET | `/api/v1/api-keys` | List all API keys |
| GET | `/api/v1/api-keys/{id}` | Get API key details |
| PATCH | `/api/v1/api-keys/{id}` | Update API key |
| DELETE | `/api/v1/api-keys/{id}` | Delete API key |

### Usage Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/usage/{key_id}` | Get usage records |
| GET | `/api/v1/usage/{key_id}/summary` | Get usage summary |

## API Documentation

- Swagger UI: http://localhost:8001/docs (when DEBUG=true)

## Usage Examples

### Create API Key
```bash
curl -X POST http://localhost:8001/api/v1/api-keys \
  -H "Content-Type: application/json" \
  -d '{"name": "My App Key", "rate_limit_per_minute": 20}'
```

Response:
```json
{
  "id": "...",
  "name": "My App Key",
  "key": "ai_xxxxxxxxxxxxx",
  "key_prefix": "ai_xxxxx",
  "is_active": true,
  "rate_limit_per_minute": 20,
  "created_at": "...",
  "last_used_at": null
}
```

**Important:** Save the `key` value - it's only shown once!

### Chat
```bash
curl -X POST http://localhost:8001/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is Python?"}
    ],
    "model": "gpt-3.5-turbo",
    "max_tokens": 500
  }'
```

### Chat Streaming (SSE)
```bash
curl -X POST http://localhost:8001/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a short poem about coding"}
    ],
    "model": "gpt-3.5-turbo"
  }'
```

Response streams token by token:
```
data: {"token": "Code"}
data: {"token": " flows"}
data: {"token": " like"}
data: {"token": " water"}
...
data: {"done": true, "full_text": "Code flows like water..."}
```

### Summarize
```bash
curl -X POST http://localhost:8001/api/v1/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your long text to summarize goes here...",
    "max_length": 100,
    "style": "concise"
  }'
```

Styles: `concise`, `detailed`, `bullet_points`

### Translate
```bash
curl -X POST http://localhost:8001/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "source_language": "auto",
    "target_language": "Spanish"
  }'
```

Use `"source_language": "auto"` for automatic language detection.

### Get Usage Summary
```bash
curl http://localhost:8001/api/v1/usage/{key_id}/summary?days=30
```

Response:
```json
{
  "total_requests": 150,
  "total_tokens": 45000,
  "total_prompt_tokens": 15000,
  "total_completion_tokens": 30000,
  "period_start": "...",
  "period_end": "..."
}
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | Your OpenAI API key |
| `DB_USER` | ai_service | PostgreSQL username |
| `DB_PASSWORD` | ai_service_pass | PostgreSQL password |
| `DB_NAME` | ai_service_db | Database name |
| `DB_HOST` | localhost | Database host |
| `DB_PORT` | 5436 | Database port |
| `RATE_LIMIT_PER_MINUTE` | 10 | Default rate limit |
| `APP_ENV` | development | Environment |
| `DEBUG` | false | Enable debug mode and docs |
| `LOG_LEVEL` | INFO | Logging level |

## Running Tests

```bash
pytest -v
```

## Project Structure

```
├── src/app/
│   ├── api/v1/
│   │   ├── api_keys.py       # API key management
│   │   ├── usage.py          # Usage tracking
│   │   ├── chat.py           # Chat endpoint
│   │   ├── summarize.py      # Summarize endpoint
│   │   └── translate.py      # Translate endpoint
│   ├── core/
│   │   ├── auth.py           # API key authentication
│   │   ├── logging.py        # Logging setup
│   │   └── rate_limit.py     # Rate limiting
│   ├── models/
│   │   ├── api_key.py        # API key model
│   │   └── usage.py          # Usage record model
│   ├── schemas/
│   │   ├── api_key.py        # API key schemas
│   │   ├── usage.py          # Usage schemas
│   │   ├── chat.py           # Chat models
│   │   ├── summarize.py      # Summarize models
│   │   └── translate.py      # Translate models
│   ├── services/
│   │   ├── api_key_service.py   # API key service
│   │   ├── usage_service.py     # Usage service
│   │   └── openai_service.py    # OpenAI client
│   ├── config.py             # Settings
│   ├── database.py           # Database connection
│   └── main.py               # App entry point
├── alembic/
│   ├── versions/             # Migration files
│   └── env.py                # Alembic config
├── tests/
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
└── pyproject.toml
```

## License

MIT
