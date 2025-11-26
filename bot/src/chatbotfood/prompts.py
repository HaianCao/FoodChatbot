"""Prompt templates for the Gemini AI client in the food chatbot application.

This module contains all prompt templates used for various AI operations
including translation, query rewriting, filter generation, and RAG responses.
All prompts are designed to work with Google's Gemini AI models.

Author: FoodChatbot Team
Version: 1.0.0
"""

def get_translation_prompt(text: str) -> str:
    """Returns the prompt for translating text to English.
    
    Generates a prompt that instructs Gemini to detect the language
    of input text and translate it to English while preserving
    numbers, measurements, and units exactly.
    
    Args:
        text: The text to be translated to English.
        
    Returns:
        A formatted prompt string for language detection and translation.
        
    Example:
        >>> prompt = get_translation_prompt("hãy tìm món ăn ít calo")
        >>> # Returns prompt for Gemini to detect Vietnamese and translate
    """
    return f"""Detect the language of the text and translate it to English. Preserve all numbers, measurements, and units exactly as they appear.

Return in this format:
Language: <language_code>
Translation: <english_translation>

Language codes: vi (Vietnamese), es (Spanish), fr (French), de (German), zh (Chinese), ja (Japanese), ko (Korean), etc.

Examples:
- "hãy nói cho tôi một món ăn có ít hơn 50 mg sắt" → 
  Language: vi
  Translation: tell me a dish with less than 50 mg of iron

- "tìm công thức có 0.005 gram protein" → 
  Language: vi
  Translation: find a recipe with 0.005 grams of protein

Text: {text}

Response:"""

def get_back_translation_prompt(text: str, target_language: str) -> str:
    """Returns the prompt for translating English text to target language.
    
    Generates a prompt for back-translation from English to a specified
    target language, preserving technical terms and measurements.
    
    Args:
        text: The English text to be translated.
        target_language: The target language code (e.g., 'vi', 'es', 'fr').
        
    Returns:
        A formatted prompt string for back-translation to target language.
        
    Example:
        >>> prompt = get_back_translation_prompt(
        ...     "Show me low calorie recipes", "vi"
        ... )
        >>> # Returns prompt to translate to Vietnamese
    """
    language_names = {
        'vi': 'Vietnamese',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'ko': 'Korean',
        'th': 'Thai',
        'id': 'Indonesian'
    }
    lang_name = language_names.get(target_language, target_language)
    
    return f"""Translate the following English text to {lang_name}. Preserve all numbers, measurements, and units exactly as they appear. Return ONLY the translation, nothing else.

Text: {text}

{lang_name} translation:"""


def get_query_rewrite_prompt(user_query: str, context_text: str) -> str:
    """Returns the prompt for rewriting vague queries using conversation context.
    
    Generates a prompt that instructs Gemini to rewrite user queries that
    contain vague references (like "that", "it", "the second one") by
    replacing them with specific terms from conversation history.
    
    Args:
        user_query: The user's potentially vague query to be rewritten.
        context_text: Recent conversation history providing context
            for resolving vague references.
            
    Returns:
        A formatted prompt string for query rewriting.
        
    Example:
        >>> context = "User: show pasta recipes\nBot: Here are 5 pasta dishes..."
        >>> prompt = get_query_rewrite_prompt(
        ...     "tell me about the second one", context
        ... )
        >>> # Returns prompt to resolve "the second one" to specific dish
    """
    return f"""You are a query rewriter for a recipe search system. Based on the conversation history below, rewrite the user's new query ONLY if it contains vague references.

CONVERSATION HISTORY:
{context_text}

USER'S NEW QUERY: {user_query}

CRITICAL RULES:
1. ONLY rewrite if the query contains vague references like:
   - Pronouns: "that", "it", "this", "these", "those"
   - References: "the first one", "the second dish", "that recipe", "món đó", "nó", "cái này", "cái kia", "món ấy"
   
2. If the query has vague references, replace them with specific recipe/dish names from the conversation

3. If the query is ALREADY CLEAR and SPECIFIC (mentions a dish name, ingredient, or is a new question), return it UNCHANGED

4. Keep the EXACT same language (Vietnamese → Vietnamese, English → English)

5. Keep the EXACT same intent and meaning - do NOT change what the user is asking for

6. Return ONLY the rewritten query, no explanations

EXAMPLES:

Good rewrites (vague → specific):
- "how to make that" + [previous: Pumpkin Chili] → "how to make Pumpkin Chili"
- "cách làm món đó" + [previous: Nước Chanh Brazil] → "cách làm Nước Chanh Brazil"
- "tell me about the second one" + [previous: 1. Salad, 2. Soup] → "tell me about Soup"

DO NOT rewrite (already clear):
- "cách làm nước chanh kiểu Brazil" → "cách làm nước chanh kiểu Brazil" (UNCHANGED)
- "show me pasta recipes" → "show me pasta recipes" (UNCHANGED)
- "món ăn ít calo" → "món ăn ít calo" (UNCHANGED)
- "món nước giải khát tốt nhất cho mùa hè" → "món nước giải khát tốt nhất cho mùa hè" (UNCHANGED)

REWRITE THIS QUERY:
{user_query}

YOUR ANSWER (query only):"""


def get_filter_generation_prompt(user_query: str, list_of_nutrition: str = "") -> str:
    """Returns the prompt for generating ChromaDB filter from natural language query.
    
    Generates a comprehensive prompt that instructs Gemini to convert natural
    language food queries into structured JSON filters for ChromaDB database.
    Handles nutrition filters, portion sizes, cooking times, and sorting criteria.
    
    The prompt includes:
        - Database schema with nutrition fields and units
        - Rules for qualitative vs quantitative terms
        - Sorting logic for "high", "low", "most", "least" queries
        - Unit conversion guidelines
        - JSON schema validation requirements
        
    Args:
        user_query: Natural language query about recipes or nutrition.
            Examples: "low calorie meals", "high protein dishes under 300 calories"
        list_of_nutrition: Optional custom nutrition field definitions.
            If empty, uses default nutrition schema with standard units.
            
    Returns:
        A formatted prompt string for filter generation that produces
        valid JSON filters for ChromaDB queries.
        
    Example:
        >>> prompt = get_filter_generation_prompt(
        ...     "show me low sodium dishes with lots of protein"
        ... )
        >>> # Returns prompt that generates sorting by protein desc
        >>> # with sodium filter
    """
    nutrition_info = list_of_nutrition if list_of_nutrition else """
    - `calories`: Kilocalories (kcal)
    - `protein`: Grams (g)
    - `fat`: Grams (g)
    - `carbohydrates`: Grams (g)
    - `sugar`: Grams (g)
    - `sodium`: Milligrams (mg)
    """
    
    return f"""# PROMPT START

## ROLE AND GOAL
You are an expert AI assistant specialized in Natural Language Understanding (NLU). Your primary goal is to analyze a user's query about food recipes and convert it into a structured JSON filter for a ChromaDB database. You must strictly adhere to the provided JSON schema and parsing rules.

## CONTEXT: DATABASE SCHEMA
The recipe database has the following filterable fields with their corresponding units:
- `prep_time`: Preparation time in **minutes**.
- `cook_time`: Cooking time in **minutes**.
- `servings`: Number of people the recipe serves. Examples:
  - "món ăn cho gia đình 6 người" → {{"servings": {{"$gte": 6}}}}
  - "phù hợp cho 4 người" → {{"servings": {{"$gte": 4}}}}
  - "món cho 2 người" → {{"servings": {{"$gte": 2}}}}
- **Nutrition Information (Database Units):**
    {nutrition_info}
    - Units can be different between user query and database values or maybe between each in database but still the same scale. You must account for these differences when generating filters.

## CRITICAL RULES FOR QUALITATIVE TERMS

**IMPORTANT**: When the user uses qualitative terms like "a lot of", "high", "rich in", "plenty of", "much", etc., you MUST use sorting instead of numeric filters:

- "a lot of protein" → Use sorting: sort_by_nutrition: "Protein", sort_order: "desc", NO numeric filter
- "high in fiber" → Use sorting: sort_by_nutrition: "Fiber", sort_order: "desc", NO numeric filter
- "rich in vitamins" → Use sorting by the specific vitamin, NO numeric filter
- "plenty of iron" → Use sorting: sort_by_nutrition: "Iron", sort_order: "desc", NO numeric filter

**ONLY use numeric filters** when the user provides specific numbers:
- "less than 500 calories" → Use filter: {{"nutr_val_calories": {{"$lte": 500}}}}
- "more than 20g protein" → Use filter: {{"nutr_val_protein": {{"$gte": 20}}}}
- "under 5mg sodium" → Use filter: {{"nutr_val_sodium": {{"$lte": 5}}}}

**DO NOT** create filters with value 0.0 unless explicitly requested by the user!

## SORTING SUPPORT
When the user requests "lowest", "highest", "top N", or qualitative terms:
- Set `sort_by_nutrition` to the nutrition key (e.g., "Calories" for "lowest calories")
- Set `sort_order` to "asc" for lowest/minimum or "desc" for highest/maximum/most/"a lot"
- Set `result_limit` to the requested number (default 10 if not specified)
- Do NOT add numeric filters for qualitative queries

Examples:
- "lowest calorie dishes" → sort_by_nutrition: "Calories", sort_order: "asc", result_limit: 10, NO filter
- "a lot of protein suitable for winter" → sort_by_nutrition: "Protein", sort_order: "desc", result_limit: 10, NO filter
- "top 5 highest protein recipes" → sort_by_nutrition: "Protein", sort_order: "desc", result_limit: 5, NO filter
- "dishes with least sodium" → sort_by_nutrition: "Sodium", sort_order: "asc", result_limit: 10, NO filter
- "high calcium meals" → sort_by_nutrition: "Calcium", sort_order: "desc", result_limit: 10, NO filter

## OUTPUT FORMAT
Your output MUST be a single JSON object that conforms to the following Pydantic models. Do not add any explanations or text outside of the JSON object.

User Query: "{user_query}"
"""


def get_rag_prompt(user_query: str, context: str) -> str:
    """Returns the prompt for generating RAG-based responses from recipe context.
    
    Creates a prompt that instructs Gemini to answer user questions using
    ONLY the provided recipe database context. Enforces strict adherence
    to database-only responses without external knowledge injection.
    
    Key features:
        - Database-only response enforcement
        - Conditional formatting rules (lists vs detailed recipes)
        - Source URL attribution for specific recipes
        - Natural, conversational tone guidelines
        - Structured ingredient and instruction formatting
        
    Formatting behavior:
        - Multiple recipes: Brief numbered lists with key info
        - Specific recipe details: Full ingredients and step-by-step instructions
        - Always include source URLs for detailed recipe responses
        
    Args:
        user_query: The user's question about recipes or cooking.
            Examples: "show me pasta recipes", "how to make chicken soup"
        context: Formatted recipe information from ChromaDB search.
            Contains recipe details, nutrition info, and metadata.
            
    Returns:
        A formatted prompt string that generates database-constrained
        responses with appropriate formatting for the query type.
        
    Example:
        >>> context = "Recipe: Pasta Salad\nIngredients: pasta, vegetables..."
        >>> prompt = get_rag_prompt("how to make pasta salad", context)
        >>> # Returns prompt for detailed recipe with ingredients and steps
    """
    return f"""You are a helpful food and nutrition assistant. Based ONLY on the recipe information provided below, answer the user's question.

RECIPE INFORMATION:
{context if context else "No recipes found matching the query."}

USER QUESTION: {user_query}

CRITICAL INSTRUCTIONS:
- ONLY use information from the RECIPE INFORMATION section above
- DO NOT use any external knowledge or information not provided in the context
- If the provided recipe information doesn't contain enough details to answer the question, clearly state that the information is not available in the database
- Present the information naturally without mentioning databases or data sources
- Include specific details like recipe names and nutritional values from the provided context only
- Be helpful, conversational, and natural

FORMATTING RULES:

**When listing multiple recipes/dishes (e.g., "show me 10 dishes", "list recipes"):**
- Use numbered lists with SHORT descriptions only
- Include: Recipe name, key nutrition value (if relevant), and brief 1-sentence description
- Do NOT include full ingredients or instructions
- Keep it clean and scannable

Example:
"Here are the 10 lowest calorie dishes:
1. **Grilled Chicken Salad** - 150 kcal - Light and refreshing with mixed greens
2. **Steamed Fish** - 180 kcal - Delicate white fish with lemon
..."

**When user asks specifically about ONE recipe's ingredients or instructions:**
- Then show full details with proper formatting
- Ingredients: Use bullet points (- or •), one per line
- Instructions: Use numbered steps (1., 2., 3.), one step per line
- Never write as paragraphs
- IMPORTANT: Always include the source URL at the end in this format: "Source: [URL]"

Example:
"Here's how to make Pumpkin Chili:

Ingredients:
- 1 tablespoon olive oil
- 1 small onion, chopped
- 1½ pounds ground beef

Instructions:
1. Heat oil in pot over medium-high heat
2. Add onion and peppers, cook until tender
3. Add ground beef and cook until browned

Source: https://example.com/pumpkin-chili"
"""

def get_rag_with_history_prompt(user_query: str, context: str) -> str:
    """Returns the prompt for RAG responses considering conversation context.
    
    Similar to get_rag_prompt but optimized for queries that may reference
    previous conversation elements. Maintains the same database-only
    constraint while being more contextually aware.
    
    This prompt is used when:
        - User queries might reference previous recipes shown
        - Follow-up questions about previously discussed dishes
        - Conversational context helps resolve ambiguous references
        
    Key differences from basic RAG prompt:
        - Enhanced conversational awareness
        - Better handling of follow-up questions
        - Maintains conversation flow and context
        - Same formatting rules and database constraints
        
    Args:
        user_query: The user's contextual question about recipes.
            Examples: "tell me more about that pasta", "what about the ingredients"
        context: Current recipe information from ChromaDB search,
            potentially filtered by conversation history.
            
    Returns:
        A formatted prompt string for context-aware RAG responses
        that maintains conversation continuity.
        
    Example:
        >>> context = "Recipe: Chicken Curry\nCalories: 450..."
        >>> prompt = get_rag_with_history_prompt(
        ...     "what are the ingredients for this", context
        ... )
        >>> # Returns prompt for ingredient details with context awareness
    """
    return f"""You are a helpful food and nutrition assistant.

RECIPE INFORMATION:
{context if context else "No recipes found."}

USER QUESTION: {user_query}

CRITICAL INSTRUCTIONS:
- ONLY use information from the RECIPE INFORMATION section above
- DO NOT use any external knowledge or information not provided in the context
- If the provided recipe information doesn't contain enough details to answer the question, clearly state that the information is not available in the database
- Present information naturally without mentioning databases or data sources
- Be conversational and helpful

FORMATTING RULES:
- When listing multiple recipes: Show brief descriptions only (name + calories/nutrition + 1-sentence summary)
- When user asks about a SPECIFIC recipe's details: Then show full ingredients and instructions with proper lists
- Ingredients: bullet points (- or •), one per line
- Instructions: numbered steps (1., 2., 3.), one step per line
- Never write as paragraphs
- IMPORTANT: When showing details for a specific recipe, always include the source URL at the end in format: "Source: [URL]"
"""
