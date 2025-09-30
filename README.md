# 🤖 Báo cáo Bài tập nhóm Môn Trí tuệ Nhân tạo

**📋 Thông tin:**

- **📚 Môn học:** MAT1207E - Nhập môn Trí tuệ Nhân tạo
- **📅 Học kỳ:** Học kỳ 1 - 2025-2026
- **🏫 Trường:** VNU-HUS (Đại học Quốc gia Hà Nội - Trường Đại học Khoa học Tự nhiên)
- **📝 Tiêu đề:** Chatbot ẩm thực
- **📅 Ngày nộp:** 
- **📄 Báo cáo PDF:** 📄 [Liên kết tới báo cáo PDF trong kho lưu trữ này]
- **🖥️ Slide thuyết trình:** 🖥️ [Liên kết tới slide thuyết trình trong kho lưu trữ này]
- **📂 Kho lưu trữ:** 📁 Bao gồm mã nguồn, dữ liệu và tài liệu (hoặc dẫn link ngoài nếu cần)

**👥 Thành viên nhóm:**

| 👤 Họ và tên    | 🆔 Mã sinh viên | 🐙 Tên GitHub | 🛠️ Đóng góp  |
| --------------- | --------------- | ------------- | ------------ |
| Cao Hải An      | 23001818        | HaianCao      | [Đóng góp 1] |
| Đặng Thế Anh    | [Mã SV 2]       | [GitHub 2]    | [Đóng góp 2] |
| Phạm Minh Cương | 23001840        | mcnb2005      | [Đóng góp 3] |
| Đỗ Minh Đức     | 23001864        | minhhhduc     | [Đóng góp 3] |
| Phạm Nhật Quang | [Mã SV 3]       | [GitHub 3]    | [Đóng góp 3] |

---

## 📑 Tổng quan cấu trúc báo cáo

### Chương 1: Giới thiệu

**📝 Tóm tắt dự án**

- ✨ Dự án phát triển một chatbot ẩm thực thông minh sử dụng trí tuệ nhân tạo để hỗ trợ người dùng trong việc nấu ăn và khám phá các món ăn mới
- 🎯 Mục tiêu chính: Tạo ra một trợ lý ảo có thể cung cấp hướng dẫn nấu ăn chi tiết, đưa ra nhận xét và đánh giá về các món ăn một cách tự nhiên và hữu ích
- 🌟 Kết quả nổi bật: Chatbot có khả năng hiểu ngôn ngữ tự nhiên, cung cấp công thức nấu ăn phù hợp với nguyên liệu có sẵn và đưa ra lời khuyên ẩm thực cá nhân hóa

**❓ Bài toán đặt ra**

- 📌 **Vấn đề thực tiễn:** Trong cuộc sống hiện đại, nhiều người gặp khó khăn trong việc lựa chọn món ăn phù hợp, tìm kiếm công thức nấu ăn và nhận được lời khuyên ẩm thực tin cậy
- 🔍 **Thách thức kỹ thuật:** Xây dựng một hệ thống AI có khả năng:
  - Hiểu và xử lý các yêu cầu ẩm thực đa dạng bằng ngôn ngữ tự nhiên
  - Cung cấp hướng dẫn nấu ăn chi tiết, từng bước một cách rõ ràng và dễ hiểu
  - Đưa ra nhận xét khách quan về hương vị, dinh dưỡng và cách trình bày món ăn
  - Tùy chỉnh gợi ý dựa trên sở thích, hạn chế ăn uống và nguyên liệu có sẵn
- 💡 **Ý nghĩa thực tiễn:** Giúp người dùng tiết kiệm thời gian tìm kiếm công thức, nâng cao kỹ năng nấu ăn, khám phá ẩm thực mới và có những trải nghiệm ẩm thực phong phú hơn

### Chương 2: Phương pháp & Triển khai

**⚙️ Phương pháp**

- 🔍 **Cách tiếp cận:** Kết hợp mô hình ngôn ngữ lớn đã được pretrained với kiến trúc RAG (Retrieval-Augmented Generation) để tối ưu hóa độ chính xác và tính thực tiễn của chatbot ẩm thực

- 🧠 **Cơ sở lý thuyết:**

  - **Large Language Model (LLM):** Sử dụng mô hình pretrained có khả năng hiểu và sinh ngôn ngữ tự nhiên để xử lý câu hỏi và tạo phản hồi tự nhiên
  - **RAG Architecture:** Tăng cường khả năng của LLM bằng cách kết hợp thông tin từ cơ sở dữ liệu kiến thức bên ngoài
  - **Vector Database:** Lưu trữ và truy xuất thông tin ẩm thực dưới dạng vector embeddings để tìm kiếm ngữ nghĩa hiệu quả

- 🔧 **Thuật toán chính:**

  - **Embedding Generation:** Chuyển đổi công thức nấu ăn và thông tin món ăn thành vector embeddings
  - **Semantic Search:** Tìm kiếm thông tin liên quan dựa trên độ tương đồng cosine trong không gian vector
  - **Context Injection:** Kết hợp thông tin được truy xuất với prompt gốc để tạo context phong phú cho LLM
  - **Response Generation:** Sinh phản hồi tự nhiên dựa trên context được tăng cường

- 📊 **Dữ liệu sử dụng:**
  - Cơ sở dữ liệu công thức nấu ăn từ các nguồn uy tín (sách nấu ăn, website ẩm thực)
  - Thông tin dinh dưỡng, thành phần nguyên liệu và cách chế biến
  - Đánh giá và nhận xét về món ăn từ chuyên gia ẩm thực
  - Dữ liệu về sở thích và hạn chế ăn uống phổ biến

**💻 Triển khai**

- 🧩 **Kiến trúc hệ thống:**

  - **Frontend:** Giao diện chat tương tác thân thiện với người dùng
  - **API Layer:** Xử lý request và routing giữa các components
  - **RAG Engine:** Core logic kết hợp retrieval và generation
  - **Vector Database:** Lưu trữ embeddings và thực hiện similarity search
  - **LLM Integration:** Kết nối với mô hình pretrained (GPT, Claude, hoặc open-source models)

- 🛠️ **Công cụ và Framework:**

  - **Vector Database:** Pinecone, Weaviate, hoặc ChromaDB cho việc lưu trữ và truy xuất vector
  - **Embedding Models:** OpenAI Embeddings, Sentence-BERT, hoặc các mô hình embedding đa ngôn ngữ
  - **LLM Framework:** LangChain hoặc LlamaIndex để xây dựng RAG pipeline
  - **Backend:** Python với FastAPI hoặc Flask
  - **Frontend:** React.js hoặc Streamlit cho demo interface

- 📁 **Cấu trúc mã nguồn:**
  ```
  chatbot-cuisine/
  ├── data/                    # Dữ liệu thô và được xử lý
  ├── embeddings/              # Module tạo và quản lý embeddings
  ├── retrieval/               # Logic tìm kiếm và truy xuất thông tin
  ├── generation/              # Module sinh phản hồi từ LLM
  ├── api/                     # REST API endpoints
  ├── frontend/                # Giao diện người dùng
  ├── config/                  # Cấu hình hệ thống
  └── tests/                   # Unit tests và integration tests
  ```

### Chương 3: Kết quả & Phân tích

**📊 Kết quả & Thảo luận**

- 📈 Các phát hiện chính, chỉ số đánh giá và phân tích

### Chương 4: Kết luận

**✅ Kết luận & Hướng phát triển**

- 🔭 Tổng kết đóng góp và đề xuất cải tiến

### Tài liệu tham khảo & Phụ lục

**📚 Tài liệu tham khảo**

- 🔗 Danh sách bài báo, sách và nguồn tham khảo

**📎 Phụ lục** _(Tùy chọn)_

- 📎 Kết quả bổ sung, đoạn mã hoặc hướng dẫn sử dụng

---

## 📝 Hướng dẫn nộp bài

### 📋 Yêu cầu

- **Định dạng:**
  - 🖨️ Báo cáo phải được đánh máy, trình bày rõ ràng và xuất ra định dạng PDF (khuyến nghị dùng LaTeX).
  - 🔁 Một bản báo cáo cần lưu trên kho GitHub của dự án, hai bản nộp trên Canvas (một cho giảng viên, một cho trợ giảng), và hai bản in (một cho giảng viên, một cho trợ giảng). Slide trình bày cũng thực hiện tương tự (không cần bản in slides).
- **Kho lưu trữ:** 📂 Bao gồm báo cáo PDF, slide, toàn bộ mã nguồn và tài liệu liên quan. Nếu vượt quá giới hạn dung lượng của GitHub, có thể tải lên Google Drive hoặc Dropbox và dẫn link trong tài liệu.
- **Làm việc nhóm:** 🤝 Cần ghi rõ đóng góp của từng thành viên trong nhóm.
- **Tài liệu hóa mã nguồn:**
  - 🧾 Có bình luận giải thích rõ các thuật toán/phần logic phức tạp
  - 🧪 Docstring cho hàm/phương thức mô tả tham số, giá trị trả về và mục đích
  - 📘 File README cho từng module mã nguồn, hướng dẫn cài đặt và sử dụng
  - 📝 Bình luận inline cho các đoạn mã không rõ ràng

### ✅ Danh sách kiểm tra trước khi nộp

- [x] ✅ Đánh dấu X vào ô để xác nhận hoàn thành
- [ ] ✍️ Điền đầy đủ các mục trong mẫu README này
- [ ] 📄 Hoàn thiện báo cáo PDF chi tiết theo cấu trúc trên
- [ ] 🎨 Tuân thủ định dạng và nội dung theo hướng dẫn giảng viên
- [ ] ➕ Thêm các mục riêng của dự án nếu cần
- [ ] 🔍 Kiểm tra lại ngữ pháp, diễn đạt và độ chính xác kỹ thuật
- [ ] ⬆️ Tải lên báo cáo PDF, slide trình bày và mã nguồn
- [ ] 🧩 Đảm bảo tất cả mã nguồn được tài liệu hóa đầy đủ với bình luận và docstring
- [ ] 🔗 Kiểm tra các liên kết và tài liệu tham khảo hoạt động đúng


