#!/usr/bin/env python3
"""
Test script for the AI website chatbot.
This script simulates a conversation with the chatbot to verify its functionality.
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('chatbot_test')

# Load environment variables
load_dotenv()

# Import the chatbot - but patch the OpenAI calls first
import openai
import random

# Mock OpenAI responses
def mock_completion_create(*args, **kwargs):
    """Mock OpenAI Completion API to avoid actual API calls during testing."""
    prompt = kwargs.get('prompt', '')
    mock_response_text = "This is a follow-up message based on our conversation about your website needs. I noticed you were interested in our services - are you still looking for help with your website project?"
    
    class MockResponse:
        def __init__(self, text):
            self.text = text
            self.choices = [type('obj', (object,), {'text': text})]
    
    return MockResponse(mock_response_text)

def mock_chat_completion_create(*args, **kwargs):
    """Mock OpenAI ChatCompletion API to avoid actual API calls during testing."""
    messages = kwargs.get('messages', [])
    last_message = messages[-1]['content'] if messages else ''
    
    responses = {
        "examples": "I'd be happy to show you examples of our work. We've created websites for businesses in various industries including fitness, retail, consulting, and tech startups. Each website is designed to be mobile-responsive, fast-loading, and optimized for conversions. Would you like me to send you a link to our portfolio?",
        "fitness": "That's great! For fitness businesses, we can create a website that includes features like class schedules, trainer profiles, membership information, and even online booking. Our Basic Business Website at $497 would work well if you mainly need an informational site, but if you want to sell workout plans online, our E-commerce package at $997 would be more suitable. What specific features would you need?",
        "ecommerce": "Our E-commerce package is priced at $997 and includes everything you need to sell your workout plans online: secure payment processing, product listings with images and descriptions, inventory management, and a mobile-responsive design. All our packages come with domain setup, SEO optimization, and 48-hour delivery. Does this sound like what you're looking for?",
        "payment": "We use Stripe for secure payment processing. Once you decide on a package, I'll send you a payment link. After your payment is confirmed, we'll start work immediately and send you an intake form to gather the specific details about your website requirements. We'll deliver the completed website within 48 hours of receiving your completed form.",
        "proceed": "Great! I'm processing your order for the E-commerce package. This includes all the features we discussed for selling your workout plans online."
    }
    
    default_response = "Thanks for reaching out! I'd be happy to help with your website needs. Our team specializes in creating high-performance websites delivered in just 48 hours. Could you tell me a bit more about your business and what kind of website you're looking for?"
    
    # Determine which response to use based on keywords in the message
    response_text = default_response
    for key, response in responses.items():
        if key.lower() in last_message.lower():
            response_text = response
            break
    
    if "proceed" in last_message.lower() or "package" in last_message.lower():
        mock_message = {"content": response_text}
        mock_choices = [type('obj', (object,), {'message': mock_message})]
        return type('obj', (object,), {'choices': mock_choices})
    
    mock_message = {"content": response_text}
    mock_choices = [type('obj', (object,), {'message': mock_message})]
    return type('obj', (object,), {'choices': mock_choices})

# Patch OpenAI methods
openai.Completion.create = mock_completion_create
openai.ChatCompletion.create = mock_chat_completion_create

# Now import the chatbot
try:
    from chatbot import chatbot, ChatbotResponse
except ImportError:
    logger.error("Failed to import chatbot. Make sure you're in the correct directory.")
    sys.exit(1)

def simulate_conversation():
    """Simulate a conversation with the chatbot to test its functionality."""
    test_lead_id = "test_user_" + os.urandom(4).hex()
    platform = "test"
    
    # Define test conversation
    test_messages = [
        "Hey, I saw your message about building websites. Do you have examples of your work?",
        "I run a small fitness business and need a website. What would you recommend?",
        "I'm interested in e-commerce since I sell workout plans. How much would that cost?",
        "That sounds reasonable. How does the payment process work?",
        "Yes, I'd like to proceed with the e-commerce package."
    ]
    
    print(f"\n{'='*80}\nTesting AI Chatbot Conversation\n{'='*80}\n")
    print(f"Test Lead ID: {test_lead_id}\nPlatform: {platform}\n")
    
    # Process each message and display responses
    for i, message in enumerate(test_messages):
        print(f"\n--- User Message {i+1} ---")
        print(f"{message}")
        
        # Get chatbot response
        response = chatbot.process_message(test_lead_id, platform, message)
        
        print(f"\n--- Chatbot Response {i+1} ---")
        print(f"{response.message}")
        
        if response.actions:
            print("\n--- Actions ---")
            for action in response.actions:
                print(f"Type: {action.get('type')}")
                if action.get('type') == 'payment_link':
                    print(f"Package: {action.get('package')}")
                    print(f"Link: {action.get('link')}")
        
        print(f"\n{'-'*80}")
    
    # Test follow-up generation
    print("\n--- Testing Follow-up Generation ---")
    print("Checking for inactive conversations and generating follow-ups...\n")
    
    # Add a fake timestamp to make the conversation appear inactive
    conversation = chatbot.conversations.get(test_lead_id)
    if conversation:
        # Import datetime with a break to avoid circular imports
        from datetime import datetime, timedelta
        # Set last updated to 2 days ago
        old_date = datetime.now() - timedelta(days=2)
        conversation.last_updated = old_date.strftime("%Y-%m-%d %H:%M:%S")
        chatbot.save_conversations()
        
        # Check for inactive conversations
        chatbot.check_inactive_conversations()
        
        # Display the follow-up message
        print("Follow-up message generated:")
        if len(conversation.messages) > len(test_messages) * 2:
            print(conversation.messages[-1].content)
        else:
            print("No follow-up was generated.")
    
    print(f"\n{'='*80}\nTest completed\n{'='*80}\n")

def main():
    """Main function to run the chatbot test."""
    try:
        simulate_conversation()
    except Exception as e:
        logger.error(f"Error in chatbot test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 