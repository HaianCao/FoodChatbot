"""
Constants and regex patterns for food data preprocessing.

Author: FoodChatbot Team
"""

import re

INPUT_ZIP_FILE = "data/foods.zip"
OUTPUT_JSON_FILE = "preprocessed_data.json"
CUSTOM_REPLACEMENTS = {
    '°C': ' deg C',
    '°F': ' deg F',
    '°': ' degrees',
    '–': '-',
    '—': '-',
    '™': '(TM)',
    '®': '(R)',
    '©': '(C)',
}
replacement_keys = sorted(CUSTOM_REPLACEMENTS.keys(), key=len, reverse=True)
REPLACEMENT_REGEX = re.compile('|'.join(re.escape(k) for k in replacement_keys))
_VULGAR_FRACTION_MAP = {
    '½': '1/2', '⅓': '1/3', '⅔': '2/3', '¼': '1/4', '¾': '3/4',
    '⅕': '1/5', '⅖': '2/5', '⅗': '3/5', '⅘': '4/5',
    '⅙': '1/6', '⅚': '5/6', '⅐': '1/7', '⅛': '1/8', '⅜': '3/8',
    '⅝': '5/8', '⅞': '7/8', '⅑': '1/9', '⅒': '1/10'
}
_VULGAR_RE = re.compile('|'.join(re.escape(k) for k in sorted(_VULGAR_FRACTION_MAP.keys(), key=len, reverse=True)))
_DIGIT_FRACTION_PATTERN = re.compile(r'(\d+)\s*[\u2044/]\s*(\d+)')
