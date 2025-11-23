import json
import re
import os
import zipfile  
from pathlib import Path
from tqdm import tqdm 
import unicodedata



INPUT_ZIP_FILE = "c:/Users/Windows/Downloads/foods-20251025T115332Z-1-001.zip"     
OUTPUT_JSON_FILE = "c:/Users/Windows/Downloads/processed_Data.json" 
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


def preprocess_simple_text(value):
    """Return a safe stripped string for simple fields (URL, Summary)."""
    if value is None:
        return ""
    try:
        return str(value).strip()
    except Exception:
        return ""
        # Replace the existing REPLACEMENT_REGEX with a proxy that first
        # converts mixed numbers like "1 1/2" or "1-1/2" into improper fractions "3/2",
        # then delegates to the original REPLACEMENT_REGEX.sub(...) behavior.
        _mixed_fraction_re = re.compile(
            r'(?P<sign>-?)\s*'                             # optional sign
            r'(?P<whole>\d+)\s*'                           # whole number
            r'(?:[-\u2014\u2013–—]\s*|\s+)'                # separator: dash or whitespace
            r'(?P<num>\d+)\s*[\u2044/]\s*(?P<den>\d+)',    # numerator, fraction slash, denominator
            flags=re.UNICODE
        )

        def _mixed_repl(m):
            try:
                sign = -1 if m.group('sign') == '-' else 1
                whole = int(m.group('whole'))
                num = int(m.group('num'))
                den = int(m.group('den'))
                if den == 0:
                    return m.group(0)  # leave as-is if invalid
                new_num = whole * den + num
                new_num *= sign
                return f"{new_num}/{den}"
            except Exception:
                return m.group(0)

        class _ReplacementProxy:
            def __init__(self, original_regex):
                self._orig = original_regex

            def sub(self, repl, text):
                # First convert mixed numbers to improper fractions
                try:
                    text = _mixed_fraction_re.sub(_mixed_repl, text)
                except Exception:
                    pass
                # Then run the original replacements (the provided repl expects the original regex)
                return self._orig.sub(repl, text)

        # If REPLACEMENT_REGEX exists, wrap it; otherwise no-op.
        try:
            REPLACEMENT_REGEX = _ReplacementProxy(REPLACEMENT_REGEX)
        except NameError:
            # If REPLACEMENT_REGEX isn't defined yet, create a proxy stub that will be replaced later.
            class _DelayedProxy:
                def __init__(self):
                    self._orig = None
                def set_original(self, orig):
                    self._orig = orig
                def sub(self, repl, text):
                    if self._orig is None:
                        return text
                    text = _mixed_fraction_re.sub(_mixed_repl, text)
                    return self._orig.sub(repl, text)
            # expose a delayed proxy; later code that sets REPLACEMENT_REGEX should set the original via:
            # REPLACEMENT_REGEX.set_original(actual_regex)
            REPLACEMENT_REGEX = _DelayedProxy()
# Map common single-character vulgar fractions to ASCII form
_VULGAR_FRACTION_MAP = {
    '½': '1/2', '⅓': '1/3', '⅔': '2/3', '¼': '1/4', '¾': '3/4',
    '⅕': '1/5', '⅖': '2/5', '⅗': '3/5', '⅘': '4/5',
    '⅙': '1/6', '⅚': '5/6', '⅐': '1/7', '⅛': '1/8', '⅜': '3/8',
    '⅝': '5/8', '⅞': '7/8', '⅑': '1/9', '⅒': '1/10'
}
_VULGAR_RE = re.compile('|'.join(re.escape(k) for k in sorted(_VULGAR_FRACTION_MAP.keys(), key=len, reverse=True)))

# Pattern to normalize digit⟂digit or digit/ digit uses the fraction slash (U+2044) or normal slash
_DIGIT_FRACTION_PATTERN = re.compile(r'(\d+)\s*[\u2044/]\s*(\d+)')

def normalize_text(text):
    # Chuẩn hóa văn bản: unicode, chuyển đổi phân số thô sang ASCII, thu gọn  các khoảng trắng
    if text is None:
        return ""
    if not isinstance(text, str):   
        text = str(text)

    # Chuẩn hóa Unicode
    text = unicodedata.normalize('NFC', text)

    # Thay thế các ký tự tùy chỉnh
    try:
        text = REPLACEMENT_REGEX.sub(lambda m: CUSTOM_REPLACEMENTS[m.group(0)], text)
    except Exception:
        pass

    # Thay thế các phân số thô bằng bản ASCII tương ứng
    text = _VULGAR_RE.sub(lambda m: _VULGAR_FRACTION_MAP[m.group(0)], text)

    # Chuẩn hóa phân số bằng cách sử dụng các dấu gạch chéo
    text = _DIGIT_FRACTION_PATTERN.sub(r'\1/\2', text)
    
    # Remove control chars and zero-width spaces
    text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')

    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def preprocess_string_list(str_list):
    """Làm sạch các trường là danh sách chuỗi (Ingredients, Instructions)."""
    if not isinstance(str_list, list):
        return []
    
    cleaned_list = []
    for item in str_list:
        if isinstance(item, str):
            # Chỉ thêm vào nếu chuỗi không rỗng sau khi làm sạch
            cleaned_item = normalize_text(item.strip())
            if cleaned_item:
                cleaned_list.append(cleaned_item)
    return cleaned_list

def preprocess_metadata(metadata_list):
    """
    Tái cấu trúc trường Metadata từ mảng chuỗi thành một đối tượng (object).
    Chuẩn hóa thời gian về đơn vị 'phút'.
    """
    if not isinstance(metadata_list, list):
        return {}
        
    processed_meta = {}
    
    for item in metadata_list:
        item = normalize_text(item) # Chuẩn hóa trước khi xử lý
        if not isinstance(item, str) or ':' not in item:
            continue
            
        try:
            raw_key, raw_value = item.split(':', 1)
            key = raw_key.strip().lower().replace(' ', '_')
            value_str = raw_value.strip()
            
            # Trích xuất số đầu tiên tìm thấy
            num_match = re.search(r'(\d+(\.\d+)?)', value_str)
            num_value = None
            if num_match:
                num_value = float(num_match.group(1))
                if num_value.is_integer():
                    num_value = int(num_value)

            # Xử lý logic riêng cho thời gian và khẩu phần
            if 'time' in key:
                # Nếu giá trị có "hour", nhân số lên 60
                if 'hour' in value_str.lower() and num_value is not None:
                    num_value = num_value * 60
                # Thêm hậu tố _minutes để làm rõ đơn vị
                processed_meta[f"{key}_minutes"] = num_value
            elif 'servings' in key:
                processed_meta[key] = num_value
            else:
                # Cho các trường hợp khác
                processed_meta[key] = num_value if num_value is not None else value_str

        except ValueError:
            continue # Bỏ qua nếu dòng bị lỗi
            
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

# Chạy hàm main khi script được thực thi
if __name__ == "__main__":
    main()