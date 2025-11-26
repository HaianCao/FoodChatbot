"""
Text normalization and cleaning utilities for food data preprocessing.

Author: FoodChatbot Team
"""

import unicodedata
import re
from constants import CUSTOM_REPLACEMENTS, REPLACEMENT_REGEX, _VULGAR_FRACTION_MAP, _VULGAR_RE, _DIGIT_FRACTION_PATTERN

def preprocess_simple_text(value):
    """
    Return a safe stripped string for simple fields (URL, Summary).

    Args:
        value (Any): The value to process.
    Returns:
        str: The processed string, or empty string if invalid.
    """
    if value is None:
        return ""
    try:
        return str(value).strip()
    except Exception:
        return ""

def normalize_text(text):
    """
    Normalize text: Unicode NFC, replace custom chars, convert vulgar fractions, collapse whitespace.

    Args:
        text (str): The text to normalize.
    Returns:
        str: The normalized text.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    text = unicodedata.normalize('NFC', text)
    try:
        text = REPLACEMENT_REGEX.sub(lambda m: CUSTOM_REPLACEMENTS[m.group(0)], text)
    except Exception:
        pass
    text = _VULGAR_RE.sub(lambda m: _VULGAR_FRACTION_MAP[m.group(0)], text)
    text = _DIGIT_FRACTION_PATTERN.sub(r'\1/\2', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def preprocess_string_list(str_list):
    """
    Clean a list of strings (e.g., Ingredients, Instructions).

    Args:
        str_list (list): List of strings to clean.
    Returns:
        list: Cleaned list of non-empty strings.
    """
    if not isinstance(str_list, list):
        return []
    cleaned_list = []
    for item in str_list:
        if isinstance(item, str):
            cleaned_item = normalize_text(item.strip())
            if cleaned_item:
                cleaned_list.append(cleaned_item)
    return cleaned_list
