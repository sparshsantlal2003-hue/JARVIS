import sys
import argparse
import logging
from fastapi import FastAPI, HTTPException
from backend.models import ChatRequest, ChatResponse
from backend.agent import Agent
from backend.logger import setup_logger

logger = setup_logger(__name__)

# ── FastAPI app (used when running as a server) ─────────────────────────────
app = FastAPI(title="JARVIS API", version="1.0.0")
try:
    jarvis_agent = Agent()
except Exception as e:
    logger.error(f"Failed to initialize Agent: {e}")
    jarvis_agent = None

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not jarvis_agent:
        raise HTTPException(status_code=500, detail="JARVIS agent is not initialized.")
    try:
        reply = jarvis_agent.chat(request.message)
        return ChatResponse(reply=reply)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── CLI text mode ────────────────────────────────────────────────────────────
def run_cli():
    print("=" * 50)
    print("      JARVIS Stage 1 CLI Terminal       ")
    print("=" * 50)
    print("Type 'exit' or 'quit' to stop.")

    try:
        cli_agent = Agent()
    except Exception as e:
        print(f"Failed to initialize JARVIS: {e}")
        return

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                print("JARVIS: Goodbye.")
                break
            if not user_input.strip():
                continue
            response = cli_agent.chat(user_input)
            print(f"JARVIS: {response}")
        except KeyboardInterrupt:
            print("\nJARVIS: Goodbye.")
            break
        except Exception as e:
            print(f"JARVIS encountered an error: {e}")


# ── Voice mode ───────────────────────────────────────────────────────────────
def run_voice():
    try:
        from backend.voice.loop import VoiceLoop
    except ImportError as e:
        print(f"[VOICE] Could not import voice module: {e}")
        print("[VOICE] Falling back to text mode.")
        run_cli()
        return

    try:
        agent = Agent()
        loop = VoiceLoop(agent)
        loop.run()
    except Exception as e:
        logger.error(f"[VOICE] Fatal error in voice loop: {e}")
        print(f"[VOICE] Voice mode failed: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="JARVIS — Intelligent Desktop AI Assistant"
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--voice", action="store_true", help="Start JARVIS in voice mode"
    )
    mode_group.add_argument(
        "--text", action="store_true", help="Start JARVIS in text mode (default)"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable verbose debug logging"
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("[JARVIS] Debug mode enabled.")

    if args.voice:
        run_voice()
    else:
        run_cli()
