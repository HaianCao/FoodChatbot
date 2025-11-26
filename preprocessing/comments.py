"""
Comment processing utilities for food data preprocessing.

Author: FoodChatbot Team
"""
from text_cleaning import normalize_text

def preprocess_comments(comments_list):
    """
    Restructure the Comments field from a list of strings to a list of dicts {author, text}.

    Args:
        comments_list (list): List of comment strings.
    Returns:
        list: List of processed comment dicts.
    """
    if not isinstance(comments_list, list):
        return []
    processed_comments = []
    for item in comments_list:
        if not isinstance(item, str) or not item.strip():
            continue
        item = normalize_text(item.strip())
        if not item:
            continue
        author = None
        text = item
        if ' says:' in item:
            try:
                parts = item.split(' says:', 1)
                if len(parts) == 2:
                    author = parts[0].strip()
                    text = parts[1].strip()
            except Exception:
                pass
        if text:
            processed_comments.append({"author": author, "text": text})
    return processed_comments
