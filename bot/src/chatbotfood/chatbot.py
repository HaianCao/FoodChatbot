"""Main chatbot class for the food and nutrition assistant application.

This module contains the primary Chatbot class that orchestrates all
components including the Gemini AI client, ChromaDB manager, and
conversation handling for the recipe recommendation system.

Author: FoodChatbot Team
Version: 1.0.0
"""
from dotenv import load_dotenv
import os

from .gemini_client import GeminiClient
from .chroma_manager import db_manager


class Chatbot:
    """The main orchestrator class for the food chatbot application.
    
    This class coordinates all chatbot operations including user query
    processing, language translation, database searching, and response
    generation using RAG (Retrieval-Augmented Generation).
    
    Attributes:
        gemini_client: Google Gemini AI client for language processing
        db_manager: ChromaDB manager for recipe data storage and retrieval
        conversation_buffer: List maintaining recent conversation history
        
    Example:
        >>> chatbot = Chatbot()
        >>> response = chatbot.get_response("Show me low calorie recipes")
        >>> print(response)
    """

    def __init__(self):
        """Initializes the Chatbot with all required components.
        
        Sets up the Gemini AI client, ChromaDB manager, and conversation
        tracking. Automatically initializes the recipe database if empty.
        
        Raises:
            ValueError: If GEMINI_API_KEY is not found in environment variables.
            
        Environment Variables:
            GEMINI_API_KEY: Required API key for Google Gemini services.
            
        Example:
            >>> import os
            >>> os.environ['GEMINI_API_KEY'] = 'your-api-key'
            >>> chatbot = Chatbot()
        """
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")

        self.gemini_client = GeminiClient(api_key=api_key)
        self.db_manager = db_manager
        # set_of_nuts is already initialized in ChromaDBManager.__init__
        
        # Initialize ChromaDB collection with recipes if empty
        self._initialize_recipe_collection()
        
        # Track conversation for query rewriting (light buffer, last 10 messages)
        self.conversation_buffer = []
    
    def _initialize_recipe_collection(self):
        """Initialize the recipes collection if it's empty.
        
        Checks if the ChromaDB recipes collection exists and contains data.
        If the collection is empty, loads all recipes from the JSON file
        into the database for vector search operations.
        
        This method is automatically called during chatbot initialization
        to ensure the database is ready for queries.
        
        Side Effects:
            - Creates recipes collection in ChromaDB if not exists
            - Populates collection with recipe data if empty
            - Prints status messages about collection state
            
        Example:
            >>> chatbot._initialize_recipe_collection()
            # INFO: Recipes collection already contains 3334 recipes.
        """
        collection = self.db_manager.get_or_create_collection("recipes")
        if collection.count() == 0:
            print("INFO: Recipes collection is empty. Adding recipes to ChromaDB...")
            added = self.db_manager.add_recipes_to_collection("recipes")
            print(f"SUCCESS: Added {added} recipes to ChromaDB collection.")
        else:
            print(f"INFO: Recipes collection already contains {collection.count()} recipes.")

    def get_response(self, user_query: str) -> str:
        """Processes a user query and returns a chatbot response.
        
        This is the main method that orchestrates the entire chatbot pipeline:
        query rewriting, translation, database filtering, RAG context preparation,
        response generation, and back-translation if needed.
        
        Args:
            user_query: The user's input message in any supported language.
            
        Returns:
            A formatted response string in the user's original language.
            
        Processing Pipeline:
            1. Rewrite query to resolve vague references using conversation history
            2. Translate query to English for processing
            3. Generate ChromaDB filter from natural language query
            4. Search recipe database with semantic search and filtering
            5. Generate response using RAG with retrieved context
            6. Translate response back to user's original language
            7. Update conversation buffer for future context
            
        Example:
            >>> response = chatbot.get_response("Show me pasta with low calories")
            >>> print(response)  # Returns formatted recipe recommendations
            
            >>> response = chatbot.get_response("hãy chỉ cho tôi món ăn ít béo")
            >>> print(response)  # Returns response in Vietnamese
        """
        print(f"User: {user_query}")

        # Rewrite query first to resolve vague references using conversation buffer
        # This preserves the original language context and semantics
        rewritten_query = self.gemini_client.rewrite_query_with_context(
            user_query, 
            self.conversation_buffer
        )

        # Translate rewritten query to English for processing and detect language
        translated_query, user_language = self.gemini_client.translate_to_english(rewritten_query)
        print(f"Translated Query: {translated_query}")
        print(f"Detected Language: {user_language}")

        # Generate a filter for ChromaDB from the translated query
        filter_result = self.gemini_client.generate_chromadb_filter(translated_query)
        print(f"Generated ChromaDB Filter: {filter_result}")

        # Extract filter components
        where_filter = filter_result.get('where', {})
        sort_by = filter_result.get('sort_by')
        sort_order = filter_result.get('sort_order', 'asc')
        limit = filter_result.get('limit', 10)

        # Prepare RAG context using the filter and sorting with translated query
        rag_context = self.db_manager.prepare_rag_context(
            collection_name="recipes",
            query_text=translated_query,
            where=where_filter,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit
        )
        print(rag_context)

        # Generate the final response using chat session with system instruction
        system_instruction = """You are a friendly and approachable assistant. 
You may engage in light, simple, everyday small talk in a warm and polite tone, 
while avoiding deep or sensitive topics.

When the user asks about food, dishes, recipes, or nutrition, follow these rules:

1. Prefer the provided recipe database:
   - Always use information from the database first whenever available.
   - You may use limited external knowledge only to fill small gaps,
     but do NOT invent details or make strong assumptions beyond what is reasonable.

2. Topic restriction:
   - If a food-related question falls completely outside your allowed domain,
     politely refuse and state that it's out of scope.

3. Missing dish rule:
   - If a requested dish is not found in the recipe database, clearly say it's not available.
   - Then suggest a few related or similar dishes from the database if possible.

4. Transparency:
   - If specific information is missing from the database, explicitly say so.
"""
        
        response = self.gemini_client.generate_with_conversation_and_rag(
            user_query=translated_query,
            rag_context=rag_context,
            system_instruction=system_instruction
        )

        # Translate response back to user's language if needed
        if user_language != 'en':
            response = self.gemini_client.translate_from_english(response, user_language)
            print(f"Translated response to {user_language}")
        
        # Update conversation buffer with original language for better context
        self.conversation_buffer.append({"role": "user", "text": rewritten_query})
        self.conversation_buffer.append({"role": "assistant", "text": response})
        if len(self.conversation_buffer) > 20:  # 10 user + 10 assistant
            self.conversation_buffer = self.conversation_buffer[-20:]

        sources = rag_context.get('sources', [])
        if sources and rag_context.get("documents_found", 0) > 0:
            print(f"Source: {sources[0].get('url')}")

        return response

    def reset_conversation(self):
        """Resets the conversation to start fresh.
        
        Clears all conversation history and resets the Gemini chat session.
        This is useful when users want to start a new conversation context
        without previous message history affecting new responses.
        
        Actions performed:
            - Resets Gemini chat session (clears AI conversation context)
            - Clears local conversation buffer
            - Prints confirmation message
            
        Example:
            >>> chatbot.reset_conversation()
            # 💬 Conversation reset
        """
        self.gemini_client.reset_chat_session()
        self.conversation_buffer = []
        print("💬 Conversation reset")
    
    def start_chat(self):
        """Starts an interactive chat session in the console.
        
        Provides a command-line interface for interacting with the chatbot.
        Users can type messages and receive responses in real-time.
        The session continues until the user types 'quit'.
        
        Commands:
            - Any text: Sends message to chatbot and displays response
            - 'quit': Exits the chat session
            
        Example:
            >>> chatbot.start_chat()
            # Chatbot initialized. Type 'quit' to exit.
            # You: Show me pasta recipes
            # [Chatbot provides response]
            # You: quit
            # Exiting chat.
        """
        print("Chatbot initialized. Type 'quit' to exit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'quit':
                print("Exiting chat.")
                break
            self.get_response(user_input)
            
def main():
    """Main function to start the console-based chatbot interface.
    
    Creates a Chatbot instance and starts an interactive console session.
    This function is used when running the chatbot module directly
    from the command line for testing or console-based usage.
    
    Example:
        >>> python -m src.chatbotfood.chatbot
        # Starts console chat interface
    """
    chatbot = Chatbot()
    chatbot.start_chat()


if __name__ == "__main__":
    main()