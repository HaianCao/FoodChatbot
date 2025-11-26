"""Main entry point for the Food Chatbot application.

This module serves as the primary entry point for starting the web server
and launching the food and nutrition chatbot application.

Usage:
    python main.py
    
The application will start a Flask web server accessible at:
    http://localhost:5000

Author: FoodChatbot Team
Version: 1.0.0
"""
from src.web.server import run_server

def main():
    """Main function to start the chatbot web application.
    
    Initializes and starts the Flask web server that provides
    the chat interface for the food and nutrition assistant.
    
    Example:
        >>> python main.py
        # Starts web server at http://localhost:5000
    """
    run_server()


if __name__ == "__main__":
    main()