"""
File I/O and orchestration utilities for food data preprocessing.

Author: FoodChatbot Team
"""

import json
import zipfile
from pathlib import Path
from tqdm import tqdm
from constants import INPUT_ZIP_FILE, OUTPUT_JSON_FILE
from text_cleaning import preprocess_simple_text, normalize_text, preprocess_string_list
from metadata import preprocess_metadata, preprocess_nutrition
from comments import preprocess_comments

def process_zip_to_json(input_zip_path=None, output_json_path=None):
    """
    Read a .zip file of JSONs, process and restructure, and write to a single output JSON file.

    Args:
        input_zip_path (str or Path, optional): Path to input .zip file. Defaults to INPUT_ZIP_FILE.
        output_json_path (str or Path, optional): Path to output .json file. Defaults to OUTPUT_JSON_FILE.
    Returns:
        None
    """
    if input_zip_path is None:
        input_zip_path = Path(INPUT_ZIP_FILE)
    else:
        input_zip_path = Path(input_zip_path)
    if output_json_path is None:
        output_json_path = Path(OUTPUT_JSON_FILE)
    else:
        output_json_path = Path(output_json_path)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    all_processed_data = []
    if not input_zip_path.exists():
        print(f"Error: Input .zip file not found at: '{input_zip_path}'")
        return
    print(f"Reading .zip file from: {input_zip_path}")
    try:
        with zipfile.ZipFile(input_zip_path, 'r') as zf:
            json_files_in_zip = [f for f in zf.namelist() if f.endswith('.json') and not f.startswith('__')]
            if not json_files_in_zip:
                print(f"Error: No .json files found in '{input_zip_path}'")
                return
            print(f"Found {len(json_files_in_zip)} .json files. Processing...")
            for file_name in tqdm(json_files_in_zip, desc="Processing JSON"):
                try:
                    with zf.open(file_name) as f:
                        content_str = f.read().decode('utf-8')
                        data = json.loads(content_str)
                    new_data = {
                        "URL": preprocess_simple_text(data.get('URL')),
                        "Summary": normalize_text(preprocess_simple_text(data.get('Summary'))),
                        "Metadata": preprocess_metadata(data.get('Metadata', [])),
                        "Ingredients": preprocess_string_list(data.get('Ingredients', [])),
                        "Instructions": preprocess_string_list(data.get('Instructions', [])),
                        "Nutrition": preprocess_nutrition(data.get('Nutrition', [])),
                        "Comments": preprocess_comments(data.get('Comments', []))
                    }
                    all_processed_data.append(new_data)
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON file: {file_name}")
                except Exception as e:
                    print(f"Warning: Error processing file {file_name}: {e}")
    except zipfile.BadZipFile:
        print(f"Error: '{input_zip_path}' is not a valid .zip file.")
        return
    except FileNotFoundError:
        print(f"Error: File not found '{input_zip_path}'.")
        return
    print(f"\nWriting {len(all_processed_data)} objects to single JSON file...")
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_processed_data, f, indent=2, ensure_ascii=False)
        print("--- COMPLETE ---")
        print(f"Processed and saved {len(all_processed_data)} recipes.")
        print(f"Results saved at: {output_json_path.resolve()}")
    except Exception as e:
        print(f"Error writing output file: {e}")
