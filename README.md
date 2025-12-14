# FastAPI AI Service

FastAPI microservice with OpenAI GPT integration, rate limiting, and structured logging.

## Features

- **OpenAI GPT Integration** - Chat, summarization, and translation with GPT-3.5/GPT-4
- **Rate Limiting** - Prevent abuse with configurable limits
- **Structured Logging** - JSON logs in production, readable in dev
- **Pydantic Validation** - Request/response validation
- **Error Handling** - Graceful error responses
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

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/chat` | Chat completion |
| POST | `/api/v1/summarize` | Text summarization |
| POST | `/api/v1/translate` | Text translation |

## API Documentation

- Swagger UI: http://localhost:8001/docs (when DEBUG=true)

## Usage Examples

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

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | Your OpenAI API key |
| `RATE_LIMIT_PER_MINUTE` | 10 | Max requests per minute per IP |
| `APP_ENV` | development | Environment (development/production) |
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
│   │   ├── chat.py         # Chat endpoint
│   │   ├── summarize.py    # Summarize endpoint
│   │   └── translate.py    # Translate endpoint
│   ├── core/
│   │   ├── logging.py      # Logging setup
│   │   └── rate_limit.py   # Rate limiting
│   ├── schemas/
│   │   ├── chat.py         # Chat models
│   │   ├── summarize.py    # Summarize models
│   │   └── translate.py    # Translate models
│   ├── services/
│   │   └── openai_service.py  # OpenAI client
│   ├── config.py           # Settings
│   └── main.py             # App entry point
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## License

MIT
