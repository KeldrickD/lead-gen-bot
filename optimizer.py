import os
import json
import logging
import random
from datetime import datetime, timedelta
from analytics import Analytics

# Set up logging
logger = logging.getLogger('lead-gen-bot')

class MessageOptimizer:
    def __init__(self):
        """Initialize the message optimizer."""
        self.analytics = Analytics()
        self.template_performance_file = 'template_performance.json'
        self.optimized_templates_file = 'optimized_templates.json'
        self.optimization_history_file = 'optimization_history.json'
        
        # Create optimization history file if it doesn't exist
        if not os.path.exists(self.optimization_history_file):
            with open(self.optimization_history_file, 'w') as f:
                json.dump({
                    "initial": [],
                    "follow_up": []
                }, f, indent=2)
    
    def load_template_performance(self):
        """Load template performance data."""
        try:
            with open(self.template_performance_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading template performance data: {e}")
            return {"initial": {}, "follow_up": {}}
    
    def save_template_performance(self, data):
        """Save template performance data."""
        try:
            with open(self.template_performance_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Saved updated template performance data")
        except Exception as e:
            logger.error(f"Error saving template performance data: {e}")
    
    def load_optimization_history(self):
        """Load optimization history."""
        try:
            with open(self.optimization_history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading optimization history: {e}")
            return {"initial": [], "follow_up": []}
    
    def save_optimization_history(self, data):
        """Save optimization history."""
        try:
            with open(self.optimization_history_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info("Saved optimization history")
        except Exception as e:
            logger.error(f"Error saving optimization history: {e}")
    
    def find_best_performing_templates(self):
        """Find the best performing templates for initial and follow-up messages."""
        template_data = self.load_template_performance()
        
        best_templates = {
            "initial": None,
            "follow_up": None
        }
        
        # Find best initial template
        initial_templates = []
        for template_id, data in template_data["initial"].items():
            if "sent_count" in data and data["sent_count"] >= 10:  # Minimum sample size
                response_rate = data.get("response_count", 0) / data["sent_count"]
                conversion_rate = data.get("conversion_count", 0) / data["sent_count"]
                score = response_rate * 0.7 + conversion_rate * 0.3  # Weighted score
                
                initial_templates.append({
                    "template_id": template_id,
                    "score": score,
                    "response_rate": response_rate,
                    "conversion_rate": conversion_rate,
                    "sent_count": data["sent_count"],
                    "template": data.get("template", "")
                })
        
        if initial_templates:
            best_templates["initial"] = sorted(initial_templates, key=lambda x: x["score"], reverse=True)[0]
        
        # Find best follow-up template
        follow_up_templates = []
        for template_id, data in template_data["follow_up"].items():
            if "sent_count" in data and data["sent_count"] >= 5:  # Lower minimum for follow-ups
                response_rate = data.get("response_count", 0) / data["sent_count"]
                conversion_rate = data.get("conversion_count", 0) / data["sent_count"]
                score = response_rate * 0.7 + conversion_rate * 0.3  # Weighted score
                
                follow_up_templates.append({
                    "template_id": template_id,
                    "score": score,
                    "response_rate": response_rate,
                    "conversion_rate": conversion_rate,
                    "sent_count": data["sent_count"],
                    "template": data.get("template", "")
                })
        
        if follow_up_templates:
            best_templates["follow_up"] = sorted(follow_up_templates, key=lambda x: x["score"], reverse=True)[0]
        
        return best_templates
    
    def generate_variants(self, template, type_key):
        """Generate variants of a template based on performance patterns."""
        variants = []
        
        if not template:
            logger.warning(f"No good template found for {type_key} to generate variants")
            return variants
        
        template_text = template["template"]
        
        # Common improvements to try
        improvements = [
            ("Add emojis", self._add_emojis),
            ("Make more concise", self._make_concise),
            ("Add question", self._add_question),
            ("Add social proof", self._add_social_proof),
            ("Add urgency", self._add_urgency)
        ]
        
        # Generate variants using different improvement strategies
        for improvement_name, improvement_func in improvements:
            try:
                variant = improvement_func(template_text, type_key)
                variants.append({
                    "template_id": f"{type_key}_{len(variants) + 1}",
                    "improvement": improvement_name,
                    "template": variant,
                    "base_template_id": template["template_id"],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                logger.error(f"Error generating {improvement_name} variant: {e}")
        
        return variants
    
    def _add_emojis(self, template_text, type_key):
        """Add relevant emojis to the template."""
        # Map of business types to relevant emojis
        business_emojis = {
            "default": ["👋", "👍", "🙌", "✨", "🔥"],
            "restaurant": ["🍽️", "🍕", "🍔", "🥗", "🍷"],
            "fitness": ["💪", "🏋️", "🧘", "🏃", "🥗"],
            "salon": ["💇", "💅", "✂️", "💆", "👩"],
            "spa": ["💆", "🧖", "✨", "🌿", "🌊"],
            "retail": ["🛍️", "👕", "👗", "👟", "🎁"],
            "bakery": ["🍞", "🥐", "🎂", "🧁", "🍪"],
            "cafe": ["☕", "🍵", "🥐", "🍰", "🧁"],
            "gym": ["💪", "🏋️", "🤸", "🏃", "🏆"],
            "yoga": ["🧘", "✨", "🌿", "💆", "🙏"],
            "dental": ["😁", "✨", "🦷", "👩‍⚕️", "👨‍⚕️"],
            "chiropractic": ["💆", "✨", "🔄", "👩‍⚕️", "👨‍⚕️"],
            "nail": ["💅", "✨", "🌈", "👑", "💖"],
            "hair": ["💇", "✂️", "💁", "✨", "👩"]
        }
        
        general_emojis = ["👋", "👍", "🙌", "✨", "😊", "📈", "🌟", "🚀"]
        
        # Select 2-3 emojis
        selected_emojis = random.sample(general_emojis, 2)
        
        # Add emojis at strategic points
        lines = template_text.split('\n')
        modified_lines = []
        
        for i, line in enumerate(lines):
            if i == 0:  # First line - greeting
                if not any(emoji in line for emoji in ["👋", "🙌", "😊"]):
                    line = f"{selected_emojis[0]} {line}"
            
            # Add emoji near call to action or important points
            if any(phrase in line.lower() for phrase in ["would you be interested", "happy to", "help you", "increase"]):
                if not any(emoji in line for emoji in ["🔥", "⭐", "✨", "🚀"]):
                    line = f"{line} {selected_emojis[1]}"
            
            modified_lines.append(line)
        
        return '\n'.join(modified_lines)
    
    def _make_concise(self, template_text, type_key):
        """Make the template more concise."""
        # Split into sentences
        template_text = template_text.replace('\n', ' ')
        sentences = []
        current = ""
        
        for char in template_text:
            current += char
            if char in ['.', '!', '?'] and len(current.strip()) > 0:
                sentences.append(current.strip())
                current = ""
        
        if current.strip():
            sentences.append(current.strip())
        
        # Remove unnecessary phrases
        phrases_to_remove = [
            "I hope this message finds you well",
            "I wanted to reach out",
            "I am writing to",
            "Just wanted to",
            "I thought I would"
        ]
        
        condensed_sentences = []
        for sentence in sentences:
            should_keep = True
            for phrase in phrases_to_remove:
                if phrase.lower() in sentence.lower():
                    should_keep = False
                    break
            
            if should_keep:
                condensed_sentences.append(sentence)
        
        # Combine shorter sentences
        result = ' '.join(condensed_sentences)
        
        # Ensure it includes placeholders
        if '{owner_name}' not in result:
            result = f"Hi {{owner_name}}! {result}"
            
        if '{business_name}' not in result and '{business_type}' not in result:
            result = result.replace("!", f"! I noticed your {{business_type}} business ({{business_name}}).")
            
        return result
    
    def _add_question(self, template_text, type_key):
        """Add a strategic question to the template."""
        questions = [
            "Are you currently happy with how you're booking new clients?",
            "Would you be interested in seeing examples of websites I've built for businesses like yours?",
            "Have you considered how a professional website could help you book more clients?",
            "Are you happy with your current number of bookings?",
            "What would it mean for your business if you could increase bookings by 30% this month?"
        ]
        
        # Don't add a question if one already exists
        if any(q in template_text for q in ["?", "interested", "considered", "happy"]):
            # Modify existing question instead
            for phrase in ["Would you be interested", "Are you interested", "Have you considered"]:
                if phrase.lower() in template_text.lower():
                    return template_text.replace(phrase, f"I'm curious - {phrase.lower()}")
            
            # If we can't find a specific phrase to modify, just return the original
            return template_text
        
        # Add a question
        selected_question = random.choice(questions)
        
        # Find a good place to insert the question
        lines = template_text.split('\n')
        
        # If there's only one line, append the question
        if len(lines) == 1:
            return f"{template_text} {selected_question}"
        
        # Otherwise, insert it before the last line
        lines.insert(-1, selected_question)
        return '\n'.join(lines)
    
    def _add_social_proof(self, template_text, type_key):
        """Add social proof to the template."""
        social_proofs = [
            "I've helped {business_type} businesses increase bookings by 30% on average.",
            "I recently helped another {business_type} business increase their bookings by 40% with a new website.",
            "My clients in the {business_type} industry have seen a 35% increase in bookings within just 2 months.",
            "Other {business_type} businesses I've worked with have been able to book 25-40% more clients.",
            "One {business_type} business I worked with went from 10 bookings per week to over 25 after launching their new site."
        ]
        
        # Don't add social proof if it already exists
        if any(phrase in template_text.lower() for phrase in ["increase", "bookings by", "helped", "clients have"]):
            return template_text
        
        # Add social proof
        selected_proof = random.choice(social_proofs)
        
        # Find a good place to insert the social proof
        if type_key == "initial":
            # For initial messages, add it in the middle
            lines = template_text.split('\n')
            
            if len(lines) <= 2:
                # Short template, just append
                return f"{template_text}\n\n{selected_proof}"
            
            # Insert after the first or second line
            insert_position = min(2, len(lines) - 1)
            lines.insert(insert_position, selected_proof)
            return '\n'.join(lines)
        else:
            # For follow-ups, add at the end
            return f"{template_text}\n\n{selected_proof}"
    
    def _add_urgency(self, template_text, type_key):
        """Add urgency to the template."""
        urgency_phrases = [
            "I'm currently taking on new clients this week and have a limited number of spots available.",
            "I have a special offer this month for new {business_type} clients.",
            "I only work with a limited number of {business_type} businesses each month, and I have a couple spots left.",
            "I'm offering a 15% discount for new clients who sign up this week.",
            "For the next few days, I'm offering a free consultation and website audit for {business_type} businesses."
        ]
        
        # Don't add urgency if it already exists
        if any(phrase in template_text.lower() for phrase in ["limited", "special offer", "discount", "this week", "spots"]):
            return template_text
        
        # Add urgency
        selected_urgency = random.choice(urgency_phrases)
        
        # For both initial and follow-up, add at the end
        return f"{template_text}\n\n{selected_urgency}"
    
    def update_templates_file(self, new_variants):
        """Update the templates file with new variants."""
        try:
            template_data = self.load_template_performance()
            
            # Add new variants
            for type_key, variants in new_variants.items():
                for variant in variants:
                    template_id = variant["template_id"]
                    
                    # Initialize template in performance data if it doesn't exist
                    if template_id not in template_data[type_key]:
                        template_data[type_key][template_id] = {
                            "template": variant["template"],
                            "sent_count": 0,
                            "response_count": 0,
                            "conversion_count": 0,
                            "created_at": variant["created_at"],
                            "improved_from": variant["base_template_id"],
                            "improvement": variant["improvement"]
                        }
            
            # Save updated template data
            self.save_template_performance(template_data)
            
            # Update optimization history
            history = self.load_optimization_history()
            for type_key, variants in new_variants.items():
                for variant in variants:
                    history[type_key].append({
                        "date": variant["created_at"],
                        "template_id": variant["template_id"],
                        "improvement": variant["improvement"],
                        "base_template_id": variant["base_template_id"]
                    })
            
            self.save_optimization_history(history)
            
            return True
        except Exception as e:
            logger.error(f"Error updating templates file: {e}")
            return False
    
    def optimize_templates(self):
        """Main method to optimize templates based on performance data."""
        logger.info("Starting template optimization process")
        
        # Find best performing templates
        best_templates = self.find_best_performing_templates()
        
        # Generate variants
        new_variants = {
            "initial": [],
            "follow_up": []
        }
        
        if best_templates["initial"]:
            logger.info(f"Generating variants for best initial template: {best_templates['initial']['template_id']}")
            new_variants["initial"] = self.generate_variants(best_templates["initial"], "initial")
        else:
            logger.warning("No good initial template found for optimization")
        
        if best_templates["follow_up"]:
            logger.info(f"Generating variants for best follow-up template: {best_templates['follow_up']['template_id']}")
            new_variants["follow_up"] = self.generate_variants(best_templates["follow_up"], "follow_up")
        else:
            logger.warning("No good follow-up template found for optimization")
        
        # Update template file with new variants
        if new_variants["initial"] or new_variants["follow_up"]:
            success = self.update_templates_file(new_variants)
            if success:
                logger.info(f"Template optimization complete. Added {len(new_variants['initial'])} initial variants and {len(new_variants['follow_up'])} follow-up variants")
                return True
            else:
                logger.error("Failed to update templates file")
                return False
        else:
            logger.warning("No new template variants were generated")
            return False
            
    def get_optimization_results(self):
        """Get the results of the optimization process."""
        history = self.load_optimization_history()
        templates = self.load_template_performance()
        
        results = {
            "initial": [],
            "follow_up": []
        }
        
        for type_key in ["initial", "follow_up"]:
            # Get the most recent optimization entries
            recent_entries = sorted(history[type_key], key=lambda x: x.get("date", ""), reverse=True)[:5]
            
            for entry in recent_entries:
                template_id = entry.get("template_id")
                if template_id and template_id in templates[type_key]:
                    template_data = templates[type_key][template_id]
                    
                    # Calculate performance metrics
                    sent_count = template_data.get("sent_count", 0)
                    response_rate = template_data.get("response_count", 0) / sent_count if sent_count > 0 else 0
                    conversion_rate = template_data.get("conversion_count", 0) / sent_count if sent_count > 0 else 0
                    
                    # Get base template for comparison
                    base_template_id = entry.get("base_template_id")
                    base_sent_count = 0
                    base_response_rate = 0
                    base_conversion_rate = 0
                    
                    if base_template_id and base_template_id in templates[type_key]:
                        base_data = templates[type_key][base_template_id]
                        base_sent_count = base_data.get("sent_count", 0)
                        base_response_rate = base_data.get("response_count", 0) / base_sent_count if base_sent_count > 0 else 0
                        base_conversion_rate = base_data.get("conversion_count", 0) / base_sent_count if base_sent_count > 0 else 0
                    
                    results[type_key].append({
                        "template_id": template_id,
                        "improvement": entry.get("improvement", ""),
                        "base_template_id": base_template_id,
                        "sent_count": sent_count,
                        "response_rate": response_rate,
                        "conversion_rate": conversion_rate,
                        "base_sent_count": base_sent_count,
                        "base_response_rate": base_response_rate,
                        "base_conversion_rate": base_conversion_rate,
                        "response_rate_change": response_rate - base_response_rate if base_sent_count > 0 else None,
                        "conversion_rate_change": conversion_rate - base_conversion_rate if base_sent_count > 0 else None
                    })
        
        return results

# Usage example
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - lead-gen-bot - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    optimizer = MessageOptimizer()
    success = optimizer.optimize_templates()
    
    if success:
        print("Template optimization complete!")
        
        # Print optimization results
        results = optimizer.get_optimization_results()
        
        print("\nOptimization Results:")
        for type_key in ["initial", "follow_up"]:
            print(f"\n{type_key.capitalize()} Templates:")
            
            if not results[type_key]:
                print("  No optimization data available")
                continue
                
            for result in results[type_key]:
                print(f"  {result['template_id']} ({result['improvement']}):")
                print(f"    Sent: {result['sent_count']}")
                print(f"    Response Rate: {result['response_rate']*100:.1f}%")
                
                if result['response_rate_change'] is not None:
                    change = result['response_rate_change'] * 100
                    direction = "+" if change >= 0 else ""
                    print(f"    Response Rate Change: {direction}{change:.1f}% from {result['base_template_id']}")
                
                print(f"    Conversion Rate: {result['conversion_rate']*100:.1f}%")
                
                if result['conversion_rate_change'] is not None:
                    change = result['conversion_rate_change'] * 100
                    direction = "+" if change >= 0 else ""
                    print(f"    Conversion Rate Change: {direction}{change:.1f}% from {result['base_template_id']}")
                
                print() 