"""
Metadata and nutrition processing utilities for food data preprocessing.

Author: FoodChatbot Team
"""

import re
from text_cleaning import normalize_text

def preprocess_metadata(metadata_list):
    """
    Restructure the Metadata field from a list of strings to a dictionary. Normalizes time to minutes.

    Args:
        metadata_list (list): List of metadata strings.
    Returns:
        dict: Processed metadata dictionary.
    """
    if not isinstance(metadata_list, list):
        return {}
    processed_meta = {}
    for item in metadata_list:
        item = normalize_text(item)
        if not isinstance(item, str) or ':' not in item:
            continue
        try:
            raw_key, raw_value = item.split(':', 1)
            key = raw_key.strip().lower().replace(' ', '_')
            value_str = raw_value.strip()
            num_match = re.search(r'(\d+(\.\d+)?)', value_str)
            num_value = None
            if num_match:
                num_value = float(num_match.group(1))
                if num_value.is_integer():
                    num_value = int(num_value)
            if 'time' in key:
                if 'hour' in value_str.lower() and num_value is not None:
                    num_value = num_value * 60
                processed_meta[f"{key}_minutes"] = num_value
            elif 'servings' in key:
                processed_meta[key] = num_value
            else:
                processed_meta[key] = num_value if num_value is not None else value_str
        except ValueError:
            continue
    return processed_meta

def preprocess_nutrition(nutrition_list):
    """
    Restructure the Nutrition field into a dictionary, each nutrient as a sub-dict with value and unit.

    Args:
        nutrition_list (list): List of nutrition strings.
    Returns:
        dict: Processed nutrition dictionary.
    """
    if not isinstance(nutrition_list, list):
        return {}
    processed_nutrition = {}
    pattern = re.compile(r'(-?[\d\.]+)\s*([\wμIU]+)?')
    for item in nutrition_list:
        item = normalize_text(item)
        if not isinstance(item, str) or ':' not in item:
            continue
        try:
            raw_key, raw_value = item.split(':', 1)
            key = raw_key.strip().lower().replace(' ', '_')
            value_obj = {"value": None, "unit": None}
            match = pattern.search(raw_value.strip())
            if match:
                try:
                    num_val = float(match.group(1))
                    if num_val.is_integer():
                        num_val = int(num_val)
                    value_obj["value"] = num_val
                except (ValueError, TypeError):
                    pass
                if match.group(2):
                    value_obj["unit"] = match.group(2)
            processed_nutrition[key] = value_obj
        except ValueError:
            continue
    return processed_nutrition
