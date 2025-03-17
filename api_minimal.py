import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('api')

# Create FastAPI app
app = FastAPI(
    title="LeadGen Bot API",
    description="API for the AI-powered lead generation and website sales chatbot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request and response models
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    message: str
    timestamp: str

# Initialize OpenAI client
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    logger.warning("OpenAI API key not found in environment variables")

# Simple API key auth
def verify_api_key(x_api_key: str = Header(None)):
    api_key = os.environ.get("API_KEY")
    if not api_key or x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@app.get("/")
async def root():
    return {"status": "online", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, authenticated: bool = Header(None)):
    """
    Simple chat endpoint that doesn't depend on the full lead-gen-bot infrastructure
    """
    try:
        # Default message if OpenAI isn't configured
        response_text = "Hello! I'm the LeadGen Bot. I can help you with your web development needs. What can I assist you with today?"
        
        # Use OpenAI if available
        if openai.api_key:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for a web development business. Be friendly, professional, and helpful."},
                    {"role": "user", "content": request.message}
                ]
            )
            response_text = completion.choices[0].message.content
        
        # Return the response
        return ChatResponse(
            message=response_text,
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_minimal:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000))) 