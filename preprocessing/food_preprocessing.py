"""
Main runner for food data preprocessing. Imports and calls the modular pipeline.

Author: FoodChatbot Team
"""

from io_utils import process_zip_to_json

if __name__ == "__main__":
    process_zip_to_json()