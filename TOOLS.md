# Hướng dẫn cài đặt công cụ bổ sung (Windows)

Một số tính năng "Full" yêu cầu cài thêm công cụ hoặc thư viện ngoài Python. Dưới đây là hướng dẫn ngắn cho Windows.

1) ffmpeg (bắt buộc nếu bạn muốn chuyển đổi video)
- Tải: https://ffmpeg.org/download.html -> Windows builds
- Giải nén, ví dụ: C:\ffmpeg\
- Thêm vào PATH: C:\ffmpeg\bin
- Mở PowerShell mới và kiểm tra: ffmpeg -version

2) LibreOffice (nếu muốn chuyển DOC/DOCX ↔ PDF bằng công cụ chính xác)
- Tải từ: https://www.libreoffice.org/download/download/
- LibreOffice cung cấp lệnh soffice để convert: soffice --headless --convert-to pdf input.docx

3) Calibre (nếu muốn chuyển đổi EBook: EPUB/MOBI/...)
- Tải: https://calibre-ebook.com/download
- Sau khi cài Calibre, lệnh ebook-convert sẽ khả dụng trên PATH: ebook-convert input.epub output.pdf

4) ImageMagick (hỗ trợ nhiều format ảnh, fallback nếu Pillow không xử lý được)
- Tải: https://imagemagick.org/script/download.php
- Thêm 'magick' hoặc 'convert' vào PATH

5) Thêm các thư viện Python cho định dạng nâng cao
- pillow-heif: đọc HEIC/AVIF
- psd-tools: đọc PSD
- cairosvg: render SVG → PNG/PDF

Cài ví dụ (PowerShell):
python -m pip install --upgrade pip
pip install -r requirements.txt

Nếu bạn muốn, mình sẽ tạo một script PowerShell (setup_tools.ps1) tự động mở link hoặc kiểm tra tool đã có hay chưa.
