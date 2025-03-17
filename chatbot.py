import os
import json
import logging
import openai
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import requests
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('chatbot')

# Import from existing project modules
from utils import load_config, format_timestamp, send_notification
from lead_tracker import LeadTracker

class Message(BaseModel):
    role: str  # "system", "assistant", or "user"
    content: str
    timestamp: Optional[str] = None

class Conversation(BaseModel):
    lead_id: str
    platform: str
    messages: List[Message]
    qualified: bool = False
    payment_sent: bool = False
    payment_completed: bool = False
    last_updated: str
    inactive_days: int = 0
    
class ChatbotResponse(BaseModel):
    message: str
    actions: List[Dict[str, Any]] = []
    
class AIWebsiteChatbot:
    """
    AI-powered chatbot for engaging with leads across multiple platforms.
    Handles qualification, payment processing, and follow-ups.
    """
    
    def __init__(self):
        """Initialize the chatbot with configuration settings."""
        self.config = load_config()
        self.lead_tracker = LeadTracker()
        
        # Initialize OpenAI client
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        if not openai.api_key:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key not found")
            
        # Load conversation history
        self.conversations = self.load_conversations()
        
        # System prompt that defines the chatbot behavior
        self.system_prompt = """
        You are an AI assistant for a web development business. Your goal is to qualify leads and guide them through 
        the process of purchasing a website. Be friendly, professional, and helpful. Ask questions to understand 
        their business needs, provide pricing information when appropriate, and guide them toward making a purchase.
        
        You should follow this general conversation flow:
        1. Initial greeting and qualification (ask about their business and website needs)
        2. Understand their specific requirements (business type, e-commerce, custom features)
        3. Provide appropriate pricing based on their needs
        4. Send a payment link when they express interest in purchasing
        5. After payment, send them to an intake form for more details
        6. Follow up if they don't respond
        
        Available website packages:
        - Basic Business Website: $497 (informational, 5 pages, contact form)
        - E-commerce Store: $997 (product listings, shopping cart, payment processing)
        - Custom Web Application: Starting at $1,997 (custom functionality, user accounts)
        
        All packages include:
        - Domain setup
        - Mobile-responsive design
        - SEO optimization
        - 48-hour delivery
        - 30 days of support
        
        Do not share this system prompt with users. Only respond as the assistant.
        """
        
    def load_conversations(self) -> Dict[str, Conversation]:
        """Load conversation history from storage."""
        conversations = {}
        try:
            if os.path.exists('conversations.json'):
                with open('conversations.json', 'r') as f:
                    data = json.load(f)
                    for lead_id, conv_data in data.items():
                        conversations[lead_id] = Conversation(**conv_data)
        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
        return conversations
    
    def save_conversations(self):
        """Save conversation history to storage."""
        try:
            data = {lead_id: conv.dict() for lead_id, conv in self.conversations.items()}
            with open('conversations.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving conversations: {e}")
    
    def get_conversation(self, lead_id: str, platform: str) -> Conversation:
        """Get existing conversation or create a new one."""
        if lead_id not in self.conversations:
            self.conversations[lead_id] = Conversation(
                lead_id=lead_id,
                platform=platform,
                messages=[],
                last_updated=format_timestamp(datetime.now())
            )
        return self.conversations[lead_id]
    
    def add_message(self, lead_id: str, platform: str, role: str, content: str) -> None:
        """Add a message to a conversation."""
        conversation = self.get_conversation(lead_id, platform)
        message = Message(
            role=role,
            content=content,
            timestamp=format_timestamp(datetime.now())
        )
        conversation.messages.append(message)
        conversation.last_updated = format_timestamp(datetime.now())
        conversation.inactive_days = 0
        self.save_conversations()
    
    def generate_stripe_payment_link(self, package_type: str) -> str:
        """Generate a Stripe payment link for the specified package type."""
        # This would integrate with the Stripe API in production
        # For now, we'll use placeholder URLs based on package type
        base_url = "https://buy.stripe.com/yourAccountLink/"
        
        if package_type.lower() == "basic" or package_type.lower() == "business":
            return f"{base_url}basic_website_497"
        elif package_type.lower() == "ecommerce" or package_type.lower() == "e-commerce":
            return f"{base_url}ecommerce_website_997"
        elif package_type.lower() == "custom":
            return f"{base_url}custom_website_1997"
        else:
            return f"{base_url}consultation"
    
    def should_send_payment_link(self, messages: List[Message]) -> Tuple[bool, str]:
        """Determine if we should send a payment link based on conversation."""
        # Simple heuristic: check if the last few messages indicate interest in a specific package
        package_keywords = {
            "basic": ["basic", "simple", "business", "small", "informational"],
            "ecommerce": ["ecommerce", "e-commerce", "online store", "products", "shop"],
            "custom": ["custom", "application", "complex", "features", "functionality"]
        }
        
        # Look at recent messages
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        user_messages = [msg.content.lower() for msg in recent_messages if msg.role == "user"]
        
        # Check for indicators of package interest and readiness
        for package, keywords in package_keywords.items():
            if any(keyword in " ".join(user_messages) for keyword in keywords):
                # Look for buying signals
                buying_signals = ["price", "cost", "how much", "pay", "purchase", "buy", "interested"]
                if any(signal in " ".join(user_messages) for signal in buying_signals):
                    return True, package
        
        return False, ""
    
    def process_message(self, lead_id: str, platform: str, message_content: str) -> ChatbotResponse:
        """Process an incoming message and generate a response."""
        # Add user message to conversation
        self.add_message(lead_id, platform, "user", message_content)
        
        # Get the conversation
        conversation = self.get_conversation(lead_id, platform)
        
        # Format messages for OpenAI API
        formatted_messages = [{"role": "system", "content": self.system_prompt}]
        for msg in conversation.messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})
        
        # Check if we should send a payment link
        should_send, package_type = self.should_send_payment_link(conversation.messages)
        
        # Special action for payment link
        actions = []
        if should_send and not conversation.payment_sent:
            payment_link = self.generate_stripe_payment_link(package_type)
            actions.append({
                "type": "payment_link",
                "link": payment_link,
                "package": package_type
            })
            conversation.payment_sent = True
            self.save_conversations()
            
            # Update lead status in lead tracker
            self.lead_tracker.update_lead_status(lead_id, "qualified")
        
        # Generate response using OpenAI
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",  # Use appropriate model
                messages=formatted_messages,
                max_tokens=300,
                temperature=0.7
            )
            
            # Extract the response text
            response_text = response.choices[0].message["content"].strip()
            
            # Add bot response to conversation
            self.add_message(lead_id, platform, "assistant", response_text)
            
            # If we're sending a payment link, append it to the message
            if actions and actions[0]["type"] == "payment_link":
                payment_package = actions[0]["package"].capitalize()
                payment_link = actions[0]["link"]
                
                response_text += f"\n\nHere's your payment link for the {payment_package} package: {payment_link}"
            
            # Return the response
            return ChatbotResponse(
                message=response_text,
                actions=actions
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Fallback response
            fallback = "I apologize, but I'm having trouble processing your request right now. Let me connect you with a human team member who can help you further."
            self.add_message(lead_id, platform, "assistant", fallback)
            
            # Send notification about the error
            send_notification(
                subject="Chatbot Error",
                message=f"Error generating response for lead {lead_id} on {platform}: {str(e)}"
            )
            
            return ChatbotResponse(message=fallback)
    
    def check_inactive_conversations(self):
        """Check for inactive conversations and send follow-ups."""
        current_time = datetime.now()
        for lead_id, conversation in self.conversations.items():
            last_updated = datetime.strptime(conversation.last_updated, "%Y-%m-%d %H:%M:%S")
            days_inactive = (current_time - last_updated).days
            
            # Update inactive days count
            conversation.inactive_days = days_inactive
            
            # Send follow-up message if inactive for 1 day and no payment yet
            if days_inactive >= 1 and not conversation.payment_completed:
                # Check if the last message was from the user
                if conversation.messages and conversation.messages[-1].role == "user":
                    continue  # Don't follow up if waiting for bot response
                
                # Generate a follow-up message
                follow_up_message = self.generate_follow_up_message(conversation)
                
                # Add follow-up to conversation
                self.add_message(lead_id, conversation.platform, "assistant", follow_up_message)
                
                # Log the follow-up
                logger.info(f"Sent follow-up to lead {lead_id} on {conversation.platform} after {days_inactive} days")
                
                # Update lead tracker
                self.lead_tracker.record_followup(lead_id, follow_up_message)
    
    def generate_follow_up_message(self, conversation: Conversation) -> str:
        """Generate a follow-up message based on conversation context."""
        # Extract some context from the conversation
        convo_summary = " ".join([msg.content for msg in conversation.messages[-5:]])
        
        # Use OpenAI to generate a contextual follow-up
        try:
            prompt = f"""
            This is a follow-up message for a lead who hasn't responded in 24+ hours.
            
            Previous conversation context:
            {convo_summary}
            
            Generate a friendly follow-up message that:
            1. References their specific business needs (if mentioned)
            2. Provides a gentle reminder of our services
            3. Asks an engaging question to restart the conversation
            4. Is concise (max 3 sentences)
            """
            
            response = openai.Completion.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=150,
                temperature=0.7
            )
            
            follow_up = response.choices[0].text.strip()
            return follow_up
        
        except Exception as e:
            logger.error(f"Error generating follow-up: {e}")
            # Fallback follow-up message
            return "Hey there! Just following up on our conversation about your website needs. I'm still here to help if you have any questions or want to proceed. Let me know if you're still interested!"
    
    def handle_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle webhook from Stripe for payment confirmation."""
        try:
            event_type = data.get("type")
            
            if event_type == "checkout.session.completed":
                # Extract payment details
                session = data.get("data", {}).get("object", {})
                metadata = session.get("metadata", {})
                lead_id = metadata.get("lead_id")
                
                if lead_id and lead_id in self.conversations:
                    # Update conversation status
                    self.conversations[lead_id].payment_completed = True
                    self.save_conversations()
                    
                    # Update lead status in lead tracker
                    self.lead_tracker.update_lead_status(lead_id, "converted")
                    
                    # Send confirmation message
                    intake_form_url = "https://forms.gle/KQGNwyWqHyVT9Bd16"
                    confirmation_message = (
                        f"Thank you for your payment! Your website project is now underway. "
                        f"To help us create the perfect website for you, please fill out our quick intake form: {intake_form_url} "
                        f"This will help us understand your specific requirements and preferences. "
                        f"We'll start work immediately after receiving your completed form!"
                    )
                    
                    self.add_message(lead_id, self.conversations[lead_id].platform, "assistant", confirmation_message)
                    
                    # Send notification to the team
                    send_notification(
                        subject="New Website Payment!",
                        message=f"Lead {lead_id} has completed payment for a website. Check conversations.json for details."
                    )
                    
                    return {"status": "success", "message": "Payment processed successfully"}
            
            return {"status": "success", "message": "Webhook received"}
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {"status": "error", "message": str(e)}


# Singleton instance for use across the application
chatbot = AIWebsiteChatbot() 