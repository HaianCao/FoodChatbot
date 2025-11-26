# Tiền Xử Lý Dữ Liệu Món Ăn 🍲

## Mô tả

Module này cung cấp pipeline mạnh mẽ để làm sạch, chuẩn hóa và tái cấu trúc dữ liệu công thức nấu ăn thô, phục vụ cho các ứng dụng chatbot và học máy.

## 🎯 Tính năng chính

- Đọc dữ liệu zip chứa nhiều file JSON công thức
- Làm sạch, chuẩn hóa văn bản, chuyển đổi ký tự đặc biệt, phân số
- Chuẩn hóa metadata, dinh dưỡng, bình luận
- Xuất ra một file JSON duy nhất, sẵn sàng cho AI/chatbot sử dụng

## 📁 Cấu trúc thư mục

```
preprocessing/
├── food_preprocessing.py      # Script chạy chính
├── constants.py              # Hằng số, regex, mapping ký tự
├── text_cleaning.py          # Hàm chuẩn hóa, làm sạch text
├── metadata.py               # Xử lý metadata, dinh dưỡng
├── comments.py               # Xử lý bình luận
├── io_utils.py               # Đọc/ghi file, điều phối pipeline
├── data/                     # Chứa file zip đầu vào (foods.zip)
├── preprocessed_data.json    # File kết quả đầu ra
```

## 🚀 Hướng dẫn sử dụng

### 1. Chuẩn bị dữ liệu đầu vào

- Đặt file zip dữ liệu công thức vào `preprocessing/data/foods.zip`

### 2. Chạy tiền xử lý

- Mở terminal tại thư mục `preprocessing` và chạy:

```bash
python food_preprocessing.py
```

- Script sẽ xử lý toàn bộ file JSON trong zip và xuất ra `preprocessed_data.json`

### 3. Kết quả

- File `preprocessed_data.json` chứa toàn bộ công thức đã được làm sạch, chuẩn hóa, tái cấu trúc.

## 🛠️ Yêu cầu

- Python 3.7+
- Thư viện: tqdm

Cài đặt nhanh:

```bash
pip install tqdm
```

## 🏗️ Mô tả các file chính

- **food_preprocessing.py**: Điểm vào pipeline, gọi các bước xử lý
- **constants.py**: Đường dẫn, mapping ký tự, regex
- **text_cleaning.py**: Chuẩn hóa, làm sạch text, ký tự đặc biệt
- **metadata.py**: Chuẩn hóa metadata, dinh dưỡng
- **comments.py**: Chuẩn hóa bình luận
- **io_utils.py**: Đọc zip, ghi file, điều phối pipeline

## ⚙️ Tuỳ chỉnh

- Đổi đường dẫn input/output: sửa `INPUT_ZIP_FILE`, `OUTPUT_JSON_FILE` trong `constants.py`
- Thêm quy tắc làm sạch: cập nhật `CUSTOM_REPLACEMENTS` trong `constants.py` hoặc mở rộng hàm ở `text_cleaning.py`

## 🐛 Xử lý lỗi thường gặp

1. **Không tìm thấy file zip đầu vào**
   - Kiểm tra lại đường dẫn `preprocessing/data/foods.zip`
2. **Lỗi giải nén zip**
   - Đảm bảo file zip hợp lệ, không bị lỗi
3. **Lỗi ghi file đầu ra**
   - Kiểm tra quyền ghi thư mục, dung lượng ổ đĩa

## 📄 Bản quyền

Dự án phục vụ học tập tại VNU-HUS.

## 👥 Tác giả

**FoodChatbot Team - Nhóm 9**

- Môn: Nhập môn Trí tuệ Nhân tạo - VNU-HUS
- Kỳ 1, Năm học 2025-2026
