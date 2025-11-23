# Trình Thu Thập Dữ Liệu TheRecipeCritic.com

Đây là một trình thu thập dữ liệu web đa giai đoạn mạnh mẽ, được thiết kế để thu thập dữ liệu công thức nấu ăn từ `therecipecritic.com`. Được xây dựng bằng Python và sử dụng Selenium với `undetected-chromedriver` để xử lý nội dung web động và vượt qua các cơ chế phát hiện bot.

Trình thu thập được thiết kế để đảm bảo tính ổn định và hiệu suất, có tính năng xử lý song song, khôi phục lỗi tự động và kiến trúc module hóa.

## Tính năng

- **Quy trình Đa giai đoạn**: Quá trình thu thập được chia thành các bước logic, tuần tự.
- **Thực thi Song song**: Sử dụng cả đa xử lý (`concurrent.futures`) và đa luồng để tăng tốc đáng kể quá trình thu thập.
- **Xử lý Lỗi Mạnh mẽ**:
    - **Bộ đếm thời gian Watchdog**: Ngăn trình thu thập bị treo trên các trang không phản hồi bằng cách khởi động lại trình điều khiển trình duyệt nếu tải trang vượt quá thời gian chờ.
    - **Khởi động lại Driver Tự động**: Tự động khởi động lại WebDriver trong các luồng worker khi gặp lỗi không mong đợi.
    - **Logic Thử lại**: Cơ chế tải trang cơ bản bao gồm thử lại cho các vấn đề mạng tạm thời.
- **Vượt qua Cloudflare**: Tích hợp `undetected-chromedriver` để vượt qua các biện pháp chống bot của Cloudflare.
- **Khả năng Tiếp tục**: Trình thu thập có thể dừng và tiếp tục từ một URL hoặc số trang cụ thể, tránh phải khởi động lại từ đầu.
- **Code Module hóa & Sạch sẽ**: Codebase được tổ chức thành thư mục `packages` với các handler cho logic Selenium, logging và tiện ích, thúc đẩy tái sử dụng code và dễ bảo trì.
- **Có thể Cấu hình**: Các tham số chính như số lượng worker, chế độ headless (không khuyến khích) và độ trễ lịch sự có thể được cấu hình qua biến môi trường hoặc hằng số.
- **Lưu trữ Dữ liệu**: Lưu các liên kết công thức được trích xuất và thông tin công thức chi tiết vào thư mục `data/`. Chi tiết công thức được lưu dưới dạng các tệp JSON riêng lẻ.

## Cấu trúc

```
.
├── packages/
│   ├── selenium_handler.py # Logic Selenium cốt lõi, tạo driver, trích xuất dữ liệu
│   ├── logging_handler.py  # Cấu hình logging tập trung
│   └── utils.py            # Các hàm tiện ích (đọc/ghi file, v.v.)
│
├── crawl_category_links.py       # Giai đoạn 1: Lấy các liên kết danh mục chính.
├── crawl_recipe_links_parallel.py  # Giai đoạn 2: Thu thập liên kết công thức từ danh mục (song song).
├── crawl_recipe_infos_parallel.py  # Giai đoạn 3: Thu thập chi tiết công thức (song song).
│
├── requirements.txt        # Các thư viện phụ thuộc.
├── data/                   # Thư mục đầu ra cho dữ liệu đã thu thập.
│   ├── links.txt           # Các liên kết danh mục ban đầu.
│   ├── combined.txt        # Tất cả các liên kết công thức riêng lẻ.
│   └── foods/              # Các tệp JSON cho mỗi công thức đã thu thập.
└── readme.md               # Tệp này.
```

## Quy trình và Cách chạy

### 1. Cài đặt

Đầu tiên, cài đặt các gói Python cần thiết:

```bash
pip install -r requirements.txt
```

### 2. Quy trình Thực thi

Trình thu thập hoạt động theo ba giai đoạn riêng biệt. Chạy chúng theo thứ tự sau:

**Giai đoạn 1: Thu thập Liên kết Danh mục**

Script này lấy danh sách ban đầu các danh mục công thức từ trang chính và lưu vào `data/links.txt`.

```bash
python crawl_category_links.py
```

**Giai đoạn 2: Thu thập Liên kết Công thức từ Danh mục (Song song)**

Script này đọc các URL danh mục từ `data/links.txt` và thu thập từng cái song song để tìm tất cả các liên kết công thức riêng lẻ.

```bash
python crawl_recipe_links_parallel.py
```

**Giai đoạn 3: Thu thập Thông tin Công thức (Song song)**

Đây là giai đoạn cuối cùng. Script đọc các URL công thức riêng lẻ từ `data/combined.txt` và thu thập từng cái song song để trích xuất thông tin chi tiết (tóm tắt, nguyên liệu, hướng dẫn, v.v.). Dữ liệu cho mỗi công thức được lưu dưới dạng tệp JSON riêng trong thư mục `data/foods/`.

```bash
python crawl_recipe_infos_parallel.py
```

## Cấu hình

Bạn có thể kiểm soát hành vi của trình thu thập bằng các biến môi trường:

- **`WORKERS`**: Đặt số lượng worker song song (process hoặc thread) để sử dụng.
  - Ví dụ: `set WORKERS=4` (Windows CMD)
  - Ví dụ: `export WORKERS=4` (Linux/macOS)
  - Mặc định là `3` nếu không được đặt.

- **`SKIP_EXISTING_PAGES`**: Nếu được đặt thành `true`, trình thu thập sẽ bỏ qua việc thu thập các trang mà tệp đầu ra đã tồn tại. Điều này hữu ích để tiếp tục một quá trình thu thập bị gián đoạn.
  - Được cấu hình dưới dạng hằng số trong chính các script.

- **`CRAWL_FROM_URL` / `CRAWL_FROM_PAGE`**: Các hằng số trong các script có thể được đặt để tiếp tục thu thập từ một điểm cụ thể.
