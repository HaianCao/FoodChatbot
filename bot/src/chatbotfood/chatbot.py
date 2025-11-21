"""
This module contains the main Chatbot class.
"""
from dotenv import load_dotenv
import os

from .gemini_client import GeminiClient
from .chroma_manager import db_manager


class Chatbot:
    """The main class for the chatbot application."""

    def __init__(self):
        """Initializes the Chatbot, loading API keys and clients."""
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
        """Initialize the recipes collection if it's empty."""
        collection = self.db_manager.get_or_create_collection("recipes")
        if collection.count() == 0:
            print("INFO: Recipes collection is empty. Adding recipes to ChromaDB...")
            added = self.db_manager.add_recipes_to_collection("recipes")
            print(f"SUCCESS: Added {added} recipes to ChromaDB collection.")
        else:
            print(f"INFO: Recipes collection already contains {collection.count()} recipes.")

    def get_response(self, user_query: str) -> str:
        """
        Gets a response from the chatbot for a given user query.

        Args:
            user_query (str): The user's input.

        Returns:
            str: The chatbot's response.
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

        # Generate the final response using chat session
        response = self.gemini_client.generate_with_conversation_and_rag(
            user_query=translated_query,
            rag_context=rag_context
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
        """Reset the conversation to start fresh."""
        self.gemini_client.reset_chat_session()
        self.conversation_buffer = []
        print("💬 Conversation reset")
    
    def start_chat(self):
        """Starts an interactive chat session in the console."""
        print("Chatbot initialized. Type 'quit' to exit.")
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'quit':
                print("Exiting chat.")
                break
            self.get_response(user_input)
            
def main():
    chatbot = Chatbot()
    chatbot.start_chat()


if __name__ == "__main__":
    main()