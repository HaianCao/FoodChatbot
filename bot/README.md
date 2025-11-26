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
├── chatbot_env/              # Virtual environment
├── main.py                   # Entry point chính
├── requirements.txt          # Python dependencies
└── processed_data.json       # Dữ liệu công thức đã xử lý
```

## 🚀 Cài đặt và chạy ứng dụng

### Yêu cầu hệ thống

- Python 3.8+
- Google AI API key
- 4GB RAM (khuyến nghị)
- Kết nối internet

### 1. Chuẩn bị môi trường

```bash
# Clone repository
git clone <repository-url>
cd bot

# Tạo virtual environment
python -m venv chatbot_env

# Kích hoạt virtual environment
# Windows
chatbot_env\Scripts\activate
# Linux/Mac
source chatbot_env/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cấu hình API Key

Tạo file `.env` trong thư mục `bot/`:

```env
GEMINI_API_KEY=your_google_ai_api_key_here
```

### 3. Chạy ứng dụng

```bash
python main.py
```

Ứng dụng sẽ khởi động tại: `http://localhost:5000`

## 🏗️ Kiến trúc hệ thống

### RAG (Retrieval-Augmented Generation) Pipeline

1. **Input Processing**: Phát hiện ngôn ngữ và dịch sang tiếng Anh
2. **Query Rewriting**: Xử lý các truy vấn mơ hồ với context cuộc trò chuyện
3. **Filter Generation**: Chuyển đổi ngôn ngữ tự nhiên thành filter ChromaDB
4. **Vector Search**: Tìm kiếm semantic trong cơ sở dữ liệu công thức
5. **Context Preparation**: Định dạng dữ liệu cho AI model
6. **Response Generation**: Tạo phản hồi bằng Gemini AI
7. **Translation**: Dịch phản hồi về ngôn ngữ gốc của người dùng

### Các thành phần chính

#### 1. ChatBot (`chatbot.py`)

- **Chức năng**: Orchestrator chính điều phối toàn bộ quy trình
- **Tính năng**: Xử lý conversation context, RAG pipeline, quản lý session

#### 2. GeminiClient (`gemini_client.py`)

- **Chức năng**: Tích hợp với Google Gemini AI API
- **Tính năng**: Translation, query rewriting, filter generation, response generation

#### 3. ChromaDBManager (`chroma_manager.py`)

- **Chức năng**: Quản lý vector database và tìm kiếm
- **Tính năng**: Vector search, metadata filtering, sorting, RAG context preparation

#### 4. Web Server (`server.py`)

- **Chức năng**: Flask web server với REST API
- **Endpoints**:
  - `POST /chat` - Chat với bot
  - `POST /reset` - Reset conversation
  - `GET /` - Giao diện web

## 📝 API Documentation

### POST /chat

Gửi tin nhắn tới chatbot.

**Request Body:**

```json
{
  "message": "Tìm món ăn ít calo"
}
```

**Response:**

```json
{
  "response": "Đây là 10 món ăn ít calo nhất:\n1. **Salad rau xanh** - 50 kcal - Tươi mát với rau mixed\n2. **Canh chua cá** - 120 kcal - Thanh mát, giàu vitamin...",
  "sources": [
    {
      "title": "Salad rau xanh",
      "url": "https://example.com/salad",
      "calories": 50
    }
  ]
}
```

### POST /reset

Reset conversation context.

**Response:**

```json
{
  "message": "Conversation reset successfully"
}
```

## 🔧 Cấu hình nâng cao

### config.py

```python
# Cơ sở dữ liệu
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "crawler" / "data"
PROCESSED_DATA_PATH = BASE_DIR / "bot" / "processed_data.json"
CHROMA_PERSIST_PATH = BASE_DIR / "bot" / "chroma_db"

# RAG Configuration
COLLECTION_NAME = "recipes"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MIN_RELEVANCE_SCORE = 0.4
MAX_RESULTS = 50
```

### Prompts tùy chỉnh

Chỉnh sửa `prompts.py` để tùy chỉnh behavior của AI:

- `get_translation_prompt()`: Cấu hình dịch thuật
- `get_query_rewrite_prompt()`: Logic xử lý query mơ hồ
- `get_filter_generation_prompt()`: Tạo filter từ ngôn ngữ tự nhiên
- `get_rag_prompt()`: Format phản hồi RAG

## 🎨 Giao diện người dùng

### Thiết kế responsive

- **Desktop**: Layout 2 cột với sidebar và chat area
- **Mobile**: Layout stack với navigation drawer
- **Tablet**: Hybrid layout tự động điều chỉnh

### Tính năng UI

- **Real-time typing indicator**: Hiển thị khi bot đang typing
- **Message formatting**: Hỗ trợ Markdown, lists, links
- **Reset button**: Nút reset conversation trong header
- **Auto-scroll**: Tự động cuộn xuống tin nhắn mới
- **Error handling**: Thông báo lỗi thân thiện

## 🐛 Xử lý lỗi và Debug

### Logging

Ứng dụng sử dụng Python logging với các level:

- `INFO`: Thông tin hoạt động bình thường
- `WARNING`: Cảnh báo không ảnh hưởng chức năng
- `ERROR`: Lỗi cần xử lý

### Lỗi thường gặp

1. **API Key không hợp lệ**

   ```
   ⚠️  Translation failed: Invalid API key
   ```

   **Giải pháp**: Kiểm tra GEMINI_API_KEY trong .env

2. **ChromaDB không khởi tạo được**

   ```
   ⚠️  ChromaDB initialization failed
   ```

   **Giải pháp**: Kiểm tra quyền truy cập thư mục chroma_db/

3. **Không tìm thấy recipes**
   ```
   ⚠️  No recipes found matching the query
   ```
   **Giải pháp**: Kiểm tra processed_data.json và database content

## 📄 License

Dự án này được phát triển cho mục đích học tập tại VNU-HUS.

## 👥 Tác giả

**FoodChatbot Team - Group 9**

- **Mô học**: Nhập môn Trí tuệ Nhân tạo - VNU-HUS
- **Kỳ học**: Kỳ 1
- **Năm học**: 2025-2026
