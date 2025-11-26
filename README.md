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

| 👤 Họ và tên    | 🆔 Mã sinh viên | 🐙 Tên GitHub | 🛠️ Đóng góp                       |
| --------------- | --------------- | ------------- | --------------------------------- |
| Cao Hải An      | 23001818        | HaianCao      | Xây dựng pipeline chatbot         |
| Đặng Thế Anh    | 23001821        | DangTAnh      | Thu thập dữ liệu                  |
| Phạm Minh Cương | 23001840        | mcnb2005      | Phát triển giao diện web          |
| Đỗ Minh Đức     | 23001864        | minhhhduc     | Xây dựng module truy xuất dữ liệu |
| Phạm Nhật Quang | 23001920        | NhatquangPham | Tiền xử lý dữ liệu                |

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

- 🔍 **Cách tiếp cận:**

  - Kết hợp mô hình ngôn ngữ lớn đã được pretrained với kiến trúc RAG (Retrieval-Augmented Generation) để tối ưu hóa độ chính xác và tính thực tiễn của chatbot ẩm thực.
  - Dữ liệu được thu thập từ các website ẩm thực uy tín, xử lý và lưu trữ dưới dạng vector để tìm kiếm ngữ nghĩa hiệu quả.
  - Các module chính:
    - **crawler/**: Thu thập dữ liệu công thức, đánh giá, nguyên liệu từ web (sử dụng script Python, selenium, lưu dữ liệu vào thư mục data/)
    - **preprocessing/**: Làm sạch, chuẩn hóa, trích xuất thông tin, lưu dữ liệu đã xử lý (tạo preprocessed_data.json)
    - **bot/src/chatbotfood**: Xử lý truy vấn, tìm kiếm, sinh phản hồi, giao tiếp với người dùng, tích hợp LLM và ChromaDB
    - **bot/src/web/**: Giao diện chat web đơn giản, kết nối backend qua API (Flask/FastAPI)

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
  - Cơ sở dữ liệu công thức nấu ăn từ https://therecipecritic.com

**💻 Triển khai**

- 🧩 **Kiến trúc hệ thống:**

  - **Frontend:** Giao diện chat tương tác thân thiện với người dùng
  - **API Layer:** Xử lý request và routing giữa các components
  - **RAG Engine:** Core logic kết hợp retrieval và generation
  - **Vector Database:** Lưu trữ embeddings và thực hiện similarity search
  - **LLM Integration:** Kết nối với mô hình pretrained Gemini

- 🛠️ **Công cụ và Framework:**

  - **Vector Database:** ChromaDB cho việc lưu trữ và truy xuất vector, sử dụng cơ chế embedding mặc định của ChromaDB.
  - **LLM:** Tích hợp Google Gemini API để sinh phản hồi và xử lý ngôn ngữ tự nhiên.
  - **Backend:** Python với Flask cho web demo.
  - **Frontend:** Giao diện web đơn giản bằng HTML/CSS/JS.

- 📁 **Cấu trúc mã nguồn:**
  ```
  VNU-HUS-IntroAI-MiniProject/
  ├── crawler/                       # Thu thập dữ liệu công thức, nguyên liệu từ web
  │   ├── crawl_category_links.py    # Script crawl link danh mục
  │   ├── crawl_recipe_links_parallel.py # Script crawl link công thức
  │   ├── crawl_recipe_infos_parallel.py # Script crawl chi tiết công thức
  │   ├── packages/                  # Các module phụ trợ crawler
  │   └── data/                      # Dữ liệu crawl được
  ├── preprocessing/                 # Làm sạch, chuẩn hóa, trích xuất thông tin, lưu dữ liệu
  │   ├── food_preprocessing.py      # Xử lý dữ liệu thực phẩm
  │   ├── comments.py, constants.py, io_utils.py, ... # Tiện ích xử lý
  │   └── data/                      # Dữ liệu để xử lý
  ├── bot/                           # Chatbot và backend
  │   ├── main.py                    # Chạy chatbot backend
  │   ├── processed_data.json        # Dữ liệu đã xử lý cho chatbot
  │   ├── src/
  │   │   ├── chatbotfood/           # Core logic: retrieval, LLM, chroma, config
  │   │   │   ├── chatbot.py         # Xử lý truy vấn, hội thoại
  │   │   │   ├── chroma_manager.py  # Quản lý ChromaDB
  │   │   │   ├── gemini_client.py   # Tích hợp Gemini API
  │   │   │   ├── config.py, prompts.py, schemas.py, ... # Cấu hình, prompt, schema
  │   │   └── web/                   # Giao diện web, server backend
  │   │       ├── server.py          # Server Flask
  │   │       └── static/            # Tài nguyên tĩnh (HTML, JS, CSS)
  ├── requirements.txt               # Thư viện Python cần thiết
  ├── README.md                      # Tài liệu dự án
  └── LaTeX Template/                # Template báo cáo LaTeX
  ```

### Chương 3: Kết quả & Phân tích

**📊 Kết quả & Thảo luận**

- Đã xây dựng thành công một chatbot ẩm thực hoàn chỉnh, có khả năng cung cấp kiến thức về các món ăn, công thức nấu ăn, gợi ý món phù hợp với nguyên liệu và sở thích người dùng.
- Chatbot trả lời lưu loát, tự nhiên nhờ tận dụng sức mạnh của mô hình ngôn ngữ Gemini, giúp phản hồi đa dạng, sát với ngữ cảnh thực tế.
- Việc lưu trữ dữ liệu dưới dạng vector với ChromaDB giúp tăng tốc độ và độ chính xác khi tìm kiếm thông tin, đảm bảo truy xuất công thức và kiến thức ẩm thực hiệu quả.
- Giao diện web thân thiện, dễ sử dụng, hỗ trợ người dùng tương tác trực tiếp với chatbot một cách thuận tiện.
- Đánh giá thực tế từ người dùng thử nghiệm cho thấy khoảng 80% câu trả lời của chatbot đạt yêu cầu cả về chất lượng giao tiếp lẫn độ chính xác thông tin.

### Chương 4: Kết luận

**✅ Kết luận & Hướng phát triển**

- Dự án đã hoàn thành mục tiêu xây dựng một hệ thống chatbot ẩm thực thông minh, ứng dụng các công nghệ AI hiện đại và lưu trữ vector.
- Chatbot đáp ứng tốt nhu cầu tra cứu, tư vấn món ăn, hỗ trợ nấu nướng cho người dùng phổ thông.
- Hướng phát triển tiếp theo: mở rộng nguồn dữ liệu, nâng cấp giao diện, bổ sung khả năng cá nhân hóa sâu hơn và tích hợp thêm các tiêu chí đánh giá món ăn (dinh dưỡng, khẩu vị, dị ứng, v.v.).

### Tài liệu tham khảo & Phụ lục

**📚 Tài liệu tham khảo**

- 🔗 Danh sách bài báo, sách và nguồn tham khảo

**📎 Phụ lục** _(Tùy chọn)_

- 📎 Kết quả bổ sung, đoạn mã hoặc hướng dẫn sử dụng

---

## 📝 Hướng dẫn nộp bài

### 📋 Yêu cầu

- **Định dạng:**
  - Báo cáo được trình bày rõ ràng, xuất ra PDF (ưu tiên LaTeX, đã có template trong `LaTeX Template/`).
  - Một bản báo cáo lưu trên GitHub, hai bản nộp Canvas, hai bản in cho giảng viên và trợ giảng. Slide trình bày tương tự (không cần bản in slide).
- **Kho lưu trữ:** Bao gồm báo cáo PDF, slide, toàn bộ mã nguồn và tài liệu liên quan. Nếu vượt quá dung lượng GitHub, tải lên Google Drive/Dropbox và dẫn link trong tài liệu.
- **Làm việc nhóm:** Đã ghi rõ đóng góp của từng thành viên trong bảng trên.
- **Tài liệu hóa mã nguồn:**
  - Có bình luận giải thích rõ các thuật toán/phần logic phức tạp
  - Docstring cho hàm/phương thức mô tả tham số, giá trị trả về và mục đích
  - File README cho từng module chính, hướng dẫn cài đặt và sử dụng (xem `bot/README.md`, `crawler/README.md`, `preprocessing/README.md`)
  - Bình luận inline cho các đoạn mã không rõ ràng

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
