# LiTree Avatar Assistant - API Guide

Complete reference for all API endpoints and WebSocket events.

## Base URL
```
http://localhost:5000
```

## REST API Endpoints

### Status & Info

#### GET `/api/status`
Get server status and capabilities.

**Response:**
```json
{
  "status": "online",
  "service": "LiTree Avatar Assistant Server",
  "version": "2.0.0",
  "ai_enabled": true,
  "websocket": true,
  "features": ["chat", "tts", "asset_upload", "persistent_history"],
  "timestamp": "2026-03-15T15:46:17.155832"
}
```

### Chat

#### POST `/api/chat`
Send a chat message and get a response.

**Request:**
```json
{
  "message": "Hello! How are you?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "Hey there! I'm doing great, thanks for asking! How can I help you today?",
  "mood": "happy",
  "session_id": "session_abc123",
  "timestamp": "2026-03-15T15:46:17.155832"
}
```

### Conversation History

#### GET `/api/history/{session_id}`
Get conversation history for a session.

**Response:**
```json
{
  "session_id": "session_abc123",
  "messages": [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

#### POST `/api/clear`
Clear conversation history.

**Request:**
```json
{
  "session_id": "session_abc123"
}
```

**Response:**
```json
{
  "status": "cleared",
  "session_id": "session_abc123"
}
```

### Avatar Styles

#### GET `/api/styles`
Get available avatar styles and moods.

**Response:**
```json
{
  "styles": ["pixar", "cyberpunk", "steampunk", "anime"],
  "moods": ["happy", "thinking", "surprised", "talking"]
}
```

### Asset Management

#### GET `/api/assets`
List all uploaded assets.

**Response:**
```json
{
  "assets": [
    {
      "filename": "avatar_pixar_happy.png",
      "type": "avatar",
      "style": "pixar",
      "mood": "happy",
      "url": "/assets/avatars/avatar_pixar_happy.png"
    }
  ]
}
```

#### GET `/api/assets/avatars/detect`
Auto-detect which avatar images are available.

**Response:**
```json
{
  "detected": {
    "pixar": {
      "happy": true,
      "thinking": false,
      "surprised": false,
      "talking": false
    },
    "cyberpunk": {...},
    "steampunk": {...},
    "anime": {...}
  }
}
```

#### POST `/api/upload`
Upload a new asset (avatar image or video).

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `file`: The file to upload
  - `type`: `"avatar"`, `"video"`, or `"audio"`
  - `style`: (optional) Avatar style name
  - `mood`: (optional) Avatar mood name

**Response:**
```json
{
  "success": true,
  "filename": "avatar_pixar_happy.png",
  "type": "avatar",
  "style": "pixar",
  "mood": "happy",
  "url": "/assets/avatars/avatar_pixar_happy.png"
}
```

### Static Assets

#### GET `/assets/{avatars|videos|audio}/{filename}`
Serve static asset files.

Example: `/assets/avatars/avatar_pixar_happy.png`

## WebSocket Events

### Connection

**Connect:**
```javascript
const socket = io('http://localhost:5000');
```

**On Connect:**
```javascript
socket.on('connect', () => {
  console.log('Connected to server');
});
```

### Events (Client → Server)

#### `chat_message`
Send a chat message.

```javascript
socket.emit('chat_message', {
  session_id: 'session_abc123',
  message: 'Hello!'
});
```

#### `set_mood`
Set the avatar mood.

```javascript
socket.emit('set_mood', {
  mood: 'happy'  // 'happy', 'thinking', 'surprised', 'talking'
});
```

### Events (Server → Client)

#### `connected`
Sent when client successfully connects.

```javascript
socket.on('connected', (data) => {
  console.log(data.message);  // "Connected to LiTree Avatar Assistant"
  console.log(data.sid);      // Session ID
});
```

#### `typing`
Sent when the assistant is processing a response.

```javascript
socket.on('typing', (data) => {
  // Show typing indicator
});
```

#### `assistant_response`
Sent when the assistant generates a response.

```javascript
socket.on('assistant_response', (data) => {
  console.log(data.response);   // The text response
  console.log(data.mood);       // Suggested mood: 'happy', 'thinking', etc.
  console.log(data.session_id);
  console.log(data.timestamp);
});
```

#### `mood_changed`
Sent when mood is updated.

```javascript
socket.on('mood_changed', (data) => {
  console.log(data.mood);  // New mood
});
```

#### `error`
Sent when an error occurs.

```javascript
socket.on('error', (data) => {
  console.error(data.message);
});
```

## Example Usage

### JavaScript (Browser)

```javascript
// Connect to WebSocket
const socket = io('http://localhost:5000');

// Listen for responses
socket.on('assistant_response', (data) => {
  console.log('LiTree:', data.response);
  updateAvatarMood(data.mood);
});

// Send message
function sendMessage(text) {
  socket.emit('chat_message', {
    session_id: 'my-session',
    message: text
  });
}

// REST API fallback
async function sendMessageREST(text) {
  const response = await fetch('http://localhost:5000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: 'my-session',
      message: text
    })
  });
  return await response.json();
}

// Upload avatar
async function uploadAvatar(file) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', 'avatar');
  formData.append('style', 'pixar');
  formData.append('mood', 'happy');
  
  const response = await fetch('http://localhost:5000/api/upload', {
    method: 'POST',
    body: formData
  });
  return await response.json();
}
```

### Python

```python
import requests
import websocket
import json

# REST API
response = requests.post('http://localhost:5000/api/chat', json={
    'session_id': 'my-session',
    'message': 'Hello!'
})
print(response.json())

# WebSocket
ws = websocket.WebSocket()
ws.connect('ws://localhost:5000/socket.io/?EIO=4&transport=websocket')

# Send message
ws.send(json.dumps({
    'type': 'chat_message',
    'data': {
        'session_id': 'my-session',
        'message': 'Hello!'
    }
}))
```

### cURL

```bash
# Chat
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello!","session_id":"test"}'

# Upload file
curl -X POST http://localhost:5000/api/upload \
  -F "file=@avatar.png" \
  -F "type=avatar" \
  -F "style=pixar" \
  -F "mood=happy"

# Get history
curl http://localhost:5000/api/history/test

# Clear history
curl -X POST http://localhost:5000/api/clear \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test"}'
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK` - Success
- `400 Bad Request` - Missing or invalid parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error responses:
```json
{
  "error": "Description of what went wrong"
}
```

## Rate Limiting

Currently no rate limiting is implemented. For production use, consider adding:
- Request throttling
- Session-based limits
- API key authentication
