import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our chatbot
from chatbot import chatbot, ChatbotResponse

# Import payment API
from create_payment_api import router as payment_router

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

# Include payment router
app.include_router(payment_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request and response models
class MessageRequest(BaseModel):
    lead_id: str
    platform: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    
class MessageResponse(BaseModel):
    message: str
    actions: List[Dict[str, Any]] = []
    conversation_id: str

class WebhookRequest(BaseModel):
    type: str
    data: Dict[str, Any]

# Simple API key auth
def verify_api_key(x_api_key: str = Header(None)):
    api_key = os.environ.get("API_KEY")
    if not api_key or x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

@app.get("/")
async def root():
    return {"status": "online", "version": "1.0.0"}

@app.post("/api/chatbot", response_model=MessageResponse)
async def process_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Process a message from a lead and return the chatbot's response.
    This endpoint handles messages from all platforms (Instagram, Facebook, Twitter, LinkedIn)
    as well as the website chat widget.
    """
    try:
        # Process the message and get response
        response = chatbot.process_message(
            lead_id=request.lead_id,
            platform=request.platform,
            message_content=request.message
        )
        
        # Add lead info to Google Sheets in the background if this is a new lead
        if request.metadata and request.metadata.get("is_new_lead", False):
            background_tasks.add_task(
                chatbot.lead_tracker.record_lead_info,
                request.lead_id,
                request.metadata
            )
        
        # Return the response
        return MessageResponse(
            message=response.message,
            actions=response.actions,
            conversation_id=request.lead_id
        )
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhook/stripe")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Stripe payment webhooks to update conversation state and send confirmation messages.
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        payload = json.loads(body)
        
        # Process the webhook
        result = chatbot.handle_webhook(payload)
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/follow-up")
async def trigger_follow_ups(authenticated: bool = Depends(verify_api_key)):
    """
    Trigger the follow-up process for inactive conversations.
    This endpoint should be called by a scheduler (e.g., cron job) daily.
    """
    try:
        chatbot.check_inactive_conversations()
        return {"status": "success", "message": "Follow-up process completed"}
    
    except Exception as e:
        logger.error(f"Error triggering follow-ups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_api():
    """Start the API server."""
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    start_api() 