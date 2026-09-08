#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converters nâng cao: hỗ trợ nhiều fallback và kiểm tra công cụ ngoài (ffmpeg, libreoffice, ebook-convert, ImageMagick).
Các chuyển đổi nặng (video, ebook, docx<->pdf, SVG rasterize, HEIC/AVIF, PSD) có thể yêu cầu công cụ/ thư viện bổ sung.
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
import zipfile

# Optional imports (may not be present)
try:
    import cairosvg
except Exception:
    cairosvg = None

try:
    import psd_tools
except Exception:
    psd_tools = None

try:
    import pillow_heif
except Exception:
    pillow_heif = None


def _ensure_dir(d):
    os.makedirs(d, exist_ok=True)


def is_tool(name):
    """Kiểm tra tool trên PATH"""
    return shutil.which(name) is not None


SUPPORTED_IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"}


def convert_image(in_path, target_ext, width=None, height=None, output_dir="outputs"):
    """
    Chuyển đổi ảnh với nhiều fallback:
    - Nếu Pillow hỗ trợ (PNG/JPEG/WEBP/BMP/GIF/TIFF/ICO) => dùng Pillow.
    - Nếu input SVG và cairosvg có => dùng cairosvg.svg2png/.. để chuyển.
    - Nếu PSD và psd-tools có => render PSD rồi save.
    - Nếu HEIC/AVIF và pillow_heif có => đọc rồi xử lý.
    - Cuối cùng thử gọi ImageMagick 'magick' hoặc 'convert' nếu có.
    Trả về đường dẫn file kết quả hoặc raise RuntimeError.
    """
    _ensure_dir(output_dir)
    target_ext = target_ext.lower().lstrip('.')
    basename = os.path.splitext(os.path.basename(in_path))[0]
    out_name = f"{basename}_converted_{uuid.uuid4().hex[:8]}.{target_ext}"
    out_path = os.path.join(output_dir, out_name)

    ext_in = os.path.splitext(in_path)[1].lower().lstrip('.')

    # If Pillow can handle both input and output
    try:
        if ext_in in SUPPORTED_IMAGE_EXTS and target_ext in SUPPORTED_IMAGE_EXTS:
            img = Image.open(in_path).convert('RGB')
            orig_w, orig_h = img.size
            if width or height:
                if width and not height:
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
    except Exception:
        pass

    # SVG input using cairosvg
    if ext_in == 'svg' and cairosvg:
        try:
            if target_ext in ('png','jpg','jpeg'):
                # cairosvg can write PNG; for jpg convert via Pillow
                png_bytes = cairosvg.svg2png(url=in_path)
                img = Image.open(io.BytesIO(png_bytes)).convert('RGB')
                if target_ext in ('jpg','jpeg'):
                    img.save(out_path, format='JPEG', quality=90)
                else:
                    img.save(out_path, format='PNG')
                return out_path
            elif target_ext == 'pdf':
                cairosvg.svg2pdf(url=in_path, write_to=out_path)
                return out_path
        except Exception as e:
            raise RuntimeError(f'Lỗi khi chuyển SVG bằng cairosvg: {e}')

    # PSD handling
    if ext_in == 'psd' and psd_tools:
        try:
            psd = psd_tools.PSDImage.open(in_path)
            img = psd.compose()
            img = img.convert('RGB')
            img.save(out_path)
            return out_path
        except Exception as e:
            raise RuntimeError(f'Lỗi khi xử lý PSD: {e}')

    # HEIC/AVIF via pillow_heif
    if ext_in in ('heic','heif','avif') and pillow_heif:
        try:
            heif_file = pillow_heif.read_heif(in_path)
            img = Image.frombytes(mode=heif_file.mode, size=heif_file.size, data=heif_file.data)
            img.save(out_path)
            return out_path
        except Exception as e:
            raise RuntimeError(f'Lỗi khi đọc HEIC/AVIF: {e}')

    # Fallback: try ImageMagick (magick/convert)
    magick = shutil.which('magick') or shutil.which('convert')
    if magick:
        cmd = [magick, in_path, out_path] if shutil.which('magick') else ['convert', in_path, out_path]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode == 0 and os.path.exists(out_path):
            return out_path
        else:
            raise RuntimeError('ImageMagick lỗi: ' + proc.stderr.decode(errors='ignore'))

    raise RuntimeError('Không thể chuyển đổi ảnh: thiếu thư viện/ công cụ. Cài cairosvg (SVG), psd-tools (PSD), pillow-heif (HEIC/AVIF) hoặc ImageMagick')


def text_to_pdf(in_path, output_dir="outputs", font_size=12):
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

    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    margin = 40
    y = height - margin
    line_height = font_size * 1.2
    c.setFont("Helvetica", font_size)
    for raw_line in text.splitlines():
        line = raw_line
        while line:
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


# Document conversions using LibreOffice if available
def docx_to_pdf_libreoffice(docx_path, output_dir="outputs"):
    if not is_tool('soffice'):
        raise RuntimeError('LibreOffice (soffice) không tìm thấy. Cài LibreOffice để dùng tính năng này.')
    _ensure_dir(output_dir)
    cmd = ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, docx_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError('LibreOffice lỗi: ' + proc.stderr.decode(errors='ignore'))
    # LibreOffice đặt cùng tên file với .pdf
    basename = os.path.splitext(os.path.basename(docx_path))[0]
    return os.path.join(output_dir, f"{basename}.pdf")


# Ebook convert wrapper (Calibre 'ebook-convert')
def ebook_convert(input_path, output_ext, output_dir='outputs'):
    if not is_tool('ebook-convert'):
        raise RuntimeError('ebook-convert (Calibre) không tìm thấy. Cài Calibre để dùng tính năng EBook.')
    _ensure_dir(output_dir)
    basename = os.path.splitext(os.path.basename(input_path))[0]
    out_path = os.path.join(output_dir, f"{basename}.{output_ext}")
    cmd = ['ebook-convert', input_path, out_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError('ebook-convert lỗi: ' + proc.stderr.decode(errors='ignore'))
    return out_path


# Video convert via ffmpeg wrapper
def can_convert_video():
    return is_tool('ffmpeg')


def convert_video_ffmpeg(in_path, target_ext, output_dir='outputs'):
    if not can_convert_video():
        raise RuntimeError('ffmpeg không có trên hệ thống.')
    _ensure_dir(output_dir)
    target_ext = target_ext.lower().lstrip('.')
    basename = os.path.splitext(os.path.basename(in_path))[0]
    out_name = f"{basename}_converted_{uuid.uuid4().hex[:8]}.{target_ext}"
    out_path = os.path.join(output_dir, out_name)
    cmd = ['ffmpeg', '-y', '-i', in_path, out_path]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError('ffmpeg lỗi: ' + proc.stderr.decode(errors='ignore'))
    return out_path


# Batch convert helper + zip
def batch_convert_and_zip(input_paths, category, target_ext, width=None, height=None, output_dir='outputs', zip_name=None):
    _ensure_dir(output_dir)
    outputs = []
    for p in input_paths:
        if category == 'Ảnh':
            out = convert_image(p, target_ext, width=width, height=height, output_dir=output_dir)
        elif category == 'Tài liệu':
            ext_in = os.path.splitext(p)[1].lower().lstrip('.')
            if ext_in in ['txt','md']:
                if target_ext == 'pdf':
                    out = text_to_pdf(p, output_dir=output_dir)
                elif target_ext in ('docx','doc'):
                    out = text_to_docx(p, output_dir=output_dir)
                else:
                    raise RuntimeError('Định dạng đích cho văn bản chưa được hỗ trợ: ' + target_ext)
            else:
                raise RuntimeError('Chỉ hỗ trợ .txt/.md cho Tài liệu (batch) trong phiên bản này')
        elif category == 'PDF':
            if target_ext == 'txt':
                out = pdf_to_text(p, output_dir=output_dir)
            else:
                raise RuntimeError('Chỉ hỗ trợ PDF → TXT trong phiên bản này')
        elif category == 'Video':
            out = convert_video_ffmpeg(p, target_ext, output_dir=output_dir)
        else:
            raise RuntimeError('Category chưa hỗ trợ batch')
        outputs.append(out)

    if not zip_name:
        zip_name = f'outputs_{uuid.uuid4().hex[:8]}.zip'
    zip_path = os.path.join(output_dir, zip_name)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for f in outputs:
            zf.write(f, arcname=os.path.basename(f))
    return zip_path
