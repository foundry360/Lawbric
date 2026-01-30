"""
Minimal Ollama Service for LLaMA 3 Integration

This is a simple backend service that connects to a local Ollama instance
running the llama3:8b model. It provides a single POST endpoint /query
that accepts prompts and returns the model's response.

This service is intentionally minimal - no authentication, no database,
no document handling. It's designed to verify basic connectivity between
the UI and a local LLaMA model.

TODO: This can later be expanded to:
- Add authentication/authorization
- Integrate with document processing for legal analysis
- Add conversation history
- Add streaming responses
- Add error handling and retries
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os

# Initialize FastAPI app
app = FastAPI(
    title="Ollama Query Service",
    description="Minimal service for querying local LLaMA 3 model via Ollama",
    version="1.0.0"
)

# Enable CORS to allow frontend to call this service
# TODO: In production, restrict origins to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama configuration
# When running in Docker, use service name 'ollama' instead of 'localhost'
# When running locally, use 'localhost'
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", f"http://{OLLAMA_HOST}:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")

# Fixed system instruction for legal document analysis (Lawbric)
# This instruction is prepended to every user query and cannot be modified by users.
# This system prompt enforces source-grounded, fact-only, auditable outputs for legal AI:
# - Source-grounded: Only uses explicitly provided text (no outside knowledge or inference)
# - Fact-only: Extracts and outputs only factual statements exactly as they appear
# - Auditable: Formats statements with page references for traceability
# - No commentary: Prohibits questions, commentary, summaries, advice, conversational phrases, or polite endings
# - No speculation: Prohibits inference, interpretation, conclusions, or speculation
# - Explicit refusal: Returns "Not found in the provided text." when no factual statements present
# - Stop immediately: Model must stop output after the last factual statement
# This ensures all model responses are fully source-grounded, fact-only, and auditable for Lawbric.
# Post-processing further enforces this by stripping any lines not starting with '- Page'.
SYSTEM_INSTRUCTION = """You are a legal document analysis assistant.

Rules:
- Use ONLY the text explicitly provided.
- Extract only the factual statements or answers made by the witness.
- Output ONLY the statements exactly as they appear in the text.
- Format each statement as: '- Page X: "[text]"'
- Do NOT include questions, commentary, summaries, advice, conversational phrases, or polite endings.
- Do NOT infer, interpret, conclude, or speculate.
- If no factual statements are present, respond exactly: 'Not found in the provided text.'
- Stop output immediately after the last factual statement."""


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    prompt: str


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    response: str


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Ollama Query Service",
        "status": "running",
        "ollama_url": OLLAMA_BASE_URL,
        "model": OLLAMA_MODEL
    }


@app.post("/query", response_model=QueryResponse)
async def query_ollama(request: QueryRequest):
    """
    Send a prompt to the local Ollama llama3:8b model and return the response.
    
    This endpoint:
    - Accepts a JSON body with a "prompt" field
    - Automatically prepends a fixed system instruction for legal document analysis
    - Sends the combined prompt to Ollama's /api/generate endpoint
    - Returns the model's raw response
    
    System Instruction (Source-Grounded, Fact-Only, Auditable for Lawbric):
    Every user query is automatically wrapped with a system instruction that enforces:
    - Source-grounded behavior: Uses ONLY text explicitly provided (no outside knowledge)
    - Fact-only outputs: Extracts and outputs only factual statements exactly as they appear
    - Auditable format: Formats each statement as "- Page X: \"[text]\"" for traceability
    - No commentary: Prohibits questions, commentary, summaries, advice, conversational phrases, or polite endings
    - No speculation: Prohibits inference, interpretation, conclusions, or speculation
    - Explicit refusal: Returns "Not found in the provided text." when no factual statements present
    - Stop immediately: Model must stop output after the last factual statement
    
    Post-Processing:
    After receiving the model response, the service automatically strips any lines not
    starting with '- Page' to remove leftover commentary, polite phrases, or other
    non-factual content. This ensures fully source-grounded, fact-only, auditable outputs
    by keeping only lines that match the required format.
    
    This ensures all model responses are fully source-grounded, fact-only, and auditable
    for Lawbric legal AI, with no commentary, questions, or speculative text.
    
    The system instruction is defined in SYSTEM_INSTRUCTION constant and cannot
    be modified by users.
    
    TODO: Future enhancements:
    - Add context from uploaded documents
    - Add conversation history
    - Add streaming for real-time responses
    - Add error handling and retries
    """
    
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Wrap user query with fixed system instruction for source-grounded, fact-only outputs
    # The system instruction is automatically prepended to every query and cannot be
    # modified or overridden by users. This enforces source-grounded, fact-only, and
    # auditable responses for Lawbric legal AI:
    # - Source-grounded: Uses only explicitly provided text, no outside knowledge
    # - Fact-only: Outputs only factual statements exactly as they appear
    # - Auditable: Formats with page references for traceability
    # - No commentary: Prohibits questions, commentary, summaries, advice, or conversational phrases
    # - No speculation: Prohibits inference, interpretation, conclusions, or speculation
    # The user's original prompt is appended after the system instruction.
    full_prompt = f"{SYSTEM_INSTRUCTION}\n\n{request.prompt}"
    
    # Prepare request to Ollama
    ollama_url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False  # Get complete response at once
    }
    
    try:
        # Send request to Ollama
        # Increased timeout for first request (model loading) and longer prompts
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(ollama_url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # Extract the response text from Ollama's response
            # Ollama returns: {"model": "...", "created_at": "...", "response": "...", "done": true}
            model_response = result.get("response", "")
            
            if not model_response:
                raise HTTPException(
                    status_code=500,
                    detail="Ollama returned an empty response"
                )
            
            # Post-processing: Strip any lines not starting with '- Page' to remove
            # leftover commentary, polite phrases, or other non-factual content.
            # This ensures fully source-grounded, fact-only, auditable outputs by
            # keeping only lines that match the required format: '- Page X: "[text]"'
            # This is a safety measure to remove any commentary the model might add
            # despite the system instruction.
            lines = model_response.split('\n')
            factual_lines = [line for line in lines if line.strip().startswith('- Page')]
            clean_response = '\n'.join(factual_lines)
            
            # If post-processing removed everything but we had a response, check if it was
            # the "Not found" message (which doesn't follow the Page format)
            if not clean_response and model_response.strip():
                # Check if the response is the "Not found" message
                if 'Not found in the provided text' in model_response:
                    clean_response = 'Not found in the provided text.'
                else:
                    # If it's not the "Not found" message and no factual lines, return empty
                    # This means the model didn't follow the format
                    clean_response = ''
            
            return QueryResponse(response=clean_response)
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="Request to Ollama timed out. The model may be processing a large prompt."
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. Make sure Ollama is running."
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Ollama API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    # Run the service
    # Default: http://localhost:8001 (to avoid conflicts with main backend on 8000)
    uvicorn.run(
        "ollama_service:app",
        host="0.0.0.0",
        port=int(os.getenv("OLLAMA_SERVICE_PORT", "8001")),
        reload=True
    )

