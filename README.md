# Ứng dụng Chuyển Đổi File (Tiếng Việt)

Ứng dụng web Flask đơn giản để chuyển đổi file local: ảnh, văn bản, PDF, và hỗ trợ video nếu hệ thống có ffmpeg.

Yêu cầu:
- Python 3.8+
- pip

Cài đặt và chạy:
1. Tạo virtualenv (khuyến nghị):
   - python -m venv venv
   - source venv/bin/activate   (Windows: venv\Scripts\activate)

2. Cài dependencies:
   - pip install -r requirements.txt

3. Chạy ứng dụng:
   - ./run.sh   (Linux/Mac) hoặc python app.py

4. Mở trình duyệt và truy cập:
   - http://127.0.0.1:5000

Lưu ý về video:
- Một số chuyển đổi video cần ffmpeg (không phải pip). Nếu bạn muốn chuyển đổi video, cài ffmpeg (ví dụ trên Ubuntu: `sudo apt install ffmpeg`) rồi thử lại.

Thư mục:
- app.py — ứng dụng Flask chính
- converters.py — các hàm chuyển đổi file
- templates/ — HTML (tiếng Việt)
- static/ — CSS
- requirements.txt — các package Python
- run.sh — script khởi động
- samples/sample.txt — file ví dụ
- tests/test_converters.py — testcase đơn giản

Hướng dẫn nhanh sử dụng:
- Tải file lên, chọn loại chuyển đổi, bấm "Chuyển đổi".
- File chuyển đổi sẽ được trả về để tải về.

Liên hệ:
- Nếu cần thêm định dạng, tự động hóa hàng loạt hoặc ZIP đầu ra, mình có thể mở rộng.
