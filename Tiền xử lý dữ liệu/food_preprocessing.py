import json
import re
import os
import zipfile  
from pathlib import Path
from tqdm import tqdm 
import unicodedata



INPUT_ZIP_FILE = "F:/Download/foods-20251026T022057Z-1-001.zip"     
OUTPUT_JSON_FILE = "F:/AI/processed_Data.json" 
CUSTOM_REPLACEMENTS = {
    '°C': ' deg C',  # (Phải đặt trước '°')
    '°F': ' deg F',  # (Phải đặt trước '°')
    '°': ' degrees', # Ký hiệu độ nói chung
    '–': '-',        # en-dash
    '—': '-',        # em-dash
    '™': '(TM)',
    '®': '(R)',
    '©': '(C)',
    # Bạn có thể thêm bất kỳ ký hiệu nào bạn phát hiện ra ở đây
}
replacement_keys = sorted(CUSTOM_REPLACEMENTS.keys(), key=len, reverse=True)
REPLACEMENT_REGEX = re.compile('|'.join(re.escape(k) for k in replacement_keys))

def normalize_text(text: str) -> str: 
    if not isinstance(text, str) or not text:
        return text
        
    # Bước 1: Chuẩn hóa NFKC (Compatibility Decomposition)
    # Đây là bước "thần kỳ" tự động chuyển:
    # '½' -> '1/2'
    # '⅓' -> '1/3'
    # '²' -> '2' (số mũ)
    try:
        text = unicodedata.normalize('NFKC', text)
    except Exception:
        pass # Bỏ qua nếu có lỗi lạ với ký tự
        
    # Bước 2: Thay thế tùy chỉnh từ bản đồ
    # '10°C' -> '10 deg C'
    text = REPLACEMENT_REGEX.sub(lambda m: CUSTOM_REPLACEMENTS[m.group(0)], text)
    
    # Bước 3: Dọn dẹp khoảng trắng (do việc thay thế có thể tạo ra 2 dấu cách)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def preprocess_simple_text(text):
    """Làm sạch các trường văn bản đơn trị (URL, Summary)."""
    if isinstance(text, str):
        return text.strip()
    return text

def preprocess_string_list(str_list):
    """Làm sạch các trường là danh sách chuỗi (Ingredients, Instructions)."""
    if not isinstance(str_list, list):
        return []
    str_list = [convert_fraction_to_float(item) for item in str_list]
    cleaned_list = []
    for item in str_list:
        if isinstance(item, str):
            # Chỉ thêm vào nếu chuỗi không rỗng sau khi làm sạch
            cleaned_item = normalize_text(item.strip())
            if cleaned_item:
                cleaned_list.append(cleaned_item)
    return cleaned_list

import re

def preprocess_metadata(metadata_list):
    """
    Tái cấu trúc trường Metadata từ mảng chuỗi thành object.
    Với các trường thời gian, đổi sang dạng:
    "prep_time_minutes": { "Hours": ..., "Minutes": ..., "Seconds": ... }
    """
    if not isinstance(metadata_list, list):
        return {}

    processed_meta = {}

    for item in metadata_list:
        # Chuẩn hóa (nếu có hàm normalize_text)
        item = normalize_text(item)
        item = item.strip() if isinstance(item, str) else item
        if not isinstance(item, str) or ':' not in item:
            continue

        try:
            raw_key, raw_value = item.split(':', 1)
            key = raw_key.strip().lower().replace(' ', '_')
            value_str = raw_value.strip().lower()

            # --- Nếu là trường thời gian ---
            if 'time' in key:
                hours = minutes = seconds = 0

                # Tìm giờ, phút, giây bằng regex
                hour_match = re.search(r'(\d+)\s*hour', value_str)
                minute_match = re.search(r'(\d+)\s*minute', value_str)
                second_match = re.search(r'(\d+)\s*second', value_str)

                if hour_match:
                    hours = int(hour_match.group(1))
                if minute_match:
                    minutes = int(minute_match.group(1))
                if second_match:
                    seconds = int(second_match.group(1))

                processed_meta[f"{key}"] = {
                    "Hours": hours,
                    "Minutes": minutes,
                    "Seconds": seconds
                }

            # --- Nếu là khẩu phần (servings) ---
            elif 'servings' in key:
                num_match = re.search(r'(\d+(\.\d+)?)', value_str)
                unit_match = re.search(r'[a-zA-Z]+', value_str.split(str(num_match.group(1))[-1])[-1]) if num_match else None

                servings_value = float(num_match.group(1)) if num_match else None
                if servings_value and servings_value.is_integer():
                    servings_value = int(servings_value)

                unit = "servings"  # mặc định
                if unit_match:
                    unit = unit_match.group(0).strip().lower()

                processed_meta[key] = {
                    "Value": servings_value,
                    "Unit": unit
                }

            # --- Các trường khác ---
            else:
                num_match = re.search(r'(\d+(\.\d+)?)', value_str)
                if num_match:
                    num_value = float(num_match.group(1))
                    if num_value.is_integer():
                        num_value = int(num_value)
                    processed_meta[key] = num_value
                else:
                    processed_meta[key] = value_str

        except Exception:
            continue

    return processed_meta

def preprocess_nutrition(nutrition_list):
    """
    Tái cấu trúc trường Nutrition thành một đối tượng (object),
    với mỗi chất là một object con chứa {value, unit}.
    """
    if not isinstance(nutrition_list, list):
        return {}

    processed_nutrition = {}
    # Regex để trích xuất số (có thể là float/int) và đơn vị (vd: kcal, g, mg, IU, μg)
    pattern = re.compile(r'(-?[\d\.]+)\s*([\wμIU]+)?')
    
    for item in nutrition_list:
        item = normalize_text(item) # Chuẩn hóa trước khi xử lý
        if not isinstance(item, str) or ':' not in item:
            continue # Bỏ qua các chuỗi rỗng "" hoặc không hợp lệ
            
        try:
            raw_key, raw_value = item.split(':', 1)
            key = raw_key.strip().lower().replace(' ', '_')
            
            value_obj = {"value": None, "unit": None}
            match = pattern.search(raw_value.strip())
            
            if match:
                # Lấy giá trị số
                try:
                    num_val = float(match.group(1))
                    if num_val.is_integer():
                        num_val = int(num_val)
                    value_obj["value"] = num_val
                except (ValueError, TypeError):
                    pass # Giữ giá trị là None
                
                # Lấy đơn vị
                if match.group(2):
                    value_obj["unit"] = match.group(2)
            
            processed_nutrition[key] = value_obj
            
        except ValueError:
            continue # Bỏ qua nếu dòng bị lỗi
            
    return processed_nutrition

def preprocess_comments(comments_list):
    """
    Tái cấu trúc trường Comments từ mảng chuỗi thành
    một mảng các đối tượng (object) {author, text}.
    """
    if not isinstance(comments_list, list):
        return []
        
    processed_comments = []
    for item in comments_list:
        if not isinstance(item, str) or not item.strip():
            continue
            
        # ÁP DỤNG CHUẨN HÓA Ở ĐÂY
        item = normalize_text(item.strip()) # Chuẩn hóa toàn bộ chuỗi
        if not item:
            continue
        author = None
        text = item
        
        # Thử tách "Tác giả says: Nội dung"
        if ' says:' in item:
            try:
                parts = item.split(' says:', 1)
                if len(parts) == 2:
                    author = parts[0].strip()
                    text = parts[1].strip()
            except Exception:
                pass # Nếu lỗi, giữ nguyên text = item
        
        # Chỉ thêm comment nếu text có nội dung
        if text:
            processed_comments.append({"author": author, "text": text})
        
    return processed_comments

def main():
    """Hàm chính để đọc file .zip, xử lý, và ghi ra file .json duy nhất."""
    
    input_zip_path = Path(INPUT_ZIP_FILE)
    output_json_path = Path(OUTPUT_JSON_FILE)
    
    # 1. Tạo thư mục chứa file đầu ra nếu nó chưa tồn tại
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 2. Khởi tạo một danh sách lớn để chứa TẤT CẢ dữ liệu đã xử lý
    all_processed_data = []
    
    if not input_zip_path.exists():
        print(f"Lỗi: Không tìm thấy tệp .zip đầu vào tại: '{input_zip_path}'")
        return

    print(f"Đang đọc tệp .zip từ: {input_zip_path}")
    
    try:
        # 3. Mở tệp .zip để đọc
        with zipfile.ZipFile(input_zip_path, 'r') as zf:
            
            # Lọc ra chỉ những tệp .json
            json_files_in_zip = [f for f in zf.namelist() if f.endswith('.json') and not f.startswith('__')]
            
            if not json_files_in_zip:
                print(f"Lỗi: Không tìm thấy tệp .json nào bên trong '{input_zip_path}'")
                return

            print(f"Tìm thấy {len(json_files_in_zip)} tệp .json. Bắt đầu xử lý...")

            # 4. Lặp qua từng tệp .json bên trong .zip
            for file_name in tqdm(json_files_in_zip, desc="Đang xử lý JSON"):
                try:
                    # 5. Mở và đọc nội dung tệp từ trong .zip
                    with zf.open(file_name) as f:
                        content_str = f.read().decode('utf-8')
                        data = json.loads(content_str)
                    
                    # 6. Xử lý và tái cấu trúc dữ liệu
                    new_data = {
                        "URL": preprocess_simple_text(data.get('URL')),
                        "Summary": normalize_text(preprocess_simple_text(data.get('Summary'))), # Summary được chuẩn hóa
                        "Metadata": preprocess_metadata(data.get('Metadata', [])),
                        "Ingredients": preprocess_string_list(data.get('Ingredients', [])),
                        "Instructions": preprocess_string_list(data.get('Instructions', [])),
                        "Nutrition": preprocess_nutrition(data.get('Nutrition', [])),
                        "Comments": preprocess_comments(data.get('Comments', []))
                    }
                    
                    # 7. Thêm đối tượng JSON đã xử lý vào danh sách lớn
                    all_processed_data.append(new_data)
                    
                except json.JSONDecodeError:
                    print(f"Cảnh báo: Bỏ qua tệp bị lỗi JSON (không đọc được): {file_name}")
                except Exception as e:
                    print(f"Cảnh báo: Lỗi không xác định khi xử lý tệp {file_name}: {e}")

    except zipfile.BadZipFile:
        print(f"Lỗi: Tệp '{input_zip_path}' không phải là tệp .zip hợp lệ.")
        return
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy tệp '{input_zip_path}'.")
        return

    # 8. Ghi toàn bộ danh sách ra MỘT file .json duy nhất
    print(f"\nĐang ghi {len(all_processed_data)} đối tượng ra tệp JSON duy nhất...")
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            # Dòng quan trọng: Dùng json.dump để ghi danh sách ra file .json
            # indent=2 giúp file dễ đọc hơn
            json.dump(all_processed_data, f, indent=2, ensure_ascii=False)
            
        print("--- HOÀN THÀNH ---")
        print(f"Đã xử lý và lưu {len(all_processed_data)} công thức.")
        print(f"Kết quả đã được lưu tại:")
        print(f"{output_json_path.resolve()}")
        
    except Exception as e:
        print(f"Lỗi khi ghi tệp đầu ra: {e}")
    import re

# Bảng quy đổi phân số Unicode → giá trị thập phân
FRACTION_MAP = {
    "¼": 0.25,
    "½": 0.5,
    "¾": 0.75,
    "⅐": 1/7,
    "⅑": 1/9,
    "⅒": 0.1,
    "⅓": 1/3,
    "⅔": 2/3,
    "⅕": 0.2,
    "⅖": 0.4,
    "⅗": 0.6,
    "⅘": 0.8,
    "⅙": 1/6,
    "⅚": 5/6,
    "⅛": 0.125,
    "⅜": 0.375,
    "⅝": 0.625,
    "⅞": 0.875
}

def convert_fraction_to_float(text):
    """
    Chuyển các ký tự phân số (hoặc dạng '1 1/2') thành số thập phân.
    """
    # 1️⃣ Xử lý trường hợp Unicode (như ½, ⅓,...)
    for frac, val in FRACTION_MAP.items():
        text = text.replace(frac, f" {val}")  # thêm dấu cách để dễ xử lý sau

    # 2️⃣ Xử lý dạng "1 1/2" hoặc "2 3/4"
    def mixed_fraction_to_decimal(match):
        whole = float(match.group(1))
        numerator = float(match.group(2))
        denominator = float(match.group(3))
        return str(round(whole + numerator / denominator, 2))

    text = re.sub(r"(\d+)\s+(\d+)\/(\d+)", mixed_fraction_to_decimal, text)

    # 3️⃣ Xử lý dạng "3/4"
    def simple_fraction_to_decimal(match):
        numerator = float(match.group(1))
        denominator = float(match.group(2))
        return str(round(numerator / denominator, 2))

    text = re.sub(r"(\d+)\/(\d+)", simple_fraction_to_decimal, text)

    # Xóa khoảng trắng thừa
    return re.sub(r"\s+", " ", text.strip())


# Chạy hàm main khi script được thực thi
if __name__ == "__main__":
    main()
