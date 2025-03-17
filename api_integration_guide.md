# LeadGen Bot API Integration Guide

This guide explains how to integrate the LeadGen Bot API into your website or application.

## API Overview

The LeadGen Bot API provides a simple interface for integrating AI-powered chat functionality into your website or application. The API supports both basic chatbot functionality and more advanced lead tracking capabilities.

### Base URL

```
https://your-render-url.onrender.com
```

Replace `your-render-url.onrender.com` with your actual Render deployment URL.

## Authentication

All API requests require an API key for authentication. The API key should be included in the HTTP header of each request:

```
X-API-Key: your-api-key
```

## API Endpoints

### Health Check

Check if the API is online and functioning.

**Endpoint:** `GET /api/health`

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2023-03-17T12:34:56.789Z"
}
```

### Chat Endpoint

Send a message to the chatbot and receive a response.

**Endpoint:** `POST /api/chat`

**Request Body:**
```json
{
  "message": "I need a website for my business",
  "user_id": "optional-user-identifier"
}
```

**Response Example:**
```json
{
  "message": "I'd be happy to help you with a website for your business! Could you tell me more about what type of business you have and what features you'd need on your website?",
  "timestamp": "2023-03-17T12:34:56.789Z"
}
```

## Integration Options

### 1. Website Chat Widget

The simplest way to integrate the LeadGen Bot is using our pre-built chat widget. To add it to your website:

1. Download the [website_chat_example.html](website_chat_example.html) file
2. Open it in a text editor
3. Replace `'https://your-render-url.onrender.com/api/chat'` with your actual API endpoint
4. Replace `'your-api-key-here'` with your actual API key
5. Copy the HTML, CSS, and JavaScript code into your website

You can customize the appearance by modifying the CSS styles.

### 2. Direct API Integration

For more custom integrations, you can call the API directly from your application:

#### JavaScript Example

```javascript
async function sendChatMessage(message, userId) {
  try {
    const response = await fetch('https://your-render-url.onrender.com/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'your-api-key-here'
      },
      body: JSON.stringify({
        message: message,
        user_id: userId
      })
    });
    
    if (!response.ok) {
      throw new Error('API request failed');
    }
    
    const data = await response.json();
    return data.message;
  } catch (error) {
    console.error('Error:', error);
    return "Sorry, I'm having trouble connecting right now.";
  }
}
```

#### Python Example

```python
import requests

def send_chat_message(message, user_id):
    url = "https://your-render-url.onrender.com/api/chat"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "your-api-key-here"
    }
    payload = {
        "message": message,
        "user_id": user_id
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception for 4XX/5XX status codes
        
        data = response.json()
        return data["message"]
    except Exception as e:
        print(f"Error sending chat message: {e}")
        return "Sorry, I'm having trouble connecting right now."
```

### 3. Mobile App Integration

For mobile applications, you can use the same API endpoints:

#### Swift Example (iOS)

```swift
func sendChatMessage(message: String, userId: String, completion: @escaping (String?, Error?) -> Void) {
    guard let url = URL(string: "https://your-render-url.onrender.com/api/chat") else {
        completion(nil, NSError(domain: "Invalid URL", code: 0, userInfo: nil))
        return
    }
    
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.addValue("application/json", forHTTPHeaderField: "Content-Type")
    request.addValue("your-api-key-here", forHTTPHeaderField: "X-API-Key")
    
    let body: [String: Any] = [
        "message": message,
        "user_id": userId
    ]
    
    do {
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
    } catch {
        completion(nil, error)
        return
    }
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            completion(nil, error)
            return
        }
        
        guard let data = data else {
            completion(nil, NSError(domain: "No data received", code: 0, userInfo: nil))
            return
        }
        
        do {
            if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
               let message = json["message"] as? String {
                completion(message, nil)
            } else {
                completion(nil, NSError(domain: "Invalid response format", code: 0, userInfo: nil))
            }
        } catch {
            completion(nil, error)
        }
    }.resume()
}
```

#### Kotlin Example (Android)

```kotlin
suspend fun sendChatMessage(message: String, userId: String): String {
    return withContext(Dispatchers.IO) {
        try {
            val url = URL("https://your-render-url.onrender.com/api/chat")
            val connection = url.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.setRequestProperty("Content-Type", "application/json")
            connection.setRequestProperty("X-API-Key", "your-api-key-here")
            connection.doOutput = true
            
            val jsonBody = """
                {
                    "message": "$message",
                    "user_id": "$userId"
                }
            """.trimIndent()
            
            connection.outputStream.use { os ->
                val input = jsonBody.toByteArray(Charsets.UTF_8)
                os.write(input, 0, input.size)
            }
            
            if (connection.responseCode == HttpURLConnection.HTTP_OK) {
                connection.inputStream.bufferedReader().use { reader ->
                    val response = StringBuilder()
                    var line: String?
                    while (reader.readLine().also { line = it } != null) {
                        response.append(line)
                    }
                    
                    val jsonObject = JSONObject(response.toString())
                    return@withContext jsonObject.getString("message")
                }
            } else {
                return@withContext "Sorry, I'm having trouble connecting right now."
            }
        } catch (e: Exception) {
            return@withContext "Sorry, I'm having trouble connecting right now."
        }
    }
}
```

## Testing Your Integration

After setting up the integration, you should test it with various types of queries to ensure it's working correctly:

1. Send a greeting message to verify the connection
2. Ask about website services to test the bot's knowledge
3. Ask about pricing to see detailed responses
4. Test error handling by temporarily using an incorrect API key

## Best Practices

1. **Error Handling**: Always implement proper error handling to gracefully manage connection issues or API errors
2. **User Experience**: Include visual feedback like typing indicators while waiting for the bot's response
3. **Persistent Conversations**: Store the user_id to maintain conversation context across sessions
4. **Responsive Design**: Ensure your chat interface works well on both desktop and mobile devices
5. **Analytics**: Consider adding analytics to track user interactions and improve the chatbot over time

## Support

If you encounter any issues or have questions about the API integration, please contact our support team at support@example.com. 