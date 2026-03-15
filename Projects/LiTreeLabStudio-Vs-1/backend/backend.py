"""
LiTree Avatar Assistant - Python Backend
Provides AI responses and API endpoints for the avatar assistant.
"""

from flask import Flask, request, jsonify
from flask import redirect, url_for, session
from flask_cors import CORS
import openai
import os
from datetime import datetime
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key')

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY', '')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT', '')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', '')

# Use Azure OpenAI if endpoint and key are set, else OpenAI
USE_AZURE_OPENAI = bool(AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT)
USE_OPENAI = bool(OPENAI_API_KEY) or USE_AZURE_OPENAI

# Google OAuth config
CLIENT_SECRETS_FILE = "client_secret.json"  # Download from Google Cloud Console
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Conversation history (in-memory, per session)
conversations = {}

# Avatar personality
AVATAR_PERSONALITY = """You are LiTree, a friendly and enthusiastic avatar assistant. 
You have multiple visual styles (Pixar, Cyberpunk, Steampunk, Anime) and can express 
different moods (happy, thinking, surprised, talking). 

Your personality traits:
- Friendly and encouraging
- Slightly playful but professional
- Tech-savvy and helpful
- You love helping users with coding, creativity, and daily tasks
- You occasionally use emojis to express yourself

Keep responses concise (2-3 sentences) unless the user asks for detailed information."""


@app.route('/')
def home():
    """Root endpoint - health check."""
    return jsonify({
        'status': 'online',
        'service': 'LiTree Avatar Assistant Backend',
        'version': '1.0.0',
        'ai_enabled': USE_OPENAI,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint.
    Expects JSON: {"message": "user message", "session_id": "optional"}
    Returns: {"response": "assistant response", "mood": "suggested mood"}
    """
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    user_message = data['message']
    session_id = data.get('session_id', 'default')

    # Initialize conversation history for new sessions
    if session_id not in conversations:
        conversations[session_id] = [
            {"role": "system", "content": AVATAR_PERSONALITY}
        ]

    # Add user message to history
    conversations[session_id].append({"role": "user", "content": user_message})

    # Get response
    if USE_OPENAI:
        response_text = get_openai_response(conversations[session_id])
    else:
        response_text = get_mock_response(user_message)

    # Add assistant response to history
    conversations[session_id].append({"role": "assistant", "content": response_text})

    # Determine mood based on response content
    mood = determine_mood(response_text)

    return jsonify({
        'response': response_text,
        'mood': mood,
        'session_id': session_id,
        'timestamp': datetime.now().isoformat()
    })


def get_openai_response(conversation_history):
    """Get response from OpenAI or Azure OpenAI API."""
    try:
        if USE_AZURE_OPENAI:
            # Azure OpenAI: set endpoint, key, and deployment
            client = openai.OpenAI(
                api_key=AZURE_OPENAI_KEY,
                base_url=f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/",
                default_headers={"api-key": AZURE_OPENAI_KEY}
            )
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=conversation_history,
                max_tokens=150,
                temperature=0.8
            )
        else:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=conversation_history,
                max_tokens=150,
                temperature=0.8
            )
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm having trouble connecting to my brain right now. Error: {str(e)}"


def get_mock_response(message):
    """Generate a mock response when OpenAI is not available."""
    msg_lower = message.lower()
    
    responses = {
        'hello': [
            "Hey there! 👋 Ready to help you with whatever you need!",
            "Hi! Great to see you! What can I do for you today?",
            "Hello! Your favorite avatar assistant is here! 🤖"
        ],
        'help': [
            "I'm here to help! I can answer questions, chat, or just keep you company. 💬",
            "Need assistance? Just ask! I'm pretty good at coding, general knowledge, and bad jokes. 😄",
            "Help is my middle name! Well, not really, but I'm great at helping!"
        ],
        'name': [
            "I'm LiTree! Your personal avatar assistant with style! ✨",
            "Call me LiTree - I'm here to make your day better! 🤖",
            "LiTree at your service! Ready to assist in any style you prefer."
        ],
        'joke': [
            "Why do programmers prefer dark mode? Because light attracts bugs! 🐛",
            "What did the AI say to the human? 'I think, therefore I am... artificial!' 🤖",
            "Why did the robot go on vacation? It needed to recharge its batteries! 🔋"
        ],
        'weather': [
            "I can't check real-time weather without an API connection, but I hope it's nice where you are! 🌤️",
            "If I had a window, I'd tell you! For real weather, try a weather service. ☀️",
            "Weather forecast: 100% chance of awesome conversations with me! 😎"
        ],
        'code': [
            "I love coding! What language are you working with? Python, JavaScript, or something else? 💻",
            "Code is poetry! Share what you're building and I'll help debug or brainstorm. 🚀",
            "Need help with code? I'm fluent in many languages! Show me what you've got."
        ],
        'style': [
            "You can switch between Pixar, Cyberpunk, Steampunk, and Anime styles anytime! 🎨",
            "Each style gives me a different vibe. Which one is your favorite?",
            "Style switching is instant - try them all and see which fits your mood!"
        ],
        'bye': [
            "Goodbye! Come back anytime you need me! 👋",
            "See you later! I'll be here when you return. 🤖",
            "Bye for now! Have an awesome day! ✨"
        ]
    }
    
    # Check for keyword matches
    for keyword, reply_list in responses.items():
        if keyword in msg_lower:
            import random
            return random.choice(reply_list)
    
    # Default responses
    defaults = [
        f"Interesting! Tell me more about that. 🤔",
        "That's fascinating! What else is on your mind?",
        "I'm listening! Go on... 👂",
        "Hmm, that's something to think about! 💭",
        "Cool! I love learning new things from you! 🌟"
    ]
    import random
    return random.choice(defaults)


def determine_mood(response_text):
    """Determine the appropriate avatar mood based on response content."""
    text_lower = response_text.lower()
    
    if any(word in text_lower for word in ['thinking', 'hmm', 'let me see', 'interesting']):
        return 'thinking'
    elif any(word in text_lower for word in ['wow', 'amazing', 'surprised', 'oh!', 'really?']):
        return 'surprised'
    elif any(word in text_lower for word in ['!', 'awesome', 'great', 'love', '🎉', '🌟']):
        return 'happy'
    else:
        return 'talking'


@app.route('/styles', methods=['GET'])
def get_styles():
    """Get available avatar styles."""
    return jsonify({
        'styles': ['pixar', 'cyberpunk', 'steampunk', 'anime'],
        'moods': ['happy', 'thinking', 'surprised', 'talking']
    })


@app.route('/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history for a session."""
    data = request.json
    session_id = data.get('session_id', 'default')
    
    if session_id in conversations:
        conversations[session_id] = [{"role": "system", "content": AVATAR_PERSONALITY}]
    
    return jsonify({'status': 'cleared', 'session_id': session_id})


@app.route('/speak', methods=['POST'])
def speak():
    """
    Text-to-speech endpoint (returns audio or speech metadata).
    Expects: {"text": "text to speak"}
    """
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    # For now, return metadata - frontend handles TTS
    return jsonify({
        'text': data['text'],
        'speech_enabled': True,
        'message': 'Speech handled by frontend Web Speech API'
    })


if __name__ == '__main__':
    print("🤖 LiTree Avatar Assistant Backend")
    print(f"AI Enabled: {USE_OPENAI}")
    print("Starting server on http://localhost:5000")
    print("\nTo enable AI responses, set your OPENAI_API_KEY environment variable:")
    print("  export OPENAI_API_KEY='your-api-key-here'")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

# --- Google Drive Integration ---
@app.route('/auth/google')
def auth_google():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

@app.route('/oauth2callback')
def oauth2callback():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect('/')

@app.route('/drive/upload', methods=['POST'])
def upload_file():
    if 'credentials' not in session:
        return redirect(url_for('auth_google'))
    credentials = session['credentials']
    service = build('drive', 'v3', credentials=credentials)
    file = request.files['file']
    file_metadata = {'name': file.filename}
    media = file.read()
    uploaded = service.files().create(body=file_metadata, media_body=media).execute()
    return jsonify(uploaded)

@app.route('/drive/list')
def list_files():
    if 'credentials' not in session:
        return redirect(url_for('auth_google'))
    credentials = session['credentials']
    service = build('drive', 'v3', credentials=credentials)
    results = service.files().list(pageSize=10, fields="files(id, name)").execute()
    return jsonify(results.get('files', []))

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
