import json
import os
from tqdm import tqdm
from pathlib import Path
from urllib.parse import urlparse # Thư viện để phân tích URL

# --- CẤU HÌNH ---
# Tên tệp đầu vào (tệp đã xử lý từ các bước trước)
INPUT_FILE = "c:/Users/Windows/Downloads/processed_data.json" 
# Tên tệp đầu ra (mỗi phần tử là một món ăn hoàn chỉnh)
OUTPUT_FILE = "c:/Users/Windows/Downloads/chunk.json" 
# --------------------

def extract_dish_name(url: str) -> str:
    """
    Trích xuất tên món ăn có thể đọc được từ URL.
    Ví dụ: 'https://.../zucchini-pizza/' -> 'Zucchini Pizza'
    """
    if not url:
        return "Unknown Dish"
    try:
        # Phân tích URL để lấy phần path
        path = urlparse(url).path
        
        # Lấy phần cuối cùng của path và loại bỏ dấu gạch chéo
        slug = path.strip('/') 
        if not slug:
             return "Unknown Dish"
             
        # Xử lý trường hợp path có nhiều cấp (ví dụ: /category/dish-name)
        if '/' in slug:
            slug = slug.split('/')[-1]

        # Chuyển 'zucchini-pizza' thành 'Zucchini Pizza'
        name = slug.replace('-', ' ').title()
        return name
    except Exception:
        return "Unknown Dish"

def format_recipe_to_text(recipe: dict) -> tuple[str, dict]:
    """
    Gộp tất cả các trường của một công thức thành một chuỗi văn bản duy nhất.
    Đồng thời trả về metadata.
    """
    
    url = recipe.get('URL', '')
    dish_name = extract_dish_name(url)
    
    # Metadata cho chunk này
    metadata = {
        "url": url,
        "dish_name": dish_name
    }
    
    # Mảng chứa các phần văn bản
    content_parts = []
    
    # 1. Tên món ăn (Thêm vào đầu để dễ nhận diện)
    content_parts.append(f"Tên món ăn: {dish_name}")

    # 2. Tóm tắt
    if summary := recipe.get('Summary'):
        content_parts.append(f"Tóm tắt: {summary}")
        
    # 3. Metadata (Thời gian, Khẩu phần)
    if metadata_obj := recipe.get('Metadata'):
        meta_lines = ["Thông tin chung:"]
        for key, value in metadata_obj.items():
            if value is not None:
                readable_key = key.replace('_', ' ').title()
                meta_lines.append(f"- {readable_key}: {value}")
        content_parts.append("\n".join(meta_lines))

    # 4. Nguyên liệu
    if ingredients := recipe.get('Ingredients', []):
        ingredient_lines = ["Nguyên liệu:"]
        for item in ingredients:
            ingredient_lines.append(f"- {item}")
        content_parts.append("\n".join(ingredient_lines))

    # 5. Hướng dẫn
    if instructions := recipe.get('Instructions', []):
        instruction_lines = ["Hướng dẫn:"]
        for i, step in enumerate(instructions):
            instruction_lines.append(f"{i + 1}. {step}")
        content_parts.append("\n".join(instruction_lines))

    # 6. Bình luận
    if comments := recipe.get('Comments', []):
        comment_lines = ["Bình luận:"]
        for comment in comments:
            author = comment.get('author') or "Ẩn danh"
            text = comment.get('text', '')
            comment_lines.append(f"- {author} nói: {text}")
        content_parts.append("\n".join(comment_lines))
        
    # Gộp tất cả các phần lại, cách nhau bằng hai dấu xuống dòng
    full_text = "\n\n".join(content_parts)
    
    return full_text, metadata

def main():
    """
    Hàm chính: Đọc dữ liệu đã xử lý, gộp mỗi công thức thành một chunk
    và lưu lại.
    """
    
    # Danh sách chứa các chunk (mỗi chunk là 1 món ăn)
    all_recipe_chunks = []
    
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)
    
    # --- 1. ĐỌC TỆP DỮ LIỆU ĐÃ XỬ LÝ ---
    if not input_path.exists():
        print(f"Lỗi: Không tìm thấy tệp đầu vào '{INPUT_FILE}'.")
        return
        
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            recipes_data = json.load(f)
    except Exception as e:
        print(f"Lỗi khi đọc tệp '{INPUT_FILE}': {e}")
        return
        
    if not isinstance(recipes_data, list):
        print("Lỗi: Dữ liệu đầu vào không phải là một danh sách.")
        return

    print(f"Đã đọc {len(recipes_data)} công thức từ '{INPUT_FILE}'. Bắt đầu gộp...")

    # --- 2. LẶP QUA TỪNG CÔNG THỨC VÀ GỘP ---
    for recipe in tqdm(recipes_data, desc="Gộp các công thức"):
        
        # Gộp toàn bộ công thức thành 1 văn bản và lấy metadata
        content, metadata = format_recipe_to_text(recipe)
        
        # Nếu không có nội dung thì bỏ qua
        if not content:
            continue
            
        # Tạo chunk mới
        chunk = {
            "content": content,
            "metadata": metadata
        }
        all_recipe_chunks.append(chunk)
                    
    # --- 3. GHI KẾT QUẢ RA TỆP JSON MỚI ---
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_recipe_chunks, f, indent=2, ensure_ascii=False)
            
        print("\n--- HOÀN THÀNH ---")
        print(f"Đã gộp và lưu {len(all_recipe_chunks)} công thức (chunk).")
        print(f"Dữ liệu đã lưu vào: {output_path.resolve()}")

    except Exception as e:
        print(f"Lỗi khi ghi tệp đầu ra: {e}")

# Chạy hàm main khi script được thực thi
if __name__ == "__main__":
    main()