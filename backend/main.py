"""
AI Writing Assistant API
========================
This is a FastAPI backend that connects to Claude (Anthropic's AI) to provide
writing assistance. It supports both regular and streaming responses.

KEY CONCEPTS FOR LEARNERS:
- FastAPI: A modern Python web framework for building APIs
- Streaming: Sending data piece-by-piece instead of all at once
- CORS: Security feature that controls which websites can call your API
- Environment Variables: Secret values stored outside your code
"""

# ============================================================================
# IMPORTS - These are libraries we need
# ============================================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# ============================================================================
# APP SETUP
# ============================================================================

# Create the FastAPI application
# Think of this as creating your "server" that will handle requests
app = FastAPI(
    title="AI Writing Assistant",
    description="An API that uses Claude to help with writing tasks",
    version="1.0.0"
)

# CORS Middleware Setup
# ---------------------
# CORS (Cross-Origin Resource Sharing) is a security feature.
# Without this, your React frontend (running on a different URL) 
# wouldn't be able to call your API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Vite dev server (local development)
        "http://localhost:3000",      # Alternative local port
        os.getenv("FRONTEND_URL", ""), # Your deployed frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Initialize the Anthropic client
# This connects to Claude's API using your API key
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# ============================================================================
# DATA MODELS (using Pydantic)
# ============================================================================

# Pydantic models define the shape of data your API accepts/returns
# Think of them as "contracts" for your data

class WritingRequest(BaseModel):
    """
    This defines what data the client must send when making a request.
    
    Example JSON that matches this model:
    {
        "prompt": "Write a blog post about Python",
        "writing_type": "blog_post",
        "tone": "professional"
    }
    """
    prompt: str                          # Required: The user's writing request
    writing_type: str = "general"        # Optional: Type of writing (has default)
    tone: str = "professional"           # Optional: Writing tone (has default)


class WritingResponse(BaseModel):
    """This defines the shape of our API's response."""
    content: str      # The generated text
    model: str        # Which AI model was used
    usage: dict       # Token usage information


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_system_prompt(writing_type: str, tone: str) -> str:
    """
    Creates a system prompt that tells Claude how to behave.
    
    System prompts are like giving instructions to Claude before the
    conversation starts. They shape how Claude responds.
    """
    return f"""You are an expert writing assistant. Your task is to help users 
with their writing needs.

Writing Type: {writing_type}
Tone: {tone}

Guidelines:
- Produce high-quality, engaging content
- Match the requested tone and style
- Be creative while staying on topic
- Format the output appropriately for the writing type
- If writing code examples, use proper formatting"""


# ============================================================================
# API ENDPOINTS (Routes)
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - just confirms the API is running.
    
    GET request to: http://your-api.com/
    Returns: A welcome message
    """
    return {
        "message": "Welcome to the AI Writing Assistant API!",
        "docs": "/docs",  # FastAPI auto-generates documentation here
        "endpoints": {
            "/generate": "POST - Generate content (regular response)",
            "/generate/stream": "POST - Generate content (streaming response)"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint - used by deployment platforms to verify the app is alive.
    
    Railway/Render will ping this endpoint to check if your server is healthy.
    """
    return {"status": "healthy"}


@app.post("/generate", response_model=WritingResponse)
async def generate_content(request: WritingRequest):
    """
    Generate writing content (non-streaming).
    
    HOW IT WORKS:
    1. Client sends a POST request with WritingRequest data
    2. We call Claude's API and wait for the COMPLETE response
    3. We return the full response at once
    
    WHEN TO USE:
    - When you need the complete response before doing anything
    - For shorter content where waiting is acceptable
    """
    try:
        # Call Claude's API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",  # The AI model to use
            max_tokens=1024,                        # Maximum response length
            system=build_system_prompt(request.writing_type, request.tone),
            messages=[
                {
                    "role": "user",
                    "content": request.prompt
                }
            ]
        )
        
        # Return the response
        return WritingResponse(
            content=message.content[0].text,
            model=message.model,
            usage={
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens
            }
        )
        
    except anthropic.APIError as e:
        # Handle API errors (bad key, rate limits, etc.)
        raise HTTPException(
            status_code=500,
            detail=f"Claude API error: {str(e)}"
        )


@app.post("/generate/stream")
async def generate_content_stream(request: WritingRequest):
    """
    Generate writing content with STREAMING.
    
    HOW STREAMING WORKS:
    1. Client sends a POST request
    2. Instead of waiting for the complete response, we send data 
       piece-by-piece as Claude generates it
    3. Client sees text appear word-by-word (like ChatGPT does!)
    
    WHY USE STREAMING:
    - Better user experience (users see progress immediately)
    - Feels faster even though total time is similar
    - Essential for longer content generation
    
    TECHNICAL DETAILS:
    - Uses Server-Sent Events (SSE) format
    - Each chunk is sent as: "data: {text}\n\n"
    - Stream ends with: "data: [DONE]\n\n"
    """
    
    async def generate():
        """
        This is a generator function (note the 'yield' keyword).
        It produces data piece-by-piece instead of all at once.
        """
        try:
            # Create a streaming request to Claude
            with client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=build_system_prompt(request.writing_type, request.tone),
                messages=[
                    {
                        "role": "user", 
                        "content": request.prompt
                    }
                ]
            ) as stream:
                # Loop through each piece of text as it's generated
                for text in stream.text_stream:
                    # 'yield' sends this chunk to the client immediately
                    # Format: Server-Sent Events (SSE)
                    yield f"data: {text}\n\n"
            
            # Signal that we're done
            yield "data: [DONE]\n\n"
            
        except anthropic.APIError as e:
            # Send error in the stream
            yield f"data: [ERROR] {str(e)}\n\n"
    
    # Return a streaming response
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",  # This tells the browser it's a stream
        headers={
            "Cache-Control": "no-cache",      # Don't cache this response
            "Connection": "keep-alive",        # Keep the connection open
            "X-Accel-Buffering": "no"          # Disable nginx buffering
        }
    )


# ============================================================================
# RUN THE SERVER (for local development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    # Uvicorn is an ASGI server that runs our FastAPI app
    # host="0.0.0.0" makes it accessible from other devices on your network
    # port=8000 is the standard development port
    uvicorn.run(app, host="0.0.0.0", port=8000)
