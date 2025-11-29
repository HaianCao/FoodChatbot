# Food Chatbot - Module Bot 🤖🍽️

## Mô tả dự án

Food Chatbot là một ứng dụng trí tuệ nhân tạo tiên tiến được phát triển để tư vấn về thực phẩm và dinh dưỡng. Sử dụng công nghệ RAG (Retrieval-Augmented Generation) kết hợp với Google Gemini AI và ChromaDB, ứng dụng cung cấp thông tin chính xác và hữu ích về các công thức nấu ăn.

### 🎯 Tính năng chính

- **Tìm kiếm công thức thông minh**: Tìm kiếm các món ăn theo tên, thành phần, hoặc yêu cầu dinh dưỡng
- **Hỗ trợ đa ngôn ngữ**: Phát hiện và dịch tự động giữa tiếng Việt và tiếng Anh
- **Lọc theo dinh dưỡng**: Tìm món ăn theo lượng calo, protein, carb, chất béo, v.v.
- **Giao diện web thân thiện**: Chat interface với thiết kế responsive
- **Conversation Context**: Hiểu và trả lời các câu hỏi liên quan đến cuộc trò chuyện trước
- **Chỉ sử dụng dữ liệu cơ sở dữ liệu**: Đảm bảo thông tin chính xác từ nguồn dữ liệu đáng tin cậy

## 📁 Cấu trúc thư mục

```
bot/
├── src/
│   ├── chatbotfood/           # Core chatbot logic
│   │   ├── __init__.py
│   │   ├── chatbot.py         # Orchestrator chính
│   │   ├── chroma_manager.py  # Quản lý vector database
│   │   ├── config.py          # Cấu hình ứng dụng
│   │   ├── gemini_client.py   # Tích hợp Google Gemini AI
│   │   ├── prompts.py         # Templates cho AI prompts
│   │   └── schemas.py         # Data validation schemas
│   └── web/
│       ├── __init__.py
│       ├── server.py          # Flask web server
│       └── static/            # HTML, CSS, JavaScript files
├── chroma_db/                 # ChromaDB vector database
├── main.py                    # Entry point chính
├── processed_data.json        # Dữ liệu công thức đã xử lý
└── README.md                  # Tệp này.
```

## 🚀 Cài đặt và chạy ứng dụng

### 1. Cấu hình API Key

Tạo file `.env` trong thư mục `bot/` và thêm hằng số API Google Gemini:

```env
GEMINI_API_KEY="API_KEY_HERE"
```

Để lấy API_KEY, làm theo các bước sau:
- Truy cập https://aistudio.google.com/apps
- Vào **Get API Key**
- Vào **Create API Key**, đặt tên và chọn project được import là Gemini API
- Sau khi tạo xong sẽ có phần API Key, sao chép giá trị này vào `API_KEY_HERE`

### 2. Chạy ứng dụng
Sau khi đã thiết lập xong môi trường ảo (Hướng dẫn tại https://github.com/HaianCao/FoodChatbot/blob/main/README.md)

```bash
cd bot

python main.py
```

Ứng dụng sẽ khởi động tại: `http://localhost:5000`, truy cập đường dẫn này trên brower và tương tác với chatbot thông qua giao diện chat
