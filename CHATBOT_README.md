# AI-Powered Website Sales Chatbot

This extension to the LeadGen Bot adds an intelligent, conversational AI chatbot that can engage with leads across multiple platforms (Instagram, Twitter, LinkedIn, Facebook, and your website), qualify prospects, and guide them through the website purchasing process.

## Features

- 🤖 **AI-powered conversations** using OpenAI's GPT models for natural interactions
- 🌐 **Multi-platform support** for engaging with leads wherever they are
- 💬 **Automated lead qualification** through intelligent questioning
- 💰 **Dynamic payment link generation** via Stripe integration
- 📊 **Lead data capture** in Google Sheets for tracking and analytics
- ⏰ **Automated follow-ups** for leads who don't respond within 24 hours
- 🔄 **Synchronization** between website chat and social media DMs
- 🔌 **API integration** with your website via FastAPI

## Setup Instructions

### 1. Install Dependencies

Make sure you have all required packages installed:

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Update your `.env` file with the required credentials:

```
# OpenAI API Key (required for chatbot)
OPENAI_API_KEY=your_openai_api_key

# Stripe API Configuration (for payment processing)
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# API Configuration
API_KEY=your_api_key_for_securing_endpoints

# Email Notification Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=your_email@gmail.com
```

### 3. Configure Stripe (Optional)

To enable payment link generation:

1. Create a Stripe account if you don't have one
2. Set up your products in the Stripe dashboard
3. Add your Stripe API keys to the `.env` file
4. Update the `generate_stripe_payment_link` method in `chatbot.py` with your specific product links

### 4. Google Sheets Integration

The chatbot leverages the existing Google Sheets integration. Make sure your Google Sheets is properly configured with the service account email.

## Usage

### Running the Chatbot API Server

To start the API server for the website integration:

```bash
python main.py --action api
```

This will start the FastAPI server on http://0.0.0.0:8000.

### Running the Chatbot with Message Checking

To start both the API server and social media message checking:

```bash
python main.py --action chatbot --platform instagram
```

To check messages on all platforms:

```bash
python main.py --action chatbot --platform all
```

### Testing the Chatbot

Run the test script to simulate a conversation with the chatbot:

```bash
python test_chatbot.py
```

### Scheduling Follow-ups

To manually trigger follow-ups for inactive conversations:

```bash
python main.py --action follow_up
```

Or you can set up a scheduled task to run this command daily.

## Website Integration

To integrate the chatbot with your website:

1. Start the API server (see above)
2. Add the chat widget to your website by adapting the `website_chat_example.html` file
3. Update the API endpoint and API key in your website code

Example fetch call to the API:

```javascript
fetch('http://your-api-url/api/chatbot', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key'
    },
    body: JSON.stringify({
        lead_id: visitorId,
        platform: 'website',
        message: userMessage
    })
}).then(res => res.json())
  .then(response => {
      // Handle response here
  });
```

## API Endpoints

The chatbot API provides the following endpoints:

- `POST /api/chatbot` - Process a message and get a response
- `POST /api/webhook/stripe` - Handle Stripe payment webhooks
- `GET /api/health` - Health check endpoint
- `POST /api/follow-up` - Trigger follow-up process for inactive conversations

## Customization

### Modifying System Prompt

To change how the chatbot behaves, edit the `system_prompt` in the `AIWebsiteChatbot` class in `chatbot.py`.

### Adding New Features

To add new features to the chatbot:

1. Extend the `process_message` method in `chatbot.py`
2. Add new action types to the `actions` array in the `ChatbotResponse`
3. Update the website integration to handle the new action types

## Deployment

For production deployment:

1. Set up a proper WSGI server for the FastAPI app (e.g., Gunicorn)
2. Deploy to a cloud provider like AWS, Google Cloud, or Render
3. Set up proper SSL for secure API communication
4. Update CORS settings in `api.py` to only allow your domains

## Troubleshooting

- Check `bot.log` for detailed logs about chatbot activity
- Ensure the OpenAI API key is valid and has sufficient credits
- Verify that your `.env` file contains all required credentials
- If you encounter issues with message checking, ensure your browser automation setup is correct

---

For more information, see the main `README.md` file for the LeadGen Bot. 