# JARVIS Stage 1

This is the foundational brain for JARVIS, an AI assistant.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your API key:
   ```bash
   cp .env.example .env
   ```

## Running the Application

### Command-Line Interface (CLI)

You can chat with JARVIS directly from the terminal:
```bash
python backend/main.py
```

### API Server

To start the FastAPI server:
```bash
uvicorn backend.main:app --reload
```

Then you can test the chat endpoint:
```bash
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"message\": \"Hello JARVIS\"}"
```

## Testing

Run tests with `pytest`:
```bash
pytest tests/
```
