# Lead Generation Bot

An AI agent that automates DM outreach to business owners on social media platforms.

## Features

- Automates DM outreach on Instagram, Facebook, LinkedIn, and Twitter
- Personalizes messages for each lead using GPT
- Tracks responses and follows up automatically
- Hands off warm leads for closing deals

## New Features

- **Analytics Dashboard**: Web-based dashboard for monitoring performance metrics
- **Template Optimization**: AI-powered optimization of message templates based on performance
- **Performance Tracking**: Track response rates and conversion metrics
- **Smart Follow-ups**: Intelligent follow-up timing based on performance data
- **Anti-Ban Protection**: Built-in protection against platform restrictions

## Requirements

- Python 3.7+
- Selenium or Playwright for browser automation
- OpenAI API key for GPT-powered message generation
- Social media accounts for outreach
- Chrome browser installed

## Setup

1. Clone this repository to your local machine.

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Copy the example environment file and fill in your credentials:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file with your API keys and social media credentials.

4. Update the `config.json` file with your preferences:
   - Set daily DM limits for each platform
   - Configure lead sources (hashtags, business types)
   - Set follow-up timing and preferences

5. For Google Sheets integration (optional):
   - Create a Google Sheets API key and download credentials
   - Create a spreadsheet and note its ID
   - Update the `config.json` with these details

## Usage

### Windows

Use the `run.bat` script to execute the bot:

```
# Run in schedule mode (default)
run.bat

# Collect leads only
run.bat collect instagram 20

# Send initial messages
run.bat message instagram 20 15

# Send follow-up messages
run.bat follow_up instagram

# Run complete workflow
run.bat run_all
```

### Mac/Linux

Use the `run.sh` script to execute the bot:

```
# Make the script executable
chmod +x run.sh

# Run in schedule mode (default)
./run.sh

# Collect leads only
./run.sh collect instagram 20

# Send initial messages
./run.sh message instagram 20 15

# Send follow-up messages
./run.sh follow_up instagram

# Run complete workflow
./run.sh run_all
```

### Manual Execution

You can also run the bot directly with Python:

```
python main.py --action schedule
python main.py --action collect --platform instagram --max_leads 20
python main.py --action message --platform instagram --max_leads 20 --max_dms 15
python main.py --action follow_up --platform instagram
python main.py --action run_all
python main.py --action analytics
python main.py --action optimize
python main.py --action dashboard
```

### Dashboard

To start the bot with the analytics dashboard:

```
# Windows
start_bot_with_dashboard.bat

# Mac/Linux
chmod +x start_bot_with_dashboard.sh
./start_bot_with_dashboard.sh
```

Access the dashboard in your browser at http://localhost:5000

## How It Works

1. **Lead Collection**: The bot scrapes business profiles from social media platforms based on hashtags, locations, or other criteria.

2. **Message Generation**: For each lead, the bot generates a personalized message using OpenAI's GPT model, considering the business type and owner name.

3. **Message Sending**: The bot logs into your social media accounts and sends DMs to the collected leads, with human-like typing patterns to avoid detection.

4. **Response Tracking**: All sent messages are tracked, and the bot checks for responses.

5. **Follow-up Messages**: If a lead doesn't respond within the configured time (default: 24 hours), the bot sends a follow-up message.

6. **Warm Lead Handoff**: When a lead shows interest (responds positively), they're marked as a warm lead for you to follow up personally.

## Components

- `main.py` - Main entry point for the application
- `scraper.py` - Lead collection from different sources
- `message_generator.py` - GPT-powered message generation
- `dm_sender.py` - Automated message sending
- `lead_tracker.py` - Lead and response tracking
- `utils.py` - Helper functions and utilities
- `analytics.py` - Performance analytics and reporting
- `optimizer.py` - Message template optimization
- `dashboard.py` - Web-based monitoring dashboard
- `config.json` - Configuration for the bot

## Analytics and Optimization

The bot includes powerful analytics and optimization features:

1. **Performance Tracking**: The bot tracks key metrics like response rates, conversion rates, and engagement patterns.

2. **Template Optimization**: The optimizer analyzes message performance and generates improved variants using techniques like:
   - Adding social proof
   - Improving conciseness
   - Adding strategic questions
   - Adding urgency elements
   - Optimizing for better engagement

3. **Dashboard Monitoring**: The web dashboard provides real-time insights into:
   - Messages sent and responses received
   - Response rates over time
   - Best performing templates
   - Platform restriction warnings
   - Optimization recommendations

4. **Scheduled Analytics**: The bot automatically generates reports and optimizes templates on a schedule.

## Tips for Success

1. **Personalize Your Templates**: Edit the message templates in `message_generator.py` to match your tone and offerings.

2. **Start Small**: Begin with a small batch of DMs (10-15) to test and refine your approach.

3. **Target Specific Niches**: Focus on specific business types that you have experience with.

4. **Monitor Regularly**: Check the bot's output and lead spreadsheet to see what's working.

5. **Follow Platform Rules**: Be aware that excessive automation may violate platform terms of service. Use responsibly.

## Troubleshooting

- **Login Issues**: If the bot can't log in, check your credentials and ensure you don't have 2FA enabled on your accounts.
- **Scraping Problems**: Instagram and other platforms frequently change their HTML structure. You may need to update the selectors in `scraper.py`.
- **Rate Limiting**: If you get blocked temporarily, reduce your daily message limits in `config.json`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is meant for legitimate business outreach. Please use responsibly and in accordance with the terms of service of each platform. The authors are not responsible for any misuse or violations. 