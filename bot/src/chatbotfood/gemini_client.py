"""Gemini AI client for recipe chatbot with RAG capabilities."""

import json
from typing import Optional, Dict, Any, List

import google.genai as genai
from google.genai import types

from . import schemas
from . import prompts
db_manager = None  # Will be assigned the singleton instance of ChromaDBManager
from .chroma_manager import db_manager

class GeminiClient:
    """Client for interacting with Google's Gemini API with RAG capabilities."""
    
    DEFAULT_MODEL = "gemini-2.5-flash-lite"
    ADVANCED_MODEL = "gemini-2.5-flash-lite"
    
    def __init__(self, api_key: str, system_instruction: str = ""):
        """Initialize the Gemini client.
        
        Args:
            api_key: Google AI API key for authentication
            system_instruction: Optional system-level instructions for the model
        """
        self.config = types.GenerateContentConfig(
            system_instruction=system_instruction,
        )
        self.client = genai.Client(api_key=api_key)
        self.chat_session = None  # Will be created when starting chat

    def start_chat_session(self, model: Optional[str] = None, system_instruction: str = ""):
        """Start a new chat session with Gemini.
        
        Args:
            model: The Gemini model to use (defaults to DEFAULT_MODEL)
            system_instruction: System instructions for the chat session
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
        """Translate non-English text to English using Gemini.
        
        Args:
            text: The text to translate
            model: The Gemini model to use (defaults to DEFAULT_MODEL)
            
        Returns:
            Tuple of (translated_text, detected_language)
            detected_language will be 'en' for English, or the detected language code
        """
        if not text or text.isascii():
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
        """Translate English text to target language using Gemini.
        
        Args:
            text: The English text to translate
            target_language: The target language code (e.g., 'vi' for Vietnamese)
            model: The Gemini model to use (defaults to DEFAULT_MODEL)
            
        Returns:
            Translated text in target language
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
        """Rewrite vague queries using conversation context.
        
        Uses recent conversation history to expand references like "that", "it", 
        "the second one" into specific, searchable queries for the RAG system.
        
        Args:
            user_query: The user's potentially vague query
            conversation_history: List of recent messages for context
            
        Returns:
            Clear, specific query ready for ChromaDB search
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

    def generate_text(self, prompt: str, model: Optional[str] = None) -> str:
        """Generate text response from a simple prompt.
        
        Args:
            prompt: The text prompt to send to the model
            model: The Gemini model to use (defaults to DEFAULT_MODEL)
            
        Returns:
            Generated text response
        """
        model = model or self.DEFAULT_MODEL
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        ]

        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=self.config
        )
        return response.text
    
    def generate_chromadb_filter(self, user_query: str) -> Dict[str, Any]:
        """Generate ChromaDB filter from natural language query.
        
        Converts user queries like "recipes under 30 minutes with high protein"
        into structured ChromaDB filter conditions.
        
        Args:
            user_query: Natural language query describing recipe requirements
            
        Returns:
            ChromaDB-compatible 'where' filter dict, or empty dict if generation fails
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
        """Convert filter object to ChromaDB 'where' clause with sorting support.
        
        Args:
            filter_obj: Parsed filter object from Gemini response
            
        Returns:
            Dict with 'where' clause and optional 'sort_by', 'sort_order', 'limit' keys
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

    def generate_with_rag_context(
        self, 
        user_query: str, 
        rag_context: Dict[str, Any],
        model: Optional[str] = None,
        translate: bool = True
    ) -> str:
        """Generate response using RAG (Retrieval-Augmented Generation) context.
        
        Combines retrieved recipe information from ChromaDB with the user's question
        to provide contextually relevant answers.
        
        Args:
            user_query: The user's original question
            rag_context: Dict with 'context' and 'sources' from ChromaDBManager
            model: The Gemini model to use (defaults to DEFAULT_MODEL)
            translate: Whether to translate the query to English first
            
        Returns:
            Generated response incorporating RAG context
        """
        model = model or self.DEFAULT_MODEL
        translated_query = self._prepare_query(user_query, translate, model)
        context_text = rag_context.get('context', '')
        prompt_with_context = self._build_rag_prompt(translated_query, context_text)
        return self._generate_response(prompt_with_context, model)

    def generate_with_conversation_and_rag(
        self,
        user_query: str,
        rag_context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        system_instruction: str = "",
        translate: bool = True
    ) -> str:
        """Generate response using chat session and RAG context.
        
        Uses Gemini's native chat API to maintain conversation context while
        incorporating retrieved recipe information.
        
        Args:
            user_query: The current user question
            rag_context: Dict with 'context' and 'sources' from ChromaDBManager
            conversation_history: Not used (chat session maintains history)
            model: The Gemini model to use (defaults to DEFAULT_MODEL)
            system_instruction: System instructions for chat session
            translate: Whether to translate the query to English first
            
        Returns:
            Generated response with conversation and RAG context
        """
        # Create new chat session if not exists
        if self.chat_session is None:
            self.start_chat_session(model=model, system_instruction=system_instruction)
        
        context_text = rag_context.get('context', '')
        current_prompt = prompts.get_rag_with_history_prompt(user_query, context_text)
        
        # Send message through chat session
        response = self.chat_session.send_message(current_prompt)
        
        return response.text
    
    def _prepare_query(self, query: str, translate: bool, model: str) -> str:
        """Prepare and optionally translate user query."""
        if translate:
            translated = self.translate_to_english(query, model)
            print(f"  📝 Original: {query}")
            print(f"  🔄 Translated: {translated}\n")
            return translated
        return query
    
    def _build_rag_prompt(self, query: str, context: str) -> str:
        """Build prompt with RAG context."""
        return prompts.get_rag_prompt(query, context)
    
    def _generate_response(self, prompt: str, model: str) -> str:
        """Generate response from a prompt."""
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)]
            )
        ]
        
        response = self.client.models.generate_content(
            model=model,
            contents=contents,
            config=self.config
        )
        return response.text
    
    def reset_chat_session(self):
        """Reset the chat session to start fresh."""
        self.chat_session = None
        print("🔄 Chat session reset")
