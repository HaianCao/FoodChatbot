"""ChromaDB vector database manager for recipe storage and retrieval.

This module provides the ChromaDBManager class for managing recipe data
in a vector database, including document storage, semantic search, and
RAG (Retrieval-Augmented Generation) context preparation.

Author: FoodChatbot Team
Version: 1.0.0
"""
import chromadb
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from . import config

class ChromaDBManager:
    """Manages ChromaDB interactions for recipe storage and retrieval.
    
    This class handles all operations with the ChromaDB vector database,
    including recipe data loading, document embedding, semantic search,
    and context preparation for RAG applications.
    
    Attributes:
        client: ChromaDB persistent client instance
        _collections: Cache of ChromaDB collections
        recipes: List of loaded recipe dictionaries
        set_of_nuts: Dictionary of nutrition keys and their units
        
    Example:
        >>> manager = ChromaDBManager(
        ...     db_path="./chroma_db",
        ...     json_path="./recipes.json"
        ... )
        >>> manager.add_recipes_to_collection("recipes")
        >>> results = manager.search("recipes", "pasta with tomatoes", n_results=5)
    """

    def __init__(self, db_path: str = "./data.db", json_path: Optional[str] = None):
        """Initializes the ChromaDB client and loads recipe data.
        
        Sets up the persistent ChromaDB client, initializes collection cache,
        and optionally loads recipe data from a JSON file.
        
        Args:
            db_path: Path to the directory for the persistent database.
                Defaults to "./data.db".
            json_path: Path to the JSON file containing recipe data.
                If None, no recipes are loaded initially.
                
        Raises:
            IOError: If the database path is not accessible.
            json.JSONDecodeError: If the JSON file is malformed.
            
        Example:
            >>> manager = ChromaDBManager(
            ...     db_path="./my_recipes_db",
            ...     json_path="./recipe_data.json"
            ... )
        """
        print(f"INFO: Initializing ChromaDBManager with DB path: '{db_path}'")
        self.client = chromadb.PersistentClient(path=db_path)
        self._collections: Dict[str, chromadb.Collection] = {}
        
        self.recipes: List[Dict[str, Any]] = []
        if json_path:
            self.load_recipes_from_json(json_path)
        
        self.set_of_nuts = self._extract_nutrition_keys()
        print("INFO: ChromaDBManager ready.")

    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """Retrieves a collection from cache or creates it if it doesn't exist.
        
        This method implements caching for ChromaDB collections to avoid
        repeated database calls. Collections are created with default settings.
        
        Args:
            name: The name of the collection to retrieve or create.
            
        Returns:
            The ChromaDB collection object.
            
        Example:
            >>> collection = manager.get_or_create_collection("recipes")
            >>> print(f"Collection has {collection.count()} documents")
        """
        if name not in self._collections:
            print(f"INFO: Accessing collection '{name}' for the first time...")
            self._collections[name] = self.client.get_or_create_collection(name=name, configuration={
                "hnsw:space": "cosine",
                "hnsw:ef_construction": 200,
                "hnsw:M": 16,
            })
        return self._collections[name]

    def load_recipes_from_json(self, json_path: str) -> int:
        """Loads recipe data from a JSON file into memory.
        
        Reads and parses a JSON file containing recipe data, storing it
        in the recipes attribute for later processing.
        
        Args:
            json_path: The path to the JSON file containing recipe data.
                Expected format: List of recipe dictionaries.
                
        Returns:
            The number of recipes successfully loaded.
            
        Raises:
            IOError: If the file cannot be read.
            json.JSONDecodeError: If the JSON is malformed.
            
        Example:
            >>> count = manager.load_recipes_from_json("recipes.json")
            >>> print(f"Loaded {count} recipes")
        """
        try:
            json_file = Path(json_path)
            if not json_file.exists():
                print(f"ERROR: JSON file not found at: {json_path}")
                return 0
            
            with json_file.open('r', encoding='utf-8') as f:
                self.recipes = json.load(f)
            
            print(f"INFO: Loaded {len(self.recipes)} recipes from {json_path}")
            return len(self.recipes)
        except (IOError, json.JSONDecodeError) as e:
            print(f"ERROR: Failed to load or parse JSON file: {e}")
            return 0

    def _format_recipe_content(self, recipe: Dict[str, Any]) -> str:
        """Formats a recipe dictionary into a searchable text string.
        
        Converts structured recipe data into a formatted text representation
        optimized for vector embedding and semantic search.
        
        Args:
            recipe: Dictionary containing recipe data with keys like
                'Summary', 'Ingredients', 'Instructions', 'Metadata'.
                
        Returns:
            A formatted string representation of the recipe suitable
            for embedding. Format: "Summary: ... | Ingredients: ... | 
            Instructions: ... | Prep: ...min, Cook: ...min"
            
        Example:
            >>> recipe = {
            ...     "Summary": "Delicious pasta dish",
            ...     "Ingredients": ["pasta", "tomato sauce"],
            ...     "Instructions": ["Boil pasta", "Add sauce"]
            ... }
            >>> formatted = manager._format_recipe_content(recipe)
        """
        parts = []
        if "Summary" in recipe:
            parts.append(f"Summary: {recipe['Summary']}")
        
        if "Ingredients" in recipe:
            parts.append("Ingredients: " + ", ".join(recipe['Ingredients']))
        
        if "Instructions" in recipe:
            parts.append("Instructions: " + " ".join(recipe['Instructions']))
        
        if "Metadata" in recipe and isinstance(recipe["Metadata"], dict):
            meta = recipe["Metadata"]
            parts.append(f"Prep: {meta.get('prep_time_minutes', 'N/A')}min, Cook: {meta.get('cook_time_minutes', 'N/A')}min")
        
        return " | ".join(parts)
    
    def _extract_nutrition_keys(self) -> Dict[str, str]:
        """Extracts unique nutrition keys and their units from loaded recipes.
        
        Scans through all loaded recipe data to collect all unique nutrition
        parameter names (e.g., 'calories', 'protein', 'fat') and their
        corresponding units (e.g., 'kcal', 'g', 'mg').
        
        This information is used to create dynamic nutrition filtering
        schemas and validate nutrition-based queries.
        
        Returns:
            Dictionary mapping nutrition parameter names to their units.
            Keys are nutrition names like 'calories', 'protein'.
            Values are unit strings like 'kcal', 'g', 'mg'.
            
        Example:
            >>> manager._extract_nutrition_keys()
            # {'calories': 'kcal', 'protein': 'g', 'sodium': 'mg', ...}
        """
        nutrition_keys = {}
        for recipe in self.recipes:
            for nut, details in recipe.get("Nutrition", {}).items():
                if nut not in nutrition_keys:
                    nutrition_keys[nut] = details.get('unit', '')
        return nutrition_keys
    
    def _sort_results(
        self, 
        results: Dict[str, Any], 
        sort_by: str, 
        sort_order: str = "asc",
        limit: int = 10
    ) -> List[int]:
        """Sorts ChromaDB search results by a metadata field value.
        
        Takes the results from a ChromaDB query and sorts them based on
        a specified metadata field (typically nutrition values). This enables
        queries like "lowest calorie dishes" or "highest protein recipes".
        
        Args:
            results: ChromaDB query results containing documents, metadatas,
                and distances from vector search.
            sort_by: Metadata field name to sort by. Usually nutrition fields
                like 'nutr_val_calories', 'nutr_val_protein'.
            sort_order: Sort direction. 'asc' for ascending (lowest first),
                'desc' for descending (highest first). Defaults to 'asc'.
            limit: Maximum number of sorted results to return.
                
        Returns:
            List of indices representing the sorted order of results.
            These indices can be used to reorder the original results.
            
        Example:
            >>> # Sort by calories (ascending = lowest first)
            >>> sorted_indices = manager._sort_results(
            ...     results, 'nutr_val_calories', 'asc', 10
            ... )
            >>> # Returns [3, 7, 1, 9, ...] representing result order
        """
        metadatas = results['metadatas'][0]
        
        # Create list of (index, value) tuples
        indexed_values = []
        for i, metadata in enumerate(metadatas):
            value = metadata.get(sort_by, float('inf') if sort_order == 'asc' else float('-inf'))
            indexed_values.append((i, value))
        
        # Sort by value
        reverse = (sort_order == 'desc')
        indexed_values.sort(key=lambda x: x[1], reverse=reverse)
        
        # Return only the indices, limited to the specified number
        return [idx for idx, _ in indexed_values[:limit]]

    def add_recipes_to_collection(self, collection_name: str = "recipes", batch_size: int = 100) -> int:
        """Adds all loaded recipes to a ChromaDB collection in batches.
        
        Processes the loaded recipe data and stores it in ChromaDB for vector search.
        Each recipe is converted to a searchable text format and stored with
        comprehensive metadata including nutrition values, cooking times, and URLs.
        
        Processing includes:
            - Text formatting for embedding (summary, ingredients, instructions)
            - Metadata extraction (prep time, cook time, servings, nutrition)
            - Batch processing for memory efficiency
            - Error handling for malformed recipes
            
        Args:
            collection_name: Name of the ChromaDB collection to store recipes in.
                Defaults to "recipes".
            batch_size: Number of recipes to process in each batch.
                Larger batches are more efficient but use more memory.
                Defaults to 100.
                
        Returns:
            Total number of new recipes successfully added to the collection.
            
        Raises:
            Exception: If ChromaDB operations fail (logged but not raised).
            
        Example:
            >>> manager.load_recipes_from_json("recipes.json")
            >>> count = manager.add_recipes_to_collection("my_recipes", 50)
            >>> print(f"Added {count} recipes to ChromaDB")
        """
        if not self.recipes:
            print("WARNING: No recipes loaded to add to the collection.")
            return 0
        
        collection = self.get_or_create_collection(name=collection_name)
        total_added = 0
        
        for i in range(0, len(self.recipes), batch_size):
            batch = self.recipes[i:i + batch_size]
            print(f"INFO: Processing batch {i // batch_size + 1}/{(len(self.recipes) + batch_size - 1) // batch_size}...")
            
            documents, metadatas, ids = [], [], []
            for recipe in batch:
                try:
                    recipe_id = f"recipe_{recipe.get('id', recipe.get('URL'))}"
                    content = self._format_recipe_content(recipe)
                    if not content.strip():
                        continue

                    metadata = {
                        "url": recipe.get("URL", ""),
                        "prep_time": recipe.get("Metadata", {}).get("prep_time_minutes", 0),
                        "cook_time": recipe.get("Metadata", {}).get("cook_time_minutes", 0),
                        "servings": recipe.get("Metadata", {}).get("servings", 0),
                    }
                    
                    for nut, details in recipe.get("Nutrition", {}).items():
                        metadata[f"nutr_val_{nut.lower()}"] = details.get("value", 0)
                        metadata[f"nutr_unit_{nut.lower()}"] = details.get("unit", "")
                    
                    documents.append(content)
                    metadatas.append(metadata)
                    ids.append(recipe_id)
                except Exception as e:
                    print(f"WARNING: Skipping recipe due to processing error: {e}")

            if not documents:
                continue

            try:
                collection.add(documents=documents, metadatas=metadatas, ids=ids)
                total_added += len(documents)
                print(f"Successfully added {len(documents)} recipes to '{collection_name}'.")
            except Exception as e:
                print(f"ERROR: Failed to add batch to ChromaDB: {e}")
        
        print(f"SUCCESS: Finished processing. Total new recipes added: {total_added}")
        return total_added

    def search(
        self, 
        collection_name: str, 
        query_text: str, 
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Performs semantic search on a ChromaDB collection.
        
        Executes a vector similarity search to find recipes matching the query.
        Supports both semantic text matching and metadata filtering for
        precise recipe discovery.
        
        Args:
            collection_name: Name of the ChromaDB collection to search.
            query_text: Natural language query to search for.
                Examples: "pasta with tomatoes", "low calorie desserts"
            n_results: Maximum number of results to return. Defaults to 5.
            where: Optional metadata filter dictionary for structured filtering.
                Format: {"field": {"$operator": value}}
                Example: {"nutr_val_calories": {"$lte": 500}}
            where_document: Optional document content filter.
                Format: {"$contains": "text_to_find"}
                
        Returns:
            ChromaDB query results containing:
                - documents: List of formatted recipe texts
                - metadatas: List of recipe metadata dicts
                - distances: List of similarity distances
                - ids: List of unique recipe identifiers
                
        Example:
            >>> results = manager.search(
            ...     "recipes", 
            ...     "chicken pasta",
            ...     n_results=10,
            ...     where={"nutr_val_calories": {"$lte": 600}}
            ... )
            >>> print(f"Found {len(results['documents'][0])} recipes")
        """
        collection = self.get_or_create_collection(name=collection_name)
        try:
            query_params = {"query_texts": [query_text], "n_results": n_results}
            if where:
                query_params["where"] = where
            if where_document:
                query_params["where_document"] = where_document
                
            return collection.query(**query_params)
        except Exception as e:
            print(f"ERROR: Failed to query collection '{collection_name}': {e}")
            return []
        
    def prepare_rag_context(
        self, 
        collection_name: str, 
        query_text: str,
        where: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Prepares formatted context for RAG (Retrieval-Augmented Generation).
        
        Searches for relevant recipes and formats them into a context string
        suitable for feeding to an LLM. Handles both semantic search and
        nutrition-based sorting to provide the most relevant information.
        
        Processing pipeline:
            1. Perform vector search with optional metadata filtering
            2. Sort results by nutrition values if requested
            3. Filter by relevance score to ensure quality
            4. Format recipes with metadata and nutrition info
            5. Truncate to fit within token limits
            
        Args:
            collection_name: Name of the ChromaDB collection to search.
            query_text: User's search query in natural language.
            where: Optional metadata filter for structured constraints.
                Example: {"nutr_val_calories": {"$lte": 500}}
            sort_by: Optional nutrition field to sort by.
                Example: "nutr_val_calories" for calorie-based sorting.
            sort_order: Sort direction. "asc" for lowest first,
                "desc" for highest first. Defaults to "asc".
            limit: Maximum number of results when sorting.
                Defaults to 20 for comprehensive context.
                
        Returns:
            Dictionary containing:
                - context: Formatted text ready for LLM consumption
                - sources: List of recipe metadata and URLs for attribution
                - documents_found: Total number of matching recipes found
                
        Example:
            >>> context = manager.prepare_rag_context(
            ...     "recipes",
            ...     "low calorie pasta",
            ...     where={"nutr_val_calories": {"$lte": 400}},
            ...     sort_by="nutr_val_calories",
            ...     sort_order="asc",
            ...     limit=10
            ... )
            >>> print(context["context"])  # Formatted recipes for LLM
        """
        n_results = limit if sort_by else config.MAX_RESULTS
        
        results = self.search(
            collection_name=collection_name,
            query_text=query_text,
            where=where,
            n_results=min(n_results * 3, 100),  # Fetch more to sort from
            
        )
        
        if not results or not results.get('documents'):
            return {
                "context": "No relevant recipes found.",
                "sources": [],
                "documents_found": 0,
            }
        
        # Sort results if requested
        if sort_by:
            sorted_indices = self._sort_results(results, sort_by, sort_order, limit)
        else:
            sorted_indices = list(range(len(results['documents'][0])))
        
        context_parts, sources = [], []
        max_chars = config.MAX_CONTEXT_TOKENS * 4
        
        for idx in sorted_indices:
            content = results['documents'][0][idx]
            metadata = results['metadatas'][0][idx]
            distance = results['distances'][0][idx]
            # Cosine distance: range [0, 2], convert to similarity [0, 1]
            # distance=0 (identical) -> similarity=1.0
            # distance=2 (opposite) -> similarity=0.0
            similarity = max(0.0, 1.0 - distance)

            # Only return results with high relevance to ensure database-only responses
            if not sort_by and similarity < config.MIN_RELEVANCE_SCORE:
                continue

            meta_parts, nutri_parts = [], []
            for key, value in metadata.items():
                if key.startswith('nutr_val_'):
                    nut_name = key.replace('nutr_val_', '').replace('_', ' ').title()
                    unit = metadata.get(f"nutr_unit_{key.replace('nutr_val_', '')}", '')
                    nutri_parts.append(f"{nut_name}: {value}{unit}")
                elif key == 'servings':
                    meta_parts.append(f"Servings: {int(value)} people")
                elif key not in ['url', 'recipe_index'] and not key.startswith('nutr_unit_'):
                    display_key = key.replace('_', ' ').title()
                    meta_parts.append(f"{display_key}: {value}")
            
            metadata_summary = " | ".join(meta_parts)
            if nutri_parts:
                metadata_summary += " | Nutrition: " + ", ".join(nutri_parts)

            entry = f"[Relevance: {similarity:.2f}] {content}\nMetadata: {metadata_summary}\nURL: {metadata.get('url', 'N/A')}"
            
            if len("\n\n".join(context_parts)) + len(entry) > max_chars:
                break
            
            context_parts.append(entry)
            sources.append({"url": metadata.get('url', ''), "relevance_score": similarity, "metadata": metadata})
        
        return {
            "context": "\n\n".join(context_parts),
            "sources": sources,
            "documents_found": len(results['documents'][0]),
        }

# Module-level instance to act as a singleton
db_manager = ChromaDBManager(
    db_path=str(config.CHROMA_DB_PATH),
    json_path=str(config.PROCESSED_DATA_PATH)
)

