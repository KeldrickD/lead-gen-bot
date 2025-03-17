import os
import openai
import random
import json
from datetime import datetime
from utils import load_config, logger, format_timestamp

class MessageGenerator:
    def __init__(self):
        self.config = load_config()
        self.setup_openai()
        self.message_templates = {
            "initial": [
                # Value proposition focused
                "Hey {owner_name}! I came across {business_name} and noticed you're doing great work. Have you thought about setting up a professional website to get even more clients? I build sleek, high-converting sites in 48 hours—happy to show you what I can do!",
                
                # Problem-solution focused
                "Hi {owner_name}! Just checked out your {business_type} business ({business_name}) and really like what you're doing. Would you be interested in a professional website that can help you book more clients? I specialize in designing websites for {business_type}s that convert visitors into customers.",
                
                # Direct offer focused
                "Hey there {owner_name}! Your {business_type} business ({business_name}) caught my eye. Have you considered how a professional website could help grow your client base? I create custom websites specifically for {business_type}s that can be ready in just 48 hours.",
                
                # Question-based approach
                "Hi {owner_name}, I noticed your {business_type} business ({business_name}) online. Are you currently happy with how you're booking new clients? I help {business_type} businesses increase bookings with custom websites designed specifically for your industry.",
                
                # Social proof focused
                "Hey {owner_name}! Your {business_type} business ({business_name}) looks great! I've helped several {business_type}s in your area increase their client base by 30% with professional websites. Would you be interested in seeing some examples?",
            ],
            "follow_up": [
                # Casual reminder
                "Hey {owner_name}, just following up on my previous message. Still interested in helping {business_name} get more clients with a professional website. Let me know if you'd like to chat about it!",
                
                # Value proposition reminder
                "Hi again {owner_name}! Just checking in—would you be interested in seeing some examples of websites I've built for other {business_type}s? No pressure, just thought it might be helpful for {business_name}.",
                
                # Direct offer reminder
                "Hey {owner_name}, just wanted to make sure you saw my previous message about creating a website for {business_name}. I've helped many {business_type}s increase their bookings with professional sites. Let me know if you're interested!",
                
                # Special offer approach
                "Hi {owner_name}, I'm following up about creating a website for {business_name}. This week I'm offering a special deal for {business_type} businesses that includes a free month of SEO services. Let me know if you'd like to learn more!",
                
                # Social proof follow-up
                "Hey {owner_name}, just checking in. I recently completed a website for another {business_type} business that increased their bookings by 40%. Would you be interested in seeing how I could help {business_name} achieve similar results?"
            ]
        }
        
        # Initialize performance tracking
        self.template_performance = self.load_template_performance()
    
    def load_template_performance(self):
        """Load performance data for message templates from file."""
        try:
            if os.path.exists("template_performance.json"):
                with open("template_performance.json", "r") as f:
                    return json.load(f)
            else:
                # Initialize with default structure
                performance = {
                    "initial": {},
                    "follow_up": {}
                }
                for i, template in enumerate(self.message_templates["initial"]):
                    performance["initial"][f"template_{i+1}"] = {
                        "sent_count": 0,
                        "response_count": 0,
                        "conversion_count": 0,
                        "template": template
                    }
                
                for i, template in enumerate(self.message_templates["follow_up"]):
                    performance["follow_up"][f"template_{i+1}"] = {
                        "sent_count": 0,
                        "response_count": 0,
                        "conversion_count": 0,
                        "template": template
                    }
                return performance
        except Exception as e:
            logger.error(f"Error loading template performance data: {e}")
            return {"initial": {}, "follow_up": {}}
    
    def save_template_performance(self):
        """Save template performance data to file."""
        try:
            with open("template_performance.json", "w") as f:
                json.dump(self.template_performance, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving template performance data: {e}")
            return False
    
    def track_message_sent(self, template_id, message_type):
        """Track that a message with a specific template was sent."""
        try:
            if template_id in self.template_performance.get(message_type, {}):
                self.template_performance[message_type][template_id]["sent_count"] += 1
                self.template_performance[message_type][template_id]["last_sent"] = format_timestamp()
                self.save_template_performance()
                return True
            return False
        except Exception as e:
            logger.error(f"Error tracking message sent: {e}")
            return False
    
    def track_message_response(self, template_id, message_type, converted=False):
        """Track that a message with a specific template received a response."""
        try:
            if template_id in self.template_performance.get(message_type, {}):
                self.template_performance[message_type][template_id]["response_count"] += 1
                if converted:
                    self.template_performance[message_type][template_id]["conversion_count"] += 1
                self.save_template_performance()
                return True
            return False
        except Exception as e:
            logger.error(f"Error tracking message response: {e}")
            return False
    
    def get_best_performing_template(self, message_type="initial"):
        """Get the best performing template based on response rate."""
        try:
            templates = self.template_performance.get(message_type, {})
            if not templates:
                return None
            
            # Calculate response rates
            response_rates = {}
            for template_id, data in templates.items():
                sent_count = data.get("sent_count", 0)
                if sent_count > 0:
                    response_rate = data.get("response_count", 0) / sent_count
                    response_rates[template_id] = response_rate
            
            # Get the template with the highest response rate
            if response_rates:
                best_template_id = max(response_rates, key=response_rates.get)
                return best_template_id, self.template_performance[message_type][best_template_id]["template"]
            
            return None
        except Exception as e:
            logger.error(f"Error getting best performing template: {e}")
            return None
    
    def setup_openai(self):
        """Set up the OpenAI API with the API key from config."""
        try:
            api_key = self.config.get("openai", {}).get("api_key")
            if not api_key:
                logger.warning("OpenAI API key not found in config. Using environment variable.")
                api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                logger.error("No OpenAI API key found in config or environment variables")
                return False
            
            openai.api_key = api_key
            return True
        except Exception as e:
            logger.error(f"Error setting up OpenAI API: {e}")
            return False
    
    def generate_message_from_template(self, lead_data, message_type="initial"):
        """Generate a message from a template for a specific lead."""
        try:
            templates = self.message_templates.get(message_type, self.message_templates["initial"])
            
            # Choose either best performing template if available or random
            best_template = self.get_best_performing_template(message_type)
            
            # 80% of the time use the best template if we have one with enough data
            # Otherwise use random template for exploration
            if best_template and random.random() < 0.8:
                template_id, template = best_template
                logger.info(f"Using best performing template ({template_id}) for {message_type} message")
            else:
                template_index = random.randint(0, len(templates) - 1)
                template_id = f"template_{template_index + 1}"
                template = templates[template_index]
                logger.info(f"Using random template ({template_id}) for {message_type} message")
            
            # Extract the necessary information from lead data
            business_name = lead_data.get("full_name", lead_data.get("username", "your business"))
            business_type = lead_data.get("business_type", "business")
            owner_name = lead_data.get("owner_name", "there")
            
            # Format the template with lead data
            message = template.format(
                owner_name=owner_name,
                business_name=business_name,
                business_type=business_type
            )
            
            # Track that this template was used
            self.track_message_sent(template_id, message_type)
            
            # Store the template ID with the message for future tracking
            message_data = {
                "text": message,
                "template_id": template_id,
                "message_type": message_type,
                "timestamp": format_timestamp()
            }
            
            return message_data
        except Exception as e:
            logger.error(f"Error generating message from template: {e}")
            default_message = "Hey there! I noticed your business and thought you might be interested in a professional website. I specialize in creating websites that convert visitors into customers. Let me know if you're interested!"
            return {
                "text": default_message,
                "template_id": "default",
                "message_type": message_type,
                "timestamp": format_timestamp()
            }
    
    def generate_message_with_gpt(self, lead_data, message_type="initial"):
        """Generate a personalized message using GPT API for a specific lead."""
        try:
            # Extract the necessary information from lead data
            business_name = lead_data.get("full_name", lead_data.get("username", "your business"))
            business_type = lead_data.get("business_type", "business")
            owner_name = lead_data.get("owner_name", "there")
            
            # Create the prompt for GPT
            if message_type == "initial":
                prompt = f"Write a friendly, engaging first DM offering website setup services for a {business_type} business named {business_name}. Address the owner as {owner_name}. Keep it short, natural, and mention you build websites specifically for {business_type}s that help get more clients. Don't use hashtags or emojis. Max 2-3 sentences."
            else:  # follow_up
                prompt = f"Write a friendly, non-pushy follow-up DM for {business_name}, a {business_type} business. Address the owner as {owner_name}. Mention that you're following up on your previous message about creating a website. Keep it short and natural. Max 2 sentences."
            
            # Call the OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that writes natural, personalized outreach messages for business owners. Your messages are concise, engaging, and sound like they were written by a real person, not a bot."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            message_text = response["choices"][0]["message"]["content"].strip()
            
            # Log the generated message
            logger.info(f"Generated {message_type} message for {business_name} using GPT")
            
            message_data = {
                "text": message_text,
                "template_id": "gpt_generated",
                "message_type": message_type,
                "timestamp": format_timestamp()
            }
            
            return message_data
        except Exception as e:
            logger.error(f"Error generating message with GPT: {e}")
            # Fallback to template-based message
            return self.generate_message_from_template(lead_data, message_type)
    
    def generate_message(self, lead_data, message_type="initial", use_gpt=True):
        """Generate a message for a lead, using GPT if available or templates as fallback."""
        if use_gpt:
            try:
                return self.generate_message_with_gpt(lead_data, message_type)
            except:
                logger.warning("Failed to generate message with GPT, falling back to template")
                return self.generate_message_from_template(lead_data, message_type)
        else:
            return self.generate_message_from_template(lead_data, message_type)
    
    def get_performance_report(self):
        """Generate a report on template performance."""
        report = []
        report.append("MESSAGE TEMPLATE PERFORMANCE REPORT\n")
        
        for message_type in ["initial", "follow_up"]:
            report.append(f"\n{message_type.upper()} MESSAGES:")
            templates = self.template_performance.get(message_type, {})
            
            for template_id, data in templates.items():
                sent = data.get("sent_count", 0)
                responses = data.get("response_count", 0)
                conversions = data.get("conversion_count", 0)
                
                if sent > 0:
                    response_rate = (responses / sent) * 100
                    if responses > 0:
                        conversion_rate = (conversions / responses) * 100
                    else:
                        conversion_rate = 0
                else:
                    response_rate = 0
                    conversion_rate = 0
                
                report.append(f"\n{template_id}:")
                report.append(f"  Sent: {sent}")
                report.append(f"  Responses: {responses} ({response_rate:.1f}%)")
                report.append(f"  Conversions: {conversions} ({conversion_rate:.1f}%)")
                
                # Only show template text for non-GPT templates
                if template_id != "gpt_generated":
                    template_text = data.get("template", "").replace("\n", " ")
                    if len(template_text) > 50:
                        template_text = template_text[:50] + "..."
                    report.append(f"  Template: {template_text}")
        
        return "\n".join(report)

if __name__ == "__main__":
    # Example usage
    generator = MessageGenerator()
    
    # Test lead data
    test_lead = {
        "username": "elite_cuts",
        "full_name": "Elite Barbershop",
        "owner_name": "Mike",
        "business_type": "Barber Shop"
    }
    
    # Generate messages
    initial_message = generator.generate_message(test_lead, "initial")
    follow_up_message = generator.generate_message(test_lead, "follow_up")
    
    print("Initial Message:")
    print(initial_message["text"])
    print("\nFollow-up Message:")
    print(follow_up_message["text"])
    
    # Print performance report
    print("\n" + generator.get_performance_report()) 