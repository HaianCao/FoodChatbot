"""Flask web server for the food chatbot application.

This module provides a web interface for the food chatbot using Flask.
It serves static files, handles chat API endpoints, and manages user sessions.

Author: FoodChatbot Team
Version: 1.0.0

API Endpoints:
    GET /: Serves the main chat interface
    GET /home/<filename>: Serves CSS and JS assets
    POST /api/chat: Processes chat messages
    POST /api/reset: Resets conversation history
    
Example:
    >>> python server.py
    # Starts server at http://localhost:5000
"""
import os
import flask
from flask import send_from_directory, request, jsonify
from src.chatbotfood.chatbot import Chatbot

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_HOME_DIR = os.path.join(BASE_DIR, 'web', 'static', 'home')

# Set template and static folders
app = flask.Flask(__name__, 
                  static_folder=os.path.join('web', 'static'),
                  static_url_path='/static')
app.secret_key = 'your_secret_key'  # Replace with a secure key in production
chatbot = Chatbot()

@app.route('/')
def home():
    """Serves the main chat interface HTML page.
    
    Returns:
        The index.html file containing the chat interface.
    """
    return send_from_directory(STATIC_HOME_DIR, 'index.html')

@app.route('/home/<path:filename>')
def serve_home_assets(filename):
    """Serves static CSS and JavaScript files for the chat interface.
    
    Args:
        filename: The name of the static file to serve (CSS, JS, etc.)
        
    Returns:
        The requested static file from the home directory.
    """
    return send_from_directory(STATIC_HOME_DIR, filename)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handles chat messages from the web interface.
    
    Processes user messages through the chatbot and returns responses
    with optional source information.
    
    Request JSON:
        {
            "message": "user's chat message"
        }
        
    Response JSON:
        {
            "response": "chatbot's response",
            "sources": ["list of source URLs"]
        }
        
    Returns:
        JSON response with chatbot answer and sources, or error message.
        
    HTTP Status Codes:
        200: Success
        400: Bad request (missing message)
        500: Internal server error
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get response from chatbot
        response = chatbot.get_response(user_message)
        
        # Parse sources if available
        sources = []
        if '📚 Sources:' in response:
            parts = response.split('📚 Sources:')
            response_text = parts[0].strip()
            if len(parts) > 1:
                sources_text = parts[1].strip()
                sources = [s.strip() for s in sources_text.split('\n') if s.strip()]
            response = response_text
        
        return jsonify({
            'response': response,
            'sources': sources
        })
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    """Resets the chat conversation history.
    
    Clears the current chat session and conversation buffer,
    starting a fresh conversation context.
    
    Response JSON:
        {
            "message": "Conversation reset successfully"
        }
        
    Returns:
        JSON confirmation message or error.
        
    HTTP Status Codes:
        200: Success
        500: Internal server error
    """
    try:
        chatbot.reset_conversation()
        return jsonify({'message': 'Conversation reset successfully'})
    except Exception as e:
        print(f"Error in reset endpoint: {e}")
        return jsonify({'error': str(e)}), 500

def run_server():
    """Starts the Flask development server for the chatbot application.
    
    Launches the web server with debug mode enabled, accessible on
    all network interfaces at port 5000.
    
    Server Configuration:
        - Host: 0.0.0.0 (all interfaces)
        - Port: 5000
        - Debug: True (auto-reload on code changes)
        
    Example:
        >>> run_server()
        # Server starts at http://localhost:5000
        # or http://your-ip:5000 for network access
    """
    print("🚀 Starting Food Chatbot Server...")
    print("📍 Visit: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)