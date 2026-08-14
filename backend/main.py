import sys
from fastapi import FastAPI, HTTPException
from backend.models import ChatRequest, ChatResponse
from backend.agent import Agent
from backend.logger import setup_logger

logger = setup_logger(__name__)

# Initialize FastAPI app and Agent
app = FastAPI(title="JARVIS API", version="1.0.0")
try:
    jarvis_agent = Agent()
except Exception as e:
    logger.error(f"Failed to initialize Agent: {e}")
    # We still allow app to start, but requests will fail.
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

def run_cli():
    print("========================================")
    print("      JARVIS Stage 1 CLI Terminal       ")
    print("========================================")
    print("Type 'exit' or 'quit' to stop.")
    
    try:
        cli_agent = Agent()
    except Exception as e:
        print(f"Failed to initialize JARVIS: {e}")
        return
        
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
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

if __name__ == "__main__":
    run_cli()
