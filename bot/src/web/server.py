import os
import flask
from flask import send_from_directory, request, jsonify
from src.chatbotfood.chatbot import Chatbot

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_HOME_DIR = os.path.join(BASE_DIR, 'backend', 'static', 'home')

# Set template and static folders
app = flask.Flask(__name__, 
                  static_folder='static',
                  static_url_path='/static')
app.secret_key = 'your_secret_key'  # Replace with a secure key in production
chatbot = Chatbot()

@app.route('/')
def home():
    """Serve the main chat interface"""
    return send_from_directory(STATIC_HOME_DIR, 'index.html')

@app.route('/home/<path:filename>')
def serve_home_assets(filename):
    """Serve CSS and JS files"""
    return send_from_directory(STATIC_HOME_DIR, filename)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
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
    """Reset the chat conversation"""
    try:
        chatbot.reset_conversation()
        return jsonify({'message': 'Conversation reset successfully'})
    except Exception as e:
        print(f"Error in reset endpoint: {e}")
        return jsonify({'error': str(e)}), 500

def run_server():
    """
    Runs the Flask server for the chatbot application.
    """
    print("🚀 Starting Food Chatbot Server...")
    print("📍 Visit: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)