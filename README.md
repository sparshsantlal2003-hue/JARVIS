# JARVIS Stage 3: Computer Control

JARVIS is an intelligent desktop AI assistant with the ability to safely interact with your Windows file system, launch applications, and simulate keystrokes.

## Setup

1. Create a virtual environment:
   `ash
   python -m venv venv
   .\venv\Scripts\activate
   `
2. Install dependencies:
   `ash
   pip install -r requirements.txt
   `
3. Copy .env.example to .env and configure your API keys:
   `ash
   cp .env.example .env
   `
   **AI Provider Selection:**
   JARVIS supports both **Google Gemini** (AI_PROVIDER=gemini) and **Groq LLaMA 3.3 70B** (AI_PROVIDER=groq).
   Set AI_PROVIDER=groq and supply your GROQ_API_KEY for blazing-fast, sub-second tool execution!

## Running the Application

### Command-Line Interface (CLI)

You can chat with JARVIS directly from the terminal:
`ash
.\venv\Scripts\python -m backend.main
`

### API Server

To start the FastAPI server:
`ash
uvicorn backend.main:app --reload
`

## Testing

Run tests with pytest to verify the provider logic, agent loops, and tool registry:
`ash
.\venv\Scripts\python -m pytest tests/
`
