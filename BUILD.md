# Build scripts (tùy chọn)

Nếu bạn muốn đóng gói .exe cho Windows, mình có thể dùng PyInstaller. Dưới đây là hướng dẫn nhanh:

1) Cài PyInstaller trong virtualenv:
   pip install pyinstaller
2) Tạo executable:
   pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" app.py
3) File .exe sẽ nằm trong dist\app.exe

Lưu ý: với nhiều thư viện phụ thuộc (cairosvg, pillow-heif, psd-tools) bạn cần đảm bảo virtualenv đầy đủ trước khi build.
