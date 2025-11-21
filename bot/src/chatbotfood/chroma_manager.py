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
            self._collections[name] = self.client.get_or_create_collection(name=name)
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
                print(f"  ✓ Successfully added {len(documents)} recipes to '{collection_name}'.")
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
            similarity = max(0.0, 1.0 - (distance / 2.0))

            # Skip relevance check when sorting by nutrition - we want all sorted results
            if not sort_by and similarity < config.MIN_RELEVANCE_SCORE:
                continue

            meta_parts, nutri_parts = [], []
            for key, value in metadata.items():
                if key.startswith('nutr_val_'):
                    nut_name = key.replace('nutr_val_', '').replace('_', ' ').title()
                    unit = metadata.get(f"nutr_unit_{key.replace('nutr_val_', '')}", '')
                    nutri_parts.append(f"{nut_name}: {value}{unit}")
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

def get_or_create_collection(self, name: str) -> chromadb.Collection:
    """
    Lấy hoặc tạo một collection và lưu vào cache để tái sử dụng.
    Đây là cách làm hiệu quả hơn thay vì gọi self.client.get... mỗi lần.

    Args:
        name (str): Tên của collection.

    Returns:
        chromadb.Collection: Đối tượng collection.
    """
    if name not in self._collections:
        print(f"INFO: Đang truy cập collection '{name}' lần đầu...")
        self._collections[name] = self.client.get_or_create_collection(name=name)
    return self._collections[name]

def load_recipes_from_json(self, json_path: str) -> int:
    """
    Load dữ liệu recipe từ file JSON.

    Args:
        json_path (str): Đường dẫn đến file JSON.

    Returns:
        int: Số lượng recipes được load.
    """
    try:
        if not Path(json_path).exists():
            print(f"ERROR: File JSON không tồn tại: {json_path}")
            return 0
        
        with open(json_path, 'r', encoding='utf-8') as f:
            self.recipes = json.load(f)
        
        print(f"INFO: Đã load {len(self.recipes)} recipes từ {json_path}")
        return len(self.recipes)
    except Exception as e:
        print(f"ERROR: Lỗi khi load JSON: {e}")
        return 0

def format_recipe_content(self, recipe: Dict[str, Any]) -> str:
    """
    Định dạng recipe thành text content cho embedding.
    
    Args:
        recipe (Dict): Recipe object từ JSON.

    Returns:
        str: Formatted text content.
    """
    parts = []
    
    if "Summary" in recipe:
        parts.append(f"Summary: {recipe['Summary']}")
    
    if "Ingredients" in recipe:
        ingredients_text = "Ingredients: " + ", ".join(recipe['Ingredients'][:10])  # Limit to first 10
        parts.append(ingredients_text)
    
    if "Instructions" in recipe:
        instructions_text = "Instructions: " + " ".join(recipe['Instructions'][:3])  # Limit to first 3 steps
        parts.append(instructions_text)
    
    if "Metadata" in recipe:
        meta = recipe["Metadata"]
        if isinstance(meta, dict):
            meta_text = f"Prep: {meta.get('prep_time_minutes', 'N/A')}min, Cook: {meta.get('cook_time_minutes', 'N/A')}min"
            parts.append(meta_text)
    
    return " | ".join(parts)
    
def load_set_of_nuts(self):
    """
    Tạo tập hợp các loại dinh dưỡng từ dữ liệu recipe.
    """
    for recipe in self.recipes:
        for nut, p in recipe.get("Nutrition", {}).items():
            self.set_of_nuts[nut] = p['unit']

def add_recipes_to_chroma(self, collection_name: str = "recipes", batch_size: int = 50) -> int:
    """
    Thêm tất cả recipes từ JSON vào ChromaDB với batch processing.
    Args:
        collection_name (str): Tên collection để lưu recipes.
        batch_size (int): Kích thước batch để xử lý cùng một lúc (giảm API calls).
    Returns:
        int: Số lượng recipes thực sự được thêm.
    """
    if not self.recipes:
        print("WARNING: Không có recipes để thêm. Hãy load JSON trước.")
        return 0
    
    total_added = 0
    total_recipes = len(self.recipes)
    
    # Process recipes in batches
    for batch_start in range(0, total_recipes, batch_size):
        batch_end = min(batch_start + batch_size, total_recipes)
        batch_recipes = self.recipes[batch_start:batch_end]
        
        print(f"INFO: Xử lý batch {batch_start // batch_size + 1}/{(total_recipes + batch_size - 1) // batch_size} (recipes {batch_start}-{batch_end}/{total_recipes})...")
        
        documents = []
        metadatas = []
        ids = []
        
        for local_idx, recipe in enumerate(batch_recipes):
            idx = batch_start + local_idx
            try:
                # Tạo content từ recipe
                content = self.format_recipe_content(recipe)
                if not content.strip():
                    continue
                
                # Tạo metadata
                metadata = {
                    "url": recipe.get("URL", ""),
                    "prep_time": recipe.get("Metadata", {}).get("prep_time_minutes", 0),
                    "cook_time": recipe.get("Metadata", {}).get("cook_time_minutes", 0),
                    "servings": recipe.get("Metadata", {}).get("servings", 0),
                    "recipe_index": idx
                }
                
                for nut, p in recipe.get("Nutrition", {}).items():
                    metadata[f"nutr_val_{nut.lower()}"] = p["value"]
                    metadata[f"nutr_unit_{nut.lower()}"] = p["unit"]
                    
                    
                
                # Tạo ID duy nhất
                recipe_id = f"recipe_{idx}"
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(recipe_id)
                
            except Exception as e:
                print(f"WARNING: Lỗi xử lý recipe index {idx}: {e}")
                continue
        
        if not documents:
            print(f"WARNING: Batch này không có recipes hợp lệ.")
            continue
        
        # Thêm batch vào ChromaDB
        print(f"  ⏳ Thêm {len(documents)} recipes vào ChromaDB...")
        added = self.add_documents(
            collection_name=collection_name,
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            skip_duplicates=True
        )
        total_added += added
        print(f"  ✓ Thêm thành công {added} recipes\n")
    
    print(f"SUCCESS: Tổng cộng thêm {total_added} recipes vào ChromaDB")
    return total_added


def add_documents(
    self, 
    collection_name: str, 
    documents: List[str], 
    metadatas: List[dict] = None, 
    ids: List[str] = None,
    skip_duplicates: bool = True
    ) -> int:
    """
    Thêm tài liệu vào một collection cụ thể với duplicate detection.
    Args:
        collection_name (str): Tên collection cần thêm vào.
        documents (List[str]): Danh sách nội dung các tài liệu.
        metadatas (List[dict]): Danh sách các metadata tương ứng.
        ids (List[str]): Danh sách các ID duy nhất tương ứng.
        skip_duplicates (bool): Bỏ qua documents với ID đã tồn tại.
        
    Returns:
        int: Số lượng documents thực sự được thêm vào DB.
    """
    if not documents:
        print("WARNING: Không có tài liệu nào để thêm.")
        return 0
    
    if not ids:
        # Tạo IDs ngẫu nhiên nếu không cung cấp
        ids = [f"doc_{i}" for i in range(len(documents))]
        
    if not metadatas:
        metadatas = [{} for _ in documents]
    collection = self.get_or_create_collection(name=collection_name)
    
    # Duplicate detection
    if skip_duplicates:
        try:
            # Lấy tất cả IDs hiện có trong collection
            existing_data = collection.get(ids=ids, include=[])
            existing_ids = set(existing_data['ids']) if existing_data['ids'] else set()
            
            # Filter out duplicates
            filtered_docs = []
            filtered_metas = []
            filtered_ids = []
            duplicates_count = 0
            
            for doc, meta, doc_id in zip(documents, metadatas, ids):
                if doc_id not in existing_ids:
                    filtered_docs.append(doc)
                    filtered_metas.append(meta)
                    filtered_ids.append(doc_id)
                else:
                    duplicates_count += 1
            
            if duplicates_count > 0:
                print(f"INFO: Bỏ qua {duplicates_count} documents trùng lặp.")
            
            if not filtered_docs:
                print("INFO: Tất cả documents đã tồn tại, không có gì để thêm.")
                return 0
            
            documents = filtered_docs
            metadatas = filtered_metas
            ids = filtered_ids
            
        except Exception as e:
            print(f"WARNING: Không thể kiểm tra duplicates: {e}. Tiếp tục thêm...")
    
    # Thêm documents (embedding sẽ tự động được tạo bởi ChromaDB)
    try:
        print(f"  💾 Generating embeddings và thêm {len(documents)} documents...")
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"  ✓ Embeddings generated và documents added thành công")
        return len(documents)
    except Exception as e:
        print(f"ERROR: Lỗi khi thêm documents: {e}")
        # Fallback: thử thêm từng document riêng lẻ
        print(f"  ⚠️  Falling back to one-by-one insertion...")
        return self._add_documents_one_by_one(collection, documents, metadatas, ids)

def search(
    self, 
    collection_name: str, 
    query_text: str, 
    n_results: int = 5,
    where: Optional[Dict[str, Any]] = None,
    where_document: Optional[Dict[str, Any]] = None,
    min_relevance_score: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Tìm kiếm thông tin trong collection bằng một câu truy vấn với filtering và ranking.

    Args:
        collection_name (str): Tên collection cần tìm kiếm.
        query_text (str): Câu hỏi hoặc nội dung cần tìm.
        n_results (int): Số lượng kết quả trả về tối đa.
        where (Optional[Dict]): Filter metadata (e.g., {"author": "username"}).
        where_document (Optional[Dict]): Filter document content.
        min_relevance_score (float): Điểm tương đồng tối thiểu (0-1). Distance sẽ được convert.

    Returns:
        List[Dict[str, Any]]: Danh sách các kết quả đã được định dạng và ranked.
    """
    collection = self.get_or_create_collection(name=collection_name)
    # Query với filtering (ChromaDB automatically creates embedding for query_texts)
    try:
        query_params = {
            "query_texts": [query_text],
            "n_results": n_results
        }
        
        if where:
            query_params["where"] = where
        if where_document:
            query_params["where_document"] = where_document
            
        results = collection.query(**query_params)
    except Exception as e:
        print(f"LỖI: Lỗi khi query collection: {e}")
        return []
        
    # Định dạng lại kết quả với relevance scoring
    formatted_results = []
    if results and results.get('documents'):
        for i, doc_content in enumerate(results['documents'][0]):
            distance = results['distances'][0][i]
            # Convert distance to similarity score (0-1, higher is better)
            # Cosine distance range: 0 (identical) to 2 (opposite)
            similarity_score = max(0.0, 1.0 - (distance / 2.0))
            
            # Filter by minimum relevance score
            if similarity_score < min_relevance_score:
                continue
                
            formatted_results.append({
                'content': doc_content,
                'metadata': results['metadatas'][0][i],
                'distance': distance,
                'similarity_score': similarity_score,
                'rank': i + 1
            })
    
    return formatted_results

def _add_documents_one_by_one(
    self, 
    collection: chromadb.Collection, 
    documents: List[str], 
    metadatas: List[dict], 
    ids: List[str]
) -> int:
    """
    Fallback method: thêm từng document riêng lẻ khi batch add fail.
    
    Args:
        collection: ChromaDB collection object.
        documents: List of document contents.
        metadatas: List of metadata dicts.
        ids: List of document IDs.
        
    Returns:
        int: Số lượng documents thành công.
    """
    success_count = 0
    failed_count = 0
    
    for doc, meta, doc_id in zip(documents, metadatas, ids):
        try:
            collection.add(
                documents=[doc],
                metadatas=[meta],
                ids=[doc_id]
            )
            success_count += 1
        except Exception as e:
            print(f"ERROR: Không thể thêm document ID '{doc_id}': {e}")
            failed_count += 1
    
    print(f"FALLBACK: Đã thêm {success_count}/{len(documents)} documents. Failed: {failed_count}")
    return success_count
    
def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
    """
    Lấy thống kê về một collection.
    
    Args:
        collection_name (str): Tên collection.
        
    Returns:
        Dict với thông tin: count, name, metadata
    """
    try:
        collection = self.get_or_create_collection(name=collection_name)
        count = collection.count()
        
        return {
            "name": collection_name,
            "count": count,
            "metadata": collection.metadata if hasattr(collection, 'metadata') else {}
        }
    except Exception as e:
        print(f"ERROR: Không thể lấy stats cho collection '{collection_name}': {e}")
        return {"name": collection_name, "count": 0, "error": str(e)}

def delete_collection(self, collection_name: str) -> bool:
    """
    Xóa một collection khỏi database.
    
    Args:
        collection_name (str): Tên collection cần xóa.
        
    Returns:
        bool: True nếu thành công.
    """
    try:
        self.client.delete_collection(name=collection_name)
        if collection_name in self._collections:
            del self._collections[collection_name]
        print(f"SUCCESS: Đã xóa collection '{collection_name}'.")
        return True
    except Exception as e:
        print(f"ERROR: Không thể xóa collection '{collection_name}': {e}")
        return False

def prepare_rag_context(
    self, 
    collection_name: str, 
    query_text: str,
    where: Optional[Dict[str, Any]] = None,
    where_document: Optional[Dict[str, Any]] = None,
    max_tokens: int = 4000,
    n_results: int = 10,
    min_relevance: float = 0.5
) -> Dict[str, Any]:
    """
    Chuẩn bị context cho RAG với quản lý token limit, tối ưu cho recipe data.
    
    Args:
        collection_name (str): Tên collection.
        query_text (str): Query từ user.
        max_tokens (int): Số tokens tối đa cho context (ước tính ~4 chars = 1 token).
        n_results (int): Số documents tối đa để retrieve.
        min_relevance (float): Điểm tương đồng tối thiểu.
        
    Returns:
        Dict với 'context', 'sources', 'total_tokens' (ước tính)
    """
    # Search for relevant documents and also add metadata to results
    results = self.search(
        collection_name=collection_name,
        query_text=query_text,
        where=where,
        where_document=where_document,
        n_results=n_results,
        min_relevance_score=min_relevance
    )
    
    if not results:
        return {
            "context": "",
            "sources": [],
            "total_tokens": 0,
            "documents_found": 0,
            "message": "Không tìm thấy thông tin liên quan."
        }
    
    # Build context within token limit
    context_parts = []
    sources = []
    estimated_tokens = 0
    max_chars = max_tokens * 4  # Rough estimate: 4 chars ≈ 1 token
    
    for result in results:
        content = result['content']
        metadata = result['metadata']
        score = result['similarity_score']
        
        # Format a detailed metadata string
        meta_parts = []
        nutri_parts = []
        for key, value in metadata.items():
            if key.startswith('nutr_val_'):
                # Format nutrition data: "Calories: 500 kcal"
                nut_name = key.replace('nutr_val_', '').replace('_', ' ').title()
                unit = metadata.get(f"nutr_unit_{key.replace('nutr_val_', '')}", '')
                nutri_parts.append(f"{nut_name}: {value}{unit}")
            elif key not in ['url', 'recipe_index'] and not key.startswith('nutr_unit_'):
                # Format other metadata: "Prep Time: 15 min"
                display_key = key.replace('_', ' ').title()
                meta_parts.append(f"{display_key}: {value}")
        
        metadata_summary = " | ".join(meta_parts)
        if nutri_parts:
            metadata_summary += " | Nutrition: " + ", ".join(nutri_parts)
            
        entry = f"[Relevance: {score:.2f}] {content}\nMetadata: {metadata_summary}\nURL: {metadata.get('url', 'N/A')}"
        entry_chars = len(entry)
        
        # Check if adding this would exceed limit
        if estimated_tokens * 4 + entry_chars > max_chars:
            break
        
        context_parts.append(entry)
        sources.append({
            "url": metadata.get('url', ''),
            "relevance_score": score,
            "metadata": metadata
        })
        estimated_tokens += entry_chars // 4
    
    context = "\n\n".join(context_parts)
    
    return {
        "context": context,
        "sources": sources,
        "total_tokens": estimated_tokens,
        "documents_used": len(sources),
        "documents_found": len(results)
    }