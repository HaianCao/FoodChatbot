"""Google Gemini AI client for recipe chatbot with RAG capabilities.

This module provides the GeminiClient class for interacting with Google's
Gemini AI API, including translation services, query processing, filter
generation, and RAG-based response generation.

Author: FoodChatbot Team
Version: 1.0.0
"""

import json
from typing import Optional, Dict, Any, List

import google.genai as genai
from google.genai import types

from . import schemas
from . import prompts
db_manager = None  # Will be assigned the singleton instance of ChromaDBManager
from .chroma_manager import db_manager

class GeminiClient:

    def extract_user_preferences(self, user_query: str, conversation_history: list = None) -> dict:
        """Extract user preferences/goals from query and conversation context using Gemini.
        Uses a prompt to instruct Gemini to return a structured JSON object summarizing
        dietary goals, preferred/avoided ingredients, cuisine types, nutrition targets, etc.
        Args:
            user_query: The user's current query (any language).
            conversation_history: List of recent message dicts (role/text), can be empty.
        Returns:
            Dictionary with keys: dietary_goals, preferred_ingredients, avoided_ingredients,
            cuisine_types, nutrition_targets, other. All values are lists.
        """
        # Build conversation context as text
        context_text = "\n".join([
            f"User: {msg['text']}" if msg['role'] == 'user' else f"Assistant: {msg['text']}"
            for msg in (conversation_history or [])
        ])
        prompt = prompts.get_preference_extraction_prompt(user_query, context_text)
        try:
            response = self.client.models.generate_content(
                model=self.DEFAULT_MODEL,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)]
                    )
                ]
            )
            # Remove markdown code block if present
            raw = response.text.strip()
            if raw.startswith('```json'):
                raw = raw[7:]
            if raw.startswith('```'):
                raw = raw[3:]
            if raw.endswith('```'):
                raw = raw[:-3]
            prefs = json.loads(raw)
            # Ensure all expected keys exist and are lists
            keys = ["dietary_goals", "preferred_ingredients", "avoided_ingredients", "cuisine_types", "nutrition_targets", "other"]
            for k in keys:
                if k not in prefs or not isinstance(prefs[k], list):
                    prefs[k] = []
            return prefs
        except Exception as e:
            print(f"⚠️  Preference extraction failed: {e}. Returning empty preferences.")
            return {k: [] for k in ["dietary_goals", "preferred_ingredients", "avoided_ingredients", "cuisine_types", "nutrition_targets", "other"]}
    """Client for interacting with Google's Gemini API with RAG capabilities.
    
    This class handles all interactions with Google's Gemini AI models,
    including translation, query processing, filter generation, and
    conversation management for the recipe chatbot.
    
    Attributes:
        DEFAULT_MODEL: Default Gemini model identifier
        ADVANCED_MODEL: Advanced Gemini model for complex tasks
        config: Gemini generation configuration
        client: Google GenAI client instance
        chat_session: Current chat session for conversation context
        
    Example:
        >>> client = GeminiClient(api_key="your-api-key")
        >>> client.start_chat_session()
        >>> response = client.generate_with_conversation_and_rag(
        ...     user_query="Show me pasta recipes",
        ...     rag_context={"context": "Recipe data...", "sources": []}
        ... )
    """
    
    DEFAULT_MODEL = "gemini-2.5-flash-lite"
    ADVANCED_MODEL = "gemini-2.5-flash-lite"
    
    def __init__(self, api_key: str, system_instruction: str = ""):
        """Initialize the Gemini client with API credentials and configuration.
        
        Sets up the Google GenAI client with authentication and default
        generation configuration. The client is ready for immediate use
        with translation, filter generation, and chat operations.
        
        Args:
            api_key: Google AI API key for authentication. Must be a valid
                API key with access to Gemini models.
            system_instruction: Optional system-level instructions that will
                be applied to model responses. Used for setting behavioral
                guidelines and response constraints.
                
        Example:
            >>> client = GeminiClient(
            ...     api_key="AIza...",
            ...     system_instruction="Always respond in Vietnamese"
            ... )
        """
        self.config = types.GenerateContentConfig(
            system_instruction=system_instruction,
        )
        self.client = genai.Client(api_key=api_key)
        self.chat_session = None  # Will be created when starting chat

    def start_chat_session(self, model: Optional[str] = None, system_instruction: str = ""):
        """Start a new chat session with Gemini for conversation context.
        
        Creates a stateful chat session that maintains conversation history
        across multiple message exchanges. This enables the model to reference
        previous messages and provide contextually aware responses.
        
        Args:
            model: The Gemini model identifier to use for the chat session.
                Defaults to DEFAULT_MODEL if not specified.
                Available models: 'gemini-2.5-flash-lite'
            system_instruction: System instructions that define the chat
                session's behavior and response style. Overrides any
                instructions set during client initialization.
                
        Note:
            Starting a new session will replace any existing chat session.
            Previous conversation history will be lost.
            
        Example:
            >>> client.start_chat_session(
            ...     system_instruction="You are a helpful cooking assistant"
            ... )
        """
        model = model or self.DEFAULT_MODEL
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
        )
        self.chat_session = self.client.chats.create(
            model=model,
            config=config
        )
        print(f"✅ Started new chat session with model: {model}")
    
    def translate_to_english(self, text: str, model: Optional[str] = None) -> tuple[str, str]:
        """Translate non-English text to English with language detection.
        
        Uses Gemini to automatically detect the input language and translate
        to English while preserving numbers, measurements, and units exactly.
        Handles multiple languages including Vietnamese, Spanish, French, etc.
        
        Translation features:
            - Automatic language detection
            - Measurement and unit preservation
            - Graceful error handling with fallback to original text
            - Support for cooking-related terminology
            
        Args:
            text: The text to translate. Can be in any supported language.
                Empty strings are returned unchanged.
            model: The Gemini model to use for translation.
                Defaults to DEFAULT_MODEL if not specified.
                
        Returns:
            A tuple containing:
                - translated_text: English translation of the input
                - detected_language: Language code (e.g., 'vi', 'es', 'fr')
                  or 'en' if already English, 'unknown' if detection fails
                  
        Example:
            >>> text, lang = client.translate_to_english("món ăn ít calo")
            >>> print(f"{text} (from {lang})")
            'low calorie food (from vi)'
        """
        if not text:
            return text, 'en'
        
        model = model or self.DEFAULT_MODEL
        translation_prompt = prompts.get_translation_prompt(text)
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=translation_prompt)]
            )
        ]
        
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=contents
            )
            # Parse response to extract language and translation
            response_text = response.text.strip()
            
            # Expected format: "Language: <code>\nTranslation: <text>"
            if "Language:" in response_text and "Translation:" in response_text:
                lines = response_text.split('\n')
                language = lines[0].replace('Language:', '').strip().lower()
                translation = '\n'.join(lines[1:]).replace('Translation:', '').strip()
                return translation, language
            else:
                # Fallback: assume it's just the translation
                return response_text, 'unknown'
        except Exception as e:
            print(f"⚠️  Translation failed: {e}. Using original text.")
            return text, 'en'
    
    def translate_from_english(self, text: str, target_language: str, model: Optional[str] = None) -> str:
        """Translate English text to specified target language.
        
        Performs back-translation from English to the user's preferred language
        while maintaining technical terms, measurements, and cooking terminology.
        Used for translating bot responses back to the user's original language.
        
        Args:
            text: The English text to translate. Should be clear, natural English.
            target_language: Target language code for translation.
                Supported: 'vi' (Vietnamese), 'es' (Spanish), 'fr' (French),
                'de' (German), 'zh' (Chinese), 'ja' (Japanese), 'ko' (Korean), etc.
            model: The Gemini model to use for translation.
                Defaults to DEFAULT_MODEL if not specified.
                
        Returns:
            Translated text in the target language. Returns original English
            text if target_language is 'en' or 'unknown', or if translation fails.
            
        Example:
            >>> vietnamese = client.translate_from_english(
            ...     "Here are 5 low calorie recipes", "vi"
            ... )
            >>> print(vietnamese)
            'Đây là 5 công thức nấu ăn ít calo'
        """
        if target_language == 'en' or target_language == 'unknown':
            return text
        
        model = model or self.DEFAULT_MODEL
        translation_prompt = prompts.get_back_translation_prompt(text, target_language)
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=translation_prompt)]
            )
        ]
        
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=contents
            )
            return response.text.strip()
        except Exception as e:
            print(f"⚠️  Back-translation failed: {e}. Using original English text.")
            return text
    
    def rewrite_query_with_context(self, user_query: str, conversation_history: list = None) -> str:
        """Rewrite vague queries using conversation context for better search.
        
        Analyzes user queries that contain vague references like "that", "it",
        "the second one" and replaces them with specific terms from recent
        conversation history. Essential for handling follow-up questions in
        conversational recipe search.
        
        Processing logic:
            1. Check if conversation history exists (return as-is for first message)
            2. Extract last 4 messages for context window
            3. Use Gemini to resolve vague references
            4. Log changes for debugging purposes
            5. Graceful fallback to original query on errors
            
        Args:
            user_query: The user's potentially vague query that may contain
                references to previous conversation elements.
                Examples: "tell me about that", "the second one", "món đó"
            conversation_history: List of recent message dictionaries with
                'role' and 'text' keys. Used to resolve ambiguous references.
                
        Returns:
            Clear, specific query ready for ChromaDB search. Returns original
            query if no rewriting is needed or if the process fails.
            
        Example:
            >>> history = [{"role": "user", "text": "pasta recipes"},
            ...            {"role": "assistant", "text": "Here are 5 pasta dishes"}]
            >>> rewritten = client.rewrite_query_with_context(
            ...     "tell me about the first one", history
            ... )
            >>> # Returns specific pasta dish name from context
        """
        # If no conversation history, return query as-is (first message)
        if not conversation_history or len(conversation_history) == 0:
            return user_query
        
        # Build context from recent conversation (last 4 messages)
        recent_context = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
        context_text = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['text'][:200]}"
            for msg in recent_context
        ])
        
        rewrite_prompt = prompts.get_query_rewrite_prompt(user_query, context_text)
        
        try:
            response = self.client.models.generate_content(
                model=self.DEFAULT_MODEL,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=rewrite_prompt)]
                    )
                ]
            )
            rewritten = response.text.strip()
            
            # Log only if query was actually changed
            if rewritten.lower() != user_query.lower():
                print(f"  🔄 Query rewrite: '{user_query}' → '{rewritten}'")
            
            return rewritten
        except Exception as e:
            print(f"⚠️  Query rewrite failed: {e}. Using original query.")
            return user_query
    
    def generate_chromadb_filter(self, user_query: str) -> Dict[str, Any]:
        """Generate structured ChromaDB filter from natural language query.
        
        Converts natural language recipe queries into ChromaDB-compatible
        filter conditions using Gemini's advanced reasoning capabilities.
        Handles nutrition constraints, cooking times, servings, and sorting.
        
        Filter capabilities:
            - Nutrition value ranges (calories, protein, fat, etc.)
            - Time constraints (prep time, cook time)
            - Serving size requirements
            - Qualitative sorting ("high protein", "low calorie")
            - Complex multi-condition queries
            
        Args:
            user_query: Natural language query describing recipe requirements.
                Examples: "low calorie pasta under 30 minutes",
                "high protein meals for 4 people", "desserts with less than 200 calories"
                
        Returns:
            Dictionary containing ChromaDB filter components:
                - 'where': Structured filter conditions for metadata
                - 'sort_by': Optional nutrition field for sorting
                - 'sort_order': 'asc' or 'desc' for sort direction
                - 'limit': Maximum results when sorting
            Returns empty dict if filter generation fails.
            
        Example:
            >>> filter_dict = client.generate_chromadb_filter(
            ...     "recipes under 500 calories with high protein"
            ... )
            >>> # Returns: {
            >>> #   'where': {'nutr_val_calories': {'$lte': 500}},
            >>> #   'sort_by': 'nutr_val_protein',
            >>> #   'sort_order': 'desc',
            >>> #   'limit': 10
            >>> # }
        """
        prompt = prompts.get_filter_generation_prompt(user_query, db_manager.set_of_nuts)
        print(f"🔍 Generating filter for query: {user_query}")
        
        try:
            response = self.client.models.generate_content(
                model=self.ADVANCED_MODEL,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schemas.Filter.model_json_schema(),
                )
            )
            filter_obj = json.loads(response.text)
            return self._build_chromadb_where_clause(filter_obj)
            
        except Exception as e:
            print(f"⚠️  Filter generation failed: {e}. No filter will be used.")
            return {}
    
    def _build_chromadb_where_clause(self, filter_obj: Dict[str, Any]) -> Dict[str, Any]:
        """Convert parsed filter object to ChromaDB query parameters.
        
        Transforms the structured filter object from Gemini into ChromaDB-compatible
        query parameters including where clauses, sorting, and result limits.
        Handles complex filter combinations and ensures proper data types.
        
        Processing steps:
            1. Extract sorting parameters (nutrition field, order, limit)
            2. Process time and serving filters with min/max operators
            3. Handle nutrition value ranges with unit adjustments
            4. Combine multiple conditions with $and operator
            5. Validate and set default values for missing parameters
            
        Args:
            filter_obj: Parsed filter dictionary from Gemini response containing:
                - sort_by_nutrition: Optional nutrition field name
                - sort_order: 'asc' or 'desc'
                - result_limit: Maximum number of results
                - *_min/*_max: Range filters for various fields
                - dict_nutrition_min/max: Nutrition value constraints
                
        Returns:
            Dictionary with ChromaDB query parameters:
                - 'where': Combined filter conditions
                - 'sort_by': Database field name for sorting
                - 'sort_order': Sort direction
                - 'limit': Result limit (defaults to 10)
                
        Example:
            >>> filter_obj = {
            ...     'sort_by_nutrition': 'Calories',
            ...     'sort_order': 'asc',
            ...     'result_limit': 5,
            ...     'prep_time_max': 30
            ... }
            >>> result = client._build_chromadb_where_clause(filter_obj)
            >>> # Returns properly formatted ChromaDB parameters
        """
        where_conditions = []
        sort_params = {}
        
        # Extract sorting parameters
        if filter_obj.get('sort_by_nutrition'):
            sort_params['sort_by'] = f"nutr_val_{filter_obj['sort_by_nutrition'].lower()}"
            sort_params['sort_order'] = filter_obj.get('sort_order', 'asc')
            # Ensure limit is always a valid number, never None
            limit_value = filter_obj.get('result_limit')
            sort_params['limit'] = limit_value if limit_value is not None else 10
        
        # Handle time and serving filters
        time_servings_filters = {}
        for field, value in filter_obj.items():
            if value is None or field.startswith('dict_nutrition_') or field in ['sort_by_nutrition', 'sort_order', 'result_limit']:
                continue

            if field.endswith('_min'):
                db_field = field.replace('_min', '')
                operator = '$gte'
            elif field.endswith('_max'):
                db_field = field.replace('_max', '')
                operator = '$lte'
            else:
                continue

            if db_field not in time_servings_filters:
                time_servings_filters[db_field] = {}
            time_servings_filters[db_field][operator] = value

        for field, conditions in time_servings_filters.items():
            where_conditions.append({field: conditions})

        # Handle nutrition filters
        if filter_obj.get('dict_nutrition_min'):
            for item in filter_obj['dict_nutrition_min']:
                db_field = f"nutr_val_{item['key'].lower()}"
                adjusted_value = item['value'] * item.get('multiply', 1)
                where_conditions.append({db_field: {'$gte': adjusted_value}})
        
        if filter_obj.get('dict_nutrition_max'):
            for item in filter_obj['dict_nutrition_max']:
                db_field = f"nutr_val_{item['key'].lower()}"
                adjusted_value = item['value'] * item.get('multiply', 1)
                where_conditions.append({db_field: {'$lte': adjusted_value}})

        # Combine conditions
        result = {}
        
        if where_conditions:
            result['where'] = (
                where_conditions[0] if len(where_conditions) == 1
                else {"$and": where_conditions}
            )
        
        # Add sorting parameters if present
        result.update(sort_params)
        
        if result.get('where'):
            print(f"  ✅ Generated ChromaDB filter: {result['where']}")
        if sort_params:
            print(f"  🔀 Sort by: {sort_params.get('sort_by')}, order: {sort_params.get('sort_order')}, limit: {sort_params.get('limit')}")
        
        return result

    def generate_with_conversation_and_rag(
        self,
        user_query: str,
        rag_context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        system_instruction: str = "",
        translate: bool = True
    ) -> str:
        """Generate response using chat session with RAG context integration.
        
        Combines Gemini's conversation capabilities with retrieved recipe
        information to provide contextually aware, database-grounded responses.
        Maintains chat history automatically through Gemini's native chat API.
        
        Key features:
            - Automatic chat session management
            - RAG context integration with conversation flow
            - Database-only response enforcement
            - Proper formatting for different response types
            - Conversation context preservation
            
        Args:
            user_query: The current user question or request.
                Can reference previous conversation elements.
            rag_context: Retrieved recipe information from ChromaDBManager containing:
                - 'context': Formatted recipe text for the model
                - 'sources': List of recipe metadata and URLs
                - 'documents_found': Number of matching recipes
            conversation_history: Not used in this implementation as
                chat session maintains history automatically.
            model: The Gemini model to use. Defaults to DEFAULT_MODEL.
            system_instruction: System instructions for new chat sessions.
                Only applied when creating a new session.
            translate: Whether to enable translation capabilities.
                Currently not implemented in this method.
                
        Returns:
            Generated response text that combines conversation context
            with retrieved recipe information, properly formatted
            according to the query type (list vs detailed recipe).
            
        Example:
            >>> rag_ctx = {
            ...     'context': 'Recipe: Pasta Salad\nIngredients: ...',
            ...     'sources': [{'url': 'https://...'}]
            ... }
            >>> response = client.generate_with_conversation_and_rag(
            ...     "How do I make the pasta salad?", rag_ctx
            ... )
            >>> # Returns detailed recipe with ingredients and instructions
        """
        # Create new chat session if not exists
        if self.chat_session is None:
            self.start_chat_session(model=model, system_instruction=system_instruction)
        
        context_text = rag_context.get('context', '')
        current_prompt = prompts.get_rag_with_history_prompt(user_query, context_text)
        
        # Send message through chat session
        response = self.chat_session.send_message(current_prompt)
        
        return response.text
    
    def reset_chat_session(self):
        """Reset the chat session to start fresh conversation.
        
        Clears the current chat session and conversation history.
        The next call to generate_with_conversation_and_rag will
        automatically create a new session.
        
        Use this method when:
            - User explicitly requests to start over
            - Conversation context becomes too long
            - Switching to a different topic or user
            - Error recovery scenarios
            
        Note:
            All previous conversation context will be permanently lost.
            Any ongoing conversation state should be saved before calling this method.
            
        Example:
            >>> client.reset_chat_session()
            >>> # Next message will start a completely fresh conversation
        """
        self.chat_session = None
        print("🔄 Chat session reset")
