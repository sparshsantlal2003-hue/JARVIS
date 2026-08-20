import sys
import argparse
import logging
from fastapi import FastAPI, HTTPException
from backend.models import ChatRequest, ChatResponse
from backend.agent import Agent
from backend.logger import setup_logger
from backend.shutdown import shutdown_manager, is_shutdown_command, FAREWELL_MESSAGE

logger = setup_logger(__name__)

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
        raise HTTPException(status_code=500, detail=str(e))


def run_cli():
    print("=" * 50)
    print("      JARVIS — Intelligent Desktop Assistant")
    print("=" * 50)
    print("Type 'exit', 'quit', or 'shutdown' to stop.\n")

    try:
        cli_agent = Agent()
    except Exception as e:
        print(f"Failed to initialize JARVIS: {e}")
        return

    # Reset shutdown state for this session
    shutdown_manager.reset()

    while not shutdown_manager.is_shutdown_requested():
        try:
            user_input = input("You: ")

            if not user_input.strip():
                continue

            # Deterministic shutdown check — no LLM call
            if is_shutdown_command(user_input):
                shutdown_manager.shutdown()  # exits process
                break

            response = cli_agent.chat(user_input)
            print(f"JARVIS: {response}\n")

        except KeyboardInterrupt:
            print()
            shutdown_manager.shutdown()
            break
        except Exception as e:
            print(f"JARVIS encountered an error: {e}")


def run_voice():
    try:
        from backend.voice.loop import VoiceLoop
    except ImportError as e:
        print(f"[VOICE] Could not import voice module: {e}")
        run_cli()
        return

    try:
        agent = Agent()
        loop = VoiceLoop(agent)
        loop.run()
    except Exception as e:
        logger.error(f"[VOICE] Fatal error: {e}")
        print(f"[VOICE] Voice mode failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JARVIS — Intelligent Desktop AI Assistant")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--voice", action="store_true", help="Start in voice mode")
    mode_group.add_argument("--text", action="store_true", help="Start in text mode (default)")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.voice:
        run_voice()
    else:
        run_cli()
