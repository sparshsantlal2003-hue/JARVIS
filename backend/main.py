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
    print("      JARVIS - Intelligent Desktop Assistant")
    print("=" * 50)
    print("Type 'exit', 'quit', or 'shutdown' to stop.\n")

    try:
        cli_agent = Agent()
    except Exception as e:
        print(f"Failed to initialize JARVIS: {e}")
        return

    shutdown_manager.reset()

    while not shutdown_manager.is_shutdown_requested():
        try:
            user_input = input("You: ")
            if not user_input.strip():
                continue

            if is_shutdown_command(user_input):
                shutdown_manager.shutdown()
                break

            response = cli_agent.chat(user_input)
            print(f"JARVIS: {response}\n")

        except KeyboardInterrupt:
            print()
            shutdown_manager.shutdown()
            break
        except Exception as e:
            print(f"JARVIS encountered an error: {e}")

def run_voice(background=False):
    from backend.single_instance import enforce_single_instance, release_single_instance
    from backend.tray import start_tray, stop_tray
    
    enforce_single_instance()
    try:
        from backend.voice.loop import VoiceLoop
    except ImportError as e:
        print(f"[VOICE] Could not import voice module: {e}")
        if not background:
            run_cli()
        return

    try:
        agent = Agent()
        loop = VoiceLoop(agent)
        start_tray(loop)
        loop.run()
    except Exception as e:
        logger.error(f"[VOICE] Fatal error: {e}")
        print(f"[VOICE] Voice mode failed: {e}")
    finally:
        stop_tray()
        release_single_instance()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JARVIS - Intelligent Desktop AI Assistant")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--voice", action="store_true", help="Start in voice mode")
    mode_group.add_argument("--text", action="store_true", help="Start in text mode (default)")
    mode_group.add_argument("--background", action="store_true", help="Start in background mode with tray")
    parser.add_argument("--debug", action="store_true", help="Enable verbose debug logging")
    
    parser.add_argument("--install-startup", action="store_true", help="Install JARVIS to Windows startup")
    parser.add_argument("--remove-startup", action="store_true", help="Remove JARVIS from Windows startup")
    parser.add_argument("--startup-status", action="store_true", help="Check JARVIS startup status")
    
    parser.add_argument("--status", action="store_true", help="Check JARVIS process status")
    parser.add_argument("--restart", action="store_true", help="Restart JARVIS background process")
    
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    from backend.startup import install_startup, remove_startup, get_startup_status
    
    if args.install_startup:
        install_startup()
        sys.exit(0)
    elif args.remove_startup:
        remove_startup()
        sys.exit(0)
    elif args.startup_status:
        get_startup_status()
        sys.exit(0)
    elif args.status:
        import ctypes
        ERROR_ALREADY_EXISTS = 183
        MUTEX_NAME = "Global\\\\JARVIS_BACKGROUND_MUTEX"
        kernel32 = ctypes.windll.kernel32
        m = kernel32.CreateMutexW(None, False, MUTEX_NAME)
        last_error = kernel32.GetLastError()
        if last_error == ERROR_ALREADY_EXISTS:
            print("\nJARVIS is RUNNING.")
        else:
            print("\nJARVIS is NOT running.")
        sys.exit(0)
    elif args.restart:
        import subprocess
        print("Use the System Tray to restart JARVIS safely.")
        sys.exit(0)

    if args.background:
        run_voice(background=True)
    el    if args.ai_status:
        from backend.config import settings
        import urllib.request
        import json
        
        provider = getattr(settings, 'ai_provider', 'omniroute').upper()
        base_url = getattr(settings, 'omniroute_base_url', 'http://localhost:20128/v1')
        r_model = getattr(settings, 'omniroute_reasoning_model', 'gpt-oss-120b')
        v_model = getattr(settings, 'omniroute_vision_model', 'gemini-flash-lite-latest')
        
        gateway_status = "Disconnected"
        if provider == "OMNIROUTE":
            try:
                # Try to ping OmniRoute models endpoint
                req = urllib.request.Request(f"{base_url}/models")
                api_key = getattr(settings, 'omniroute_api_key', 'dummy')
                req.add_header("Authorization", f"Bearer {api_key}")
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        gateway_status = "Connected"
            except Exception as e:
                gateway_status = f"Error ({e})"
        
        print(f"\nJARVIS AI STATUS")
        print(f"--------------------------------")
        print(f"Gateway:          {provider}")
        print(f"Gateway Status:   {gateway_status}")
        print(f"\nReasoning:")
        print(f"Provider:         {provider}")
        print(f"Model:            {r_model}")
        print(f"Status:           {'Ready' if gateway_status == 'Connected' else 'Unverified'}")
        print(f"\nVision:")
        print(f"Provider:         {provider}")
        print(f"Model:            {v_model}")
        print(f"Status:           {'Ready' if gateway_status == 'Connected' else 'Unverified'}")
        print(f"--------------------------------\n")
        return

    if args.voice:
        run_voice(background=False)
    else:
        run_cli()
