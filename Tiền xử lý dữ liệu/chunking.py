import json
import re
from tqdm import tqdm


def extract_recipe_name(url):
    """Lấy tên món ăn từ URL."""
    name = url.strip("/").split("/")[-1]
    name = name.replace("-", " ").title()
    return name


def format_metadata(metadata):
    """Chuyển Metadata từ dạng dict → câu chữ dễ đọc."""
    parts = []

    for key, value in metadata.items():
        key_clean = key.replace("_", " ")

        # Nếu là thời gian (có Hours/Minutes/Seconds)
        if isinstance(value, dict) and {"Hours", "Minutes", "Seconds"} <= value.keys():
            time_str = f"{int(value['Hours'])}h {int(value['Minutes'])}m {int(value['Seconds'])}s"
            parts.append(f"{key_clean}: {time_str}")

        # Nếu là servings {Value, Unit}
        elif isinstance(value, dict) and {"Value", "Unit"} <= value.keys():
            parts.append(f"{key_clean}: {value['Value']} {value['Unit']}")

        # Nếu là dict khác
        elif isinstance(value, dict):
            inner = " ".join(f"{k}: {v}" for k, v in value.items())
            parts.append(f"{key_clean}: {inner}")

        # Nếu là giá trị thường
        else:
            parts.append(f"{key_clean}: {value}")

    return ", ".join(parts)


def chunk_by_recipe(input_file, output_file):
    """Mỗi công thức là 1 chunk, không còn dấu {}."""
    with open(input_file, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    chunks = []

    for i, recipe in enumerate(tqdm(recipes, desc="Chunking recipes"), start=1):
        url = recipe.get("URL", "")
        name = extract_recipe_name(url)
        summary = recipe.get("Summary", "")
        metadata = recipe.get("Metadata", {})
        ingredients = recipe.get("Ingredients", [])
        instructions = recipe.get("Instructions", [])

        # Format metadata
        metadata_str = format_metadata(metadata) if metadata else "N/A"

        # Gộp các phần thành đoạn văn hoàn chỉnh
        text_parts = [
            f"Recipe: {name}",
            f"Summary: {summary}",
            f"Metadata: {metadata_str}",
            "Ingredients: " + ", ".join(ingredients) if ingredients else "Ingredients: N/A",
            "Instructions: " + " ".join(instructions) if instructions else "Instructions: N/A"
        ]

        chunk_text = "\n".join(text_parts)

        chunks.append({
            "Chunk_ID": i,
            "Recipe_Name": name,
            "Source_URL": url,
            "Text": chunk_text
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"✅ Hoàn thành! Đã tạo {len(chunks)} chunks → {output_file}")


if __name__ == "__main__":
    input_path = "F:/AI/processed_Data.json"          # file của em
    output_path = "F:/AI/chunking_food.json"
    chunk_by_recipe(input_path, output_path)

         # file đầu ra

