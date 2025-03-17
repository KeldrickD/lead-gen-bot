#!/usr/bin/env python3
"""
Simple test script to verify the basic functionality of the AI chatbot components.
This doesn't require actually importing the chatbot module.
"""

import os
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('simple_test')

# Mock data
mock_lead_id = "test_user_123"
mock_platform = "test"
mock_messages = [
    {
        "role": "user",
        "content": "Hey, I saw your message about building websites. Do you have examples of your work?",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "role": "assistant",
        "content": "I'd be happy to show you examples of our work. We've created websites for businesses in various industries including fitness, retail, consulting, and tech startups. Each website is designed to be mobile-responsive, fast-loading, and optimized for conversions. Would you like me to send you a link to our portfolio?",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "role": "user",
        "content": "I run a small fitness business and need a website. What would you recommend?",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]

def test_conversation_storage():
    """Test storing and retrieving conversations."""
    try:
        # Create a mock conversation
        conversation = {
            "lead_id": mock_lead_id,
            "platform": mock_platform,
            "messages": mock_messages,
            "qualified": True,
            "payment_sent": False,
            "payment_completed": False,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "inactive_days": 0
        }
        
        # Store all conversations
        conversations = {mock_lead_id: conversation}
        
        with open('test_conversations.json', 'w') as f:
            json.dump(conversations, f, indent=2)
            
        logger.info("Successfully saved mock conversation to test_conversations.json")
        
        # Now read it back
        with open('test_conversations.json', 'r') as f:
            loaded_conversations = json.load(f)
            
        if mock_lead_id in loaded_conversations:
            logger.info("Successfully loaded mock conversation from file")
            loaded_messages = loaded_conversations[mock_lead_id]["messages"]
            logger.info(f"The conversation has {len(loaded_messages)} messages")
            
            # Print some details
            print("\n====== Conversation Test ======")
            print(f"Lead ID: {mock_lead_id}")
            print(f"Platform: {mock_platform}")
            print(f"Number of messages: {len(loaded_messages)}")
            print(f"Qualified: {loaded_conversations[mock_lead_id]['qualified']}")
            print(f"Last updated: {loaded_conversations[mock_lead_id]['last_updated']}")
            print("\n====== Message Contents ======")
            
            for idx, msg in enumerate(loaded_messages):
                print(f"\nMessage {idx+1} ({msg['role']}):")
                print(f"{msg['content']}")
                
            print("\n====== Test Complete ======")
            return True
        else:
            logger.error("Failed to find the lead ID in the loaded conversations")
            return False
            
    except Exception as e:
        logger.error(f"Error in conversation test: {e}")
        return False

def test_stripe_integration_mock():
    """Test the mock Stripe payment link generation."""
    try:
        # Mock function to generate payment links
        def generate_stripe_payment_link(package_type):
            base_url = "https://buy.stripe.com/test/"
            
            if package_type.lower() == "basic" or package_type.lower() == "business":
                return f"{base_url}basic_website_497"
            elif package_type.lower() == "ecommerce" or package_type.lower() == "e-commerce":
                return f"{base_url}ecommerce_website_997"
            elif package_type.lower() == "custom":
                return f"{base_url}custom_website_1997"
            else:
                return f"{base_url}consultation"
        
        # Test different package types
        packages = ["basic", "ecommerce", "custom", "unknown"]
        
        print("\n====== Stripe Payment Link Test ======")
        for package in packages:
            link = generate_stripe_payment_link(package)
            print(f"Package: {package} -> Payment link: {link}")
        
        print("====== Test Complete ======")
        return True
        
    except Exception as e:
        logger.error(f"Error in Stripe integration test: {e}")
        return False

def test_follow_up_logic():
    """Test the follow-up message generation logic."""
    try:
        # Mock data
        conversation = {
            "lead_id": mock_lead_id,
            "platform": mock_platform,
            "messages": mock_messages,
            "qualified": True,
            "payment_sent": False,
            "payment_completed": False,
            "last_updated": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "inactive_days": 2
        }
        
        # Mock follow-up message generation
        follow_up_message = "I noticed it's been a couple of days since we last spoke about your fitness business website. I'm still here to help if you have any questions or want to proceed. What specific features would you need for your fitness website?"
        
        # Add follow-up to conversation
        conversation["messages"].append({
            "role": "assistant",
            "content": follow_up_message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        print("\n====== Follow-up Message Test ======")
        print(f"Lead ID: {conversation['lead_id']}")
        print(f"Inactive for: {conversation['inactive_days']} days")
        print(f"Follow-up message: {follow_up_message}")
        print("====== Test Complete ======")
        return True
        
    except Exception as e:
        logger.error(f"Error in follow-up logic test: {e}")
        return False

def main():
    """Run all tests."""
    print("\n======================================")
    print("Starting AI Chatbot Component Tests")
    print("======================================\n")
    
    test_results = {
        "conversation_storage": test_conversation_storage(),
        "stripe_integration": test_stripe_integration_mock(),
        "follow_up_logic": test_follow_up_logic()
    }
    
    # Print summary
    print("\n======================================")
    print("Test Results Summary")
    print("======================================")
    
    for test_name, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print("\n======================================")
    
    # Return success if all tests passed
    return all(test_results.values())

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 