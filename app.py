#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import uuid
from converters import (
    convert_image,
    text_to_pdf,
    text_to_docx,
    pdf_to_text,
    can_convert_video,
    convert_video_ffmpeg
)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
ALLOWED_EXTENSIONS = set([
    # images
    "png", "jpg", "jpeg", "gif", "bmp", "webp",
    # text
    "txt", "md",
    # pdf
    "pdf",
    # video
    "mp4", "mov", "avi", "mkv", "webm"
])

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "thay-the-bang-khoa-bao-mat"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB limit

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("Không tìm thấy file để tải lên.")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("Vui lòng chọn file.")
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash("Định dạng file không được hỗ trợ trong ví dụ này.")
            return redirect(request.url)

        category = request.form.get("category")
        target_format = request.form.get("target_format")
        width = request.form.get("width", type=int)
        height = request.form.get("height", type=int)

        filename = secure_filename(file.filename)
        uid = uuid.uuid4().hex
        in_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{uid}_{filename}")
        file.save(in_path)

        try:
            out_path = None
            if category == "anh":
                out_path = convert_image(in_path, target_format, width=width, height=height, output_dir=app.config["OUTPUT_FOLDER"])
            elif category == "vanban":
                # input assumed text
                if target_format.lower() == "pdf":
                    out_path = text_to_pdf(in_path, output_dir=app.config["OUTPUT_FOLDER"])
                elif target_format.lower() in ("docx", "doc"):
                    out_path = text_to_docx(in_path, output_dir=app.config["OUTPUT_FOLDER"])
                else:
                    flash("Định dạng đích cho văn bản không được hỗ trợ.")
                    return redirect(request.url)
            elif category == "pdf":
                if target_format.lower() == "txt":
                    out_path = pdf_to_text(in_path, output_dir=app.config["OUTPUT_FOLDER"])
                else:
                    flash("Chỉ hỗ trợ chuyển PDF → TXT trong phiên bản này.")
                    return redirect(request.url)
            elif category == "video":
                if not can_convert_video():
                    flash("Chức năng chuyển đổi video cần ffmpeg. Vui lòng cài ffmpeg hoặc sử dụng các chức năng khác.")
                    return redirect(request.url)
                # simple ffmpeg-based convert
                out_path = convert_video_ffmpeg(in_path, target_format, output_dir=app.config["OUTPUT_FOLDER"])
            else:
                flash("Thể loại không hợp lệ.")
                return redirect(request.url)

            if out_path is None:
                flash("Không thể chuyển đổi file (lỗi nội bộ).")
                return redirect(request.url)

            return send_file(out_path, as_attachment=True)
        except Exception as e:
            flash(f"Lỗi khi chuyển đổi: {e}")
            return redirect(request.url)
    return render_template("index.html", ffmpeg_available=can_convert_video())

if __name__ == "__main__":
    app.run(debug=True)
