import chromadb
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from . import config

class ChromaDBManager:
    """Manages ChromaDB interactions, including data loading and searching."""

    def __init__(self, db_path: str = "./data.db", json_path: Optional[str] = None):
        """Initializes the ChromaDB client and loads recipe data if provided."

        Args:
            db_path (str): Path to the directory for the persistent database.
            json_path (str, optional): Path to the JSON file containing recipe data.
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
        """Retrieves a collection from the cache or creates it if it doesn't exist."

        Args:
            name (str): The name of the collection.

        Returns:
            chromadb.Collection: The collection object.
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
        """Loads recipe data from a JSON file."

        Args:
            json_path (str): The path to the JSON file.

        Returns:
            int: The number of recipes loaded.
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
        """Formats a recipe dictionary into a string for embedding."

        Args:
            recipe (Dict[str, Any]): The recipe data.

        Returns:
            str: A formatted string representation of the recipe.
        """
        parts = []
        if "Summary" in recipe:
            parts.append(f"Summary: {recipe['Summary']}")
        
        if "Ingredients" in recipe:
            parts.append("Ingredients: " + ", ".join(recipe['Ingredients'][:10]))
        
        if "Instructions" in recipe:
            parts.append("Instructions: " + " ".join(recipe['Instructions'][:3]))
        
        if "Metadata" in recipe and isinstance(recipe["Metadata"], dict):
            meta = recipe["Metadata"]
            parts.append(f"Prep: {meta.get('prep_time_minutes', 'N/A')}min, Cook: {meta.get('cook_time_minutes', 'N/A')}min")
        
        return " | ".join(parts)
    
    def _extract_nutrition_keys(self) -> Dict[str, str]:
        """Extracts a set of all unique nutrition keys and their units from the recipes.
        
        Returns:
            Dict[str, str]: A dictionary mapping nutrition keys to their units.
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
        """Sort search results by a metadata field.
        
        Args:
            results: ChromaDB query results
            sort_by: Metadata field to sort by (e.g., 'nutr_val_calories')
            sort_order: 'asc' for ascending, 'desc' for descending
            limit: Maximum number of results to return
            
        Returns:
            List of sorted indices
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
        """Adds all loaded recipes to a ChromaDB collection in batches."

        Args:
            collection_name (str): The name of the collection.
            batch_size (int): The number of recipes to process in each batch.

        Returns:
            int: The total number of new recipes added to the collection.
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
        """Searches a collection for documents matching a query."

        Args:
            collection_name (str): The name of the collection to search.
            query_text (str): The text to search for.
            n_results (int): The maximum number of results to return.
            where (Optional[Dict[str, Any]]): A filter to apply to the metadata.
            where_document (Optional[Dict[str, Any]]): A filter to apply to the document content.

        Returns:
            List[Dict[str, Any]]: A list of search results.
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
        """Prepares a context string for a RAG model from search results."

        Args:
            collection_name (str): The name of the collection to search.
            query_text (str): The user's query.
            where (Optional[Dict[str, Any]]): A filter for the search.
            sort_by (Optional[str]): Field to sort by (e.g., 'nutr_val_calories').
            sort_order (str): Sort order - 'asc' for ascending or 'desc' for descending.
            limit (int): Maximum number of results to return when sorting.

        Returns:
            Dict[str, Any]: A dictionary containing the context, sources, and token info.
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

            # Skip relevance check when sorting by nutrition - we want all sorted results
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

