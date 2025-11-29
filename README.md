# 🤖 Báo cáo Bài tập nhóm Môn Trí tuệ Nhân tạo

**📋 Thông tin:**

- **📚 Môn học:** MAT1207E - Nhập môn Trí tuệ Nhân tạo
- **📅 Học kỳ:** Học kỳ 1 - 2025-2026
- **🏫 Trường:** VNU-HUS (Đại học Quốc gia Hà Nội - Trường Đại học Khoa học Tự nhiên)
- **📝 Tiêu đề:** Chatbot ẩm thực
- **📅 Ngày nộp:**
- **📄 Báo cáo PDF:** https://github.com/HaianCao/FoodChatbot/blob/main/LaTeX%20Template/main-vi.pdf
- **🖥️ Slide thuyết trình:** 🖥️ [Liên kết tới slide thuyết trình trong kho lưu trữ này]
- **📂 Kho lưu trữ:** 📁 Bao gồm mã nguồn, dữ liệu và tài liệu (hoặc dẫn link ngoài nếu cần)

**👥 Thành viên nhóm:**

| 👤 Họ và tên    | 🆔 Mã sinh viên | 🐙 Tên GitHub | 🛠️ Đóng góp                       |
| --------------- | --------------- | ------------- | --------------------------------- |
| Cao Hải An      | 23001818        | HaianCao      | Xây dựng pipeline chatbot         |
| Đặng Thế Anh    | 23001821        | DangTAnh      | Thu thập dữ liệu                  |
| Phạm Minh Cương | 23001840        | mcnb2005      | Phát triển giao diện web          |
| Đỗ Minh Đức     | 23001864        | minhhhduc     | Xây dựng module truy xuất dữ liệu |
| Phạm Nhật Quang | 23001920        | NhatquangPham | Tiền xử lý dữ liệu                |

---

## 📑 Giới thiệu

Dự án xây dựng một **chatbot ẩm thực thông minh** có khả năng:

- Gợi ý món ăn theo sở thích và nguyên liệu
- Cung cấp công thức nấu ăn chi tiết
- Phân tích hương vị, dinh dưỡng
- Cá nhân hóa dựa trên hạn chế và sở thích của người dùng

Hệ thống sử dụng mô hình **RAG (Retrieval-Augmented Generation)** kết hợp LLM Gemini và cơ sở dữ liệu vector từ ChromaDB.

## ⚙️ Triển khai

### 🔍 Pipeline chính

1. **Crawl dữ liệu** từ website công thức nấu ăn
2. **Tiền xử lý dữ liệu:** làm sạch, phân tích cấu trúc, chuẩn hóa
3. **Sinh embeddings:** biểu diễn công thức dưới dạng vector
4. **Lưu trữ VectorDB:** ChromaDB với HNSW + cosine similarity
5. **Truy vấn RAG:**  
   - Nhận câu hỏi từ người dùng  
   - Semantic search → tìm món phù hợp  
   - Tạo phản hồi tự nhiên qua LLM và context retrieved

### 🛠️ Công nghệ sử dụng
- **Selenium** (Crawl)
- **Gemini API** (LLM)
- **ChromaDB** (Vector Database)
- **Python + Flask** (Backend)
- **HTML/CSS/JS** (Frontend chat)

## 📂 Cấu trúc dự án

```plaintext
FoodChatbot/
├── crawler/             # Thu thập dữ liệu
├── preprocessing/       # Làm sạch & chuẩn hóa
├── bot/               
│   ├── src/chatbotfood/ # Chatbot RAG + Backend
│   ├── src/web/         # Trang web để chat
|   └── main.py          # File chính chạy chatbot
├── LaTeX Template/      # Mẫu báo cáo
├── Proposed Topic Template.md 
└── README.md            # Mô tả dự án
```

## 🚀 Cài đặt môi trường
- Cài đặt phiên bản **Python 3.10** trở lên

```bash
cd FoodChatbot

python -m venv venv

# Nếu sử dụng Linux/Mac
source venv/bin/activate 

# Nếu sử dụng Windows
venv\Scripts\activate 

pip install -r requirements.txt
```

Sau khi đã cài đặt xong môi trường, xem tiếp hướng dẫn chạy file trong các file `README.md` của từng module nhỏ

## Tài liệu tham khảo & Phụ lục

**📚 Tài liệu tham khảo**

- Vaswani, Ashish et al. – Attention Is All You Need - DOI: 10.48550/arXiv.1706.03762
- The ML Tech Lead! – Understanding the Self-Attention Mechanism in 8 min - YouTube: https://www.youtube.com/watch?v=W28LfOld44Y
- The ML Tech Lead! – The Multi-head Attention Mechanism Explained! - YouTube: https://www.youtube.com/watch?v=W6s9i02EiR0&t=34s
- Dan Jurafsky & James H. Martin – Speech and - - Language Processing (3rd Edition Draft, 2023) - Link: https://web.stanford.edu/~jurafsky/slp3/
- Google Research – Gemini 1.5 Technical Report - DOI: 10.48550/arXiv.2403.05530
- Google Research – Gemini 2.5 Technical Report - DOI: 10.48550/arXiv.2507.06261
- Google Research – GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints - DOI: 10.48550/arXiv.2305.13245

**Hướng dẫn sử dụng**: được đặt trong từng thư mục nhỏ hơn của từng module.

### ✅ Danh sách kiểm tra trước khi nộp

- [x] ✅ Đánh dấu X vào ô để xác nhận hoàn thành
- [x] ✍️ Điền đầy đủ các mục trong mẫu README này
- [x] 📄 Hoàn thiện báo cáo PDF chi tiết theo cấu trúc trên
- [x] 🎨 Tuân thủ định dạng và nội dung theo hướng dẫn giảng viên
- [x] ➕ Thêm các mục riêng của dự án nếu cần
- [x] 🔍 Kiểm tra lại ngữ pháp, diễn đạt và độ chính xác kỹ thuật
- [x] ⬆️ Tải lên báo cáo PDF, slide trình bày và mã nguồn
- [x] 🧩 Đảm bảo tất cả mã nguồn được tài liệu hóa đầy đủ với bình luận và docstring
- [x] 🔗 Kiểm tra các liên kết và tài liệu tham khảo hoạt động đúng
