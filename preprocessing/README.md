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
└── README.md                 # Tệp này.
```

## 🚀 Hướng dẫn sử dụng
Sau khi đã thiết lập xong môi trường ảo (Hướng dẫn tại https://github.com/HaianCao/FoodChatbot/blob/main/README.md)

### 1. Chuẩn bị dữ liệu đầu vào

- Đặt file zip dữ liệu công thức vào `preprocessing/data/foods.zip`

### 2. Chạy tiền xử lý

```bash
cd preprocessing

python food_preprocessing.py
```

- Script sẽ xử lý toàn bộ file JSON trong zip và xuất ra `preprocessed_data.json`

### 3. Kết quả

- File `preprocessed_data.json` chứa toàn bộ công thức đã được làm sạch, chuẩn hóa, tái cấu trúc.
