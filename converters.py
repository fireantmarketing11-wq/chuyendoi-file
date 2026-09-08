# -*- coding: utf-8 -*-
"""
Hàm chuyển đổi đơn giản cho ảnh, văn bản, PDF, video (nếu có ffmpeg).
Mục tiêu: hoạt động không cần chỉnh sửa thêm cho phần ảnh/văn bản/pdf.
Video yêu cầu ffmpeg (không phải pip).
"""
from PIL import Image
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from docx import Document
from PyPDF2 import PdfReader
import shutil
import subprocess
import uuid

def _ensure_dir(d):
    os.makedirs(d, exist_ok=True)

def convert_image(in_path, target_ext, width=None, height=None, output_dir="outputs"):
    """
    Chuyển đổi ảnh sang đuôi target_ext (ví dụ: 'png', 'jpg', 'webp').
    Nếu width/height được cung cấp, sẽ thay đổi kích thước giữ tỉ lệ nếu chỉ một chiều được cho.
    Trả về đường dẫn file kết quả.
    """
    _ensure_dir(output_dir)
    target_ext = target_ext.lower().lstrip(".")
    basename = os.path.splitext(os.path.basename(in_path))[0]
    out_name = f"{basename}_converted_{uuid.uuid4().hex[:8]}.{target_ext}"
    out_path = os.path.join(output_dir, out_name)

    img = Image.open(in_path).convert("RGB")
    orig_w, orig_h = img.size
    if width or height:
        if width and not height:
            # tính theo tỉ lệ
            ratio = width / orig_w
            height = int(orig_h * ratio)
        elif height and not width:
            ratio = height / orig_h
            width = int(orig_w * ratio)
        img = img.resize((width, height), Image.LANCZOS)

    save_kwargs = {}
    if target_ext in ("jpg", "jpeg"):
        save_kwargs["format"] = "JPEG"
        save_kwargs["quality"] = 90
    else:
        save_kwargs["format"] = target_ext.upper()

    img.save(out_path, **save_kwargs)
    return out_path

def text_to_pdf(in_path, output_dir="outputs", font_size=12):
    """
    Chuyển file .txt (UTF-8) sang PDF bằng reportlab.
    Nếu file không decode được bằng utf-8 sẽ thử latin-1.
    """
    _ensure_dir(output_dir)
    basename = os.path.splitext(os.path.basename(in_path))[0]
    out_path = os.path.join(output_dir, f"{basename}.pdf")

    # đọc text
    with open(in_path, "rb") as f:
        data = f.read()
    try:
        text = data.decode("utf-8")
    except Exception:
        text = data.decode("latin-1")

    # tạo pdf
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin
    line_height = font_size * 1.2
    c.setFont("Helvetica", font_size)
    for raw_line in text.splitlines():
        # wrap dài
        line = raw_line
        while line:
            # ước lượng số char fit per line (đơn giản)
            max_chars = int((width - margin * 2) / (font_size * 0.6))
            to_draw = line[:max_chars]
            c.drawString(margin, y, to_draw)
            line = line[max_chars:]
            y -= line_height
            if y < margin:
                c.showPage()
                c.setFont("Helvetica", font_size)
                y = height - margin
    c.save()
    return out_path

def text_to_docx(in_path, output_dir="outputs"):
    _ensure_dir(output_dir)
    basename = os.path.splitext(os.path.basename(in_path))[0]
    out_path = os.path.join(output_dir, f"{basename}.docx")

    with open(in_path, "rb") as f:
        data = f.read()
    try:
        text = data.decode("utf-8")
    except Exception:
        text = data.decode("latin-1")

    doc = Document()
    for line in text.splitlines():
        doc.add_paragraph(line)
    doc.save(out_path)
    return out_path

def pdf_to_text(in_path, output_dir="outputs"):
    _ensure_dir(output_dir)
    basename = os.path.splitext(os.path.basename(in_path))[0]
    out_path = os.path.join(output_dir, f"{basename}.txt")

    reader = PdfReader(in_path)
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            texts.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(texts))
    return out_path

# Video helpers (dùng ffmpeg nếu có)
def can_convert_video():
    return shutil.which("ffmpeg") is not None

def convert_video_ffmpeg(in_path, target_ext, output_dir="outputs"):
    """
    Chuyển đổi video bằng ffmpeg nếu có. Trả về đường dẫn file kết quả.
    target_ext: 'mp4', 'webm', 'gif', ...
    """
    if not can_convert_video():
        raise RuntimeError("ffmpeg không có trên hệ thống.")

    _ensure_dir(output_dir)
    target_ext = target_ext.lower().lstrip(".")
    basename = os.path.splitext(os.path.basename(in_path))[0]
    out_name = f"{basename}_converted_{uuid.uuid4().hex[:8]}.{target_ext}"
    out_path = os.path.join(output_dir, out_name)

    # Lệnh ffmpeg cơ bản: ffmpeg -i in_path out_path -y
    cmd = ["ffmpeg", "-y", "-i", in_path, out_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg lỗi: {proc.stderr.decode(errors='ignore')}")
    return out_path
