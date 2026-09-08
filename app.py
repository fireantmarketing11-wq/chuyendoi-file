#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Giao diện GUI đã mở rộng: hỗ trợ chọn nhiều file (batch), tạo ZIP đầu ra, và thông báo rõ các công cụ bổ sung cần cài.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import webbrowser
from converters import (
    convert_image,
    text_to_pdf,
    text_to_docx,
    pdf_to_text,
    can_convert_video,
    convert_video_ffmpeg,
    batch_convert_and_zip,
    is_tool,
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(APP_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CATEGORIES = {
    "Ảnh": [
        "png","svg","jpeg","jpg","ico","webp","bmp","gif","tiff","dds",
        "heic","psd","avif","tga"
    ],
    "Tài liệu": [
        "pdf","doc","docx","docm","odt","xps","rtf","dot","dotx","djvu",
        "aw","abw","dbk","kwd","sxw"
    ],
    "EBook": [
        "epub","mobi","pdb","azw3","fb2","tcr","lrf","rb","snb"
    ],
    "Vector": [
        "svg","ai","plt","eps","wmf","sk","emf","fig","cgm","sk1","ps"
    ],
    "Video": ["mp4","webm","mkv","avi","mov","wmv","flv","gif"]
}

SUPPORTED_IMAGE_EXTS = {"png","jpg","jpeg","webp","bmp","gif","tiff","ico"}

class ConverterApp:
    def __init__(self, root):
        self.root = root
        root.title("Chuyển Đổi File — Ứng Dụng Local (Full)")
        root.geometry("820x620")

        self.input_paths = []
        self.category = tk.StringVar(value="Ảnh")
        self.target_format = tk.StringVar(value="png")
        self.batch_mode = tk.BooleanVar(value=False)
        self.zip_output = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        frm = tk.Frame(self.root, padx=12, pady=12)
        frm.pack(fill=tk.BOTH, expand=True)

        # File selector (supports multiple)
        tk.Label(frm, text="1) Chọn file (hoặc nhiều file cho batch):").grid(row=0, column=0, sticky="w")
        btn_file = tk.Button(frm, text="Chọn file...", command=self.choose_files)
        btn_file.grid(row=0, column=1, sticky="w")
        self.lbl_file = tk.Label(frm, text="(chưa chọn)", anchor="w")
        self.lbl_file.grid(row=0, column=2, columnspan=6, sticky="w")

        # Batch checkbox
        tk.Checkbutton(frm, text="Chế độ batch (nhiều file)", variable=self.batch_mode, command=self.on_batch_toggle).grid(row=1, column=1, sticky='w', pady=(8,0))
        tk.Checkbutton(frm, text="Nén ZIP đầu ra (nếu batch)", variable=self.zip_output).grid(row=1, column=2, sticky='w', pady=(8,0))

        # Categories
        left = tk.Frame(frm)
        left.grid(row=2, column=0, rowspan=5, sticky="ns", pady=(10,0))
        tk.Label(left, text="Danh mục:").pack(anchor="w")
        for cat in CATEGORIES.keys():
            b = tk.Radiobutton(left, text=cat, variable=self.category, value=cat, command=self.update_formats)
            b.pack(anchor="w")

        # format buttons
        tk.Label(frm, text="2) Chọn định dạng đích:").grid(row=2, column=1, sticky="w", pady=(10,0))
        self.format_frame = tk.Frame(frm)
        self.format_frame.grid(row=3, column=1, columnspan=7, sticky="w", pady=(6,0))
        self._render_format_buttons()

        # size
        self.size_frame = tk.Frame(frm)
        self.size_frame.grid(row=4, column=1, columnspan=7, sticky="w", pady=(12,0))
        tk.Label(self.size_frame, text="Kích thước (px, để trống giữ nguyên):").grid(row=0, column=0, sticky="w")
        tk.Label(self.size_frame, text="W:").grid(row=0, column=1)
        self.ent_w = tk.Entry(self.size_frame, width=8)
        self.ent_w.grid(row=0, column=2, padx=(0,8))
        tk.Label(self.size_frame, text="H:").grid(row=0, column=3)
        self.ent_h = tk.Entry(self.size_frame, width=8)
        self.ent_h.grid(row=0, column=4)

        # tools status
        self.tools_frame = tk.Frame(frm)
        self.tools_frame.grid(row=5, column=1, columnspan=6, sticky='w', pady=(8,0))
        self._render_tools_status()

        # Buttons
        self.btn_convert = tk.Button(frm, text="Chuyển đổi", command=self.on_convert, bg="#1976d2", fg="#fff")
        self.btn_convert.grid(row=6, column=1, pady=16, sticky="w")

        self.btn_open_out = tk.Button(frm, text="Mở thư mục outputs", command=self.open_outputs)
        self.btn_open_out.grid(row=6, column=2, pady=16, sticky="w")

        self.status = tk.Label(frm, text="Sẵn sàng.", anchor="w")
        self.status.grid(row=7, column=0, columnspan=9, sticky="w")

        self.update_formats()

    def _render_tools_status(self):
        for w in self.tools_frame.winfo_children():
            w.destroy()
        ff = 'ffmpeg' if is_tool('ffmpeg') else '(ffmpeg: không có)'
        so = 'soffice' if is_tool('soffice') else '(soffice: không có)'
        ec = 'ebook-convert' if is_tool('ebook-convert') else '(ebook-convert: không có)'
        im = 'magick/convert' if (is_tool('magick') or is_tool('convert')) else '(ImageMagick: không có)'
        tk.Label(self.tools_frame, text=f'Tools: {ff} | {so} | {ec} | {im}').pack(anchor='w')

    def _render_format_buttons(self):
        for w in self.format_frame.winfo_children():
            w.destroy()
        fmt_list = CATEGORIES.get(self.category.get(), [])
        r = 0
        c = 0
        for fmt in fmt_list:
            btn = tk.Button(self.format_frame, text=fmt.upper(), width=8, command=lambda f=fmt: self.set_format(f))
            # disable video buttons if ffmpeg missing
            if self.category.get() == 'Video' and not is_tool('ffmpeg'):
                btn.config(state=tk.DISABLED)
            btn.grid(row=r, column=c, padx=4, pady=4)
            c += 1
            if c >= 8:
                c = 0
                r += 1

    def set_format(self, fmt):
        self.target_format.set(fmt)
        self.status.config(text=f"Đã chọn định dạng: {fmt}")

    def update_formats(self):
        self._render_format_buttons()
        if self.category.get() == 'Ảnh':
            self.size_frame.grid()
        else:
            self.size_frame.grid_remove()
        self._render_tools_status()

    def choose_files(self):
        if self.batch_mode.get():
            paths = filedialog.askopenfilenames(title="Chọn nhiều file để chuyển đổi")
            if paths:
                self.input_paths = list(paths)
                self.lbl_file.config(text=f"{len(self.input_paths)} file đã chọn")
        else:
            path = filedialog.askopenfilename(title="Chọn file để chuyển đổi")
            if path:
                self.input_paths = [path]
                self.lbl_file.config(text=path)
        # auto-select category based on first file
        if self.input_paths:
            ext = os.path.splitext(self.input_paths[0])[1].lower().lstrip('.')
            if ext in ['png','jpg','jpeg','webp','bmp','gif','tiff','ico']:
                self.category.set('Ảnh')
            elif ext in ['txt','md']:
                self.category.set('Tài liệu')
            elif ext == 'pdf':
                self.category.set('PDF')
            elif ext in ['epub','mobi','azw3','fb2','pdb']:
                self.category.set('EBook')
            elif ext in ['svg','ai','eps','ps']:
                self.category.set('Vector')
            elif ext in ['mp4','mov','avi','mkv','webm','wmv','flv','gif']:
                self.category.set('Video')
            self.update_formats()

    def open_outputs(self):
        if os.name == 'nt':
            os.startfile(OUTPUT_DIR)
        else:
            webbrowser.open(OUTPUT_DIR)

    def on_batch_toggle(self):
        if self.batch_mode.get():
            self.zip_output.set(True)

    def on_convert(self):
        if not self.input_paths:
            messagebox.showwarning('Thiếu file', 'Vui lòng chọn file trước khi chuyển đổi')
            return
        cat = self.category.get()
        tgt = self.target_format.get()
        w = self.ent_w.get().strip()
        h = self.ent_h.get().strip()
        try:
            w = int(w) if w else None
            h = int(h) if h else None
        except ValueError:
            messagebox.showerror('Lỗi', 'Kích thước phải là số nguyên hoặc để trống')
            return

        self.btn_convert.config(state=tk.DISABLED)
        self.status.config(text='Đang chuyển đổi...')
        threading.Thread(target=self._do_convert, args=(cat, tgt, w, h), daemon=True).start()

    def _do_convert(self, cat, tgt, w, h):
        try:
            if self.batch_mode.get() and len(self.input_paths) > 1:
                if self.zip_output.get():
                    zip_path = batch_convert_and_zip(self.input_paths, cat, tgt, width=w, height=h, output_dir=OUTPUT_DIR)
                    self.status.config(text=f'Hoàn tất: {zip_path}')
                    messagebox.showinfo('Hoàn tất', f'Đã tạo ZIP: {zip_path}')
                else:
                    outs = []
                    for p in self.input_paths:
                        # reuse single-file logic by calling converters directly
                        ext_in = os.path.splitext(p)[1].lower().lstrip('.')
                        if cat == 'Ảnh':
                            out = convert_image(p, tgt, width=w, height=h, output_dir=OUTPUT_DIR)
                        elif cat == 'Tài liệu':
                            if ext_in in ['txt','md']:
                                if tgt == 'pdf':
                                    out = text_to_pdf(p, output_dir=OUTPUT_DIR)
                                else:
                                    out = text_to_docx(p, output_dir=OUTPUT_DIR)
                            else:
                                raise RuntimeError('Batch Tài liệu chỉ hỗ trợ .txt/.md')
                        elif cat == 'PDF' and tgt == 'txt':
                            out = pdf_to_text(p, output_dir=OUTPUT_DIR)
                        elif cat == 'Video':
                            out = convert_video_ffmpeg(p, tgt, output_dir=OUTPUT_DIR)
                        else:
                            raise RuntimeError('Category chưa hỗ trợ batch không nén')
                        outs.append(out)
                    self.status.config(text=f'Hoàn tất: {len(outs)} file')
                    messagebox.showinfo('Hoàn tất', f'Đã tạo {len(outs)} file trong outputs/')
            else:
                p = self.input_paths[0]
                ext_in = os.path.splitext(p)[1].lower().lstrip('.')
                if cat == 'Ảnh':
                    out_path = convert_image(p, tgt, width=w, height=h, output_dir=OUTPUT_DIR)
                elif cat == 'Tài liệu':
                    if ext_in in ['txt','md']:
                        if tgt == 'pdf':
                            out_path = text_to_pdf(p, output_dir=OUTPUT_DIR)
                        else:
                            out_path = text_to_docx(p, output_dir=OUTPUT_DIR)
                    else:
                        raise RuntimeError('Tài liệu chỉ hỗ trợ .txt/.md ở phiên bản này')
                elif cat == 'PDF':
                    if ext_in == 'pdf' and tgt == 'txt':
                        out_path = pdf_to_text(p, output_dir=OUTPUT_DIR)
                    else:
                        raise RuntimeError('Chỉ hỗ trợ PDF → TXT')
                elif cat == 'EBook':
                    out_path = None
                    # try ebook-convert if available
                    try:
                        from converters import ebook_convert
                        out_path = ebook_convert(p, tgt, output_dir=OUTPUT_DIR)
                    except Exception as e:
                        raise RuntimeError('EBook conversion cần Calibre (ebook-convert). ' + str(e))
                elif cat == 'Vector':
                    raise RuntimeError('Chuyển đổi Vector chưa được bật — có thể cần Inkscape/ImageMagick')
                elif cat == 'Video':
                    if not is_tool('ffmpeg'):
                        raise RuntimeError('ffmpeg không tìm thấy — cài ffmpeg để chuyển đổi video')
                    out_path = convert_video_ffmpeg(p, tgt, output_dir=OUTPUT_DIR)
                else:
                    raise RuntimeError('Thể loại không hợp lệ')

                if out_path and os.path.exists(out_path):
                    self.status.config(text=f'Hoàn tất: {out_path}')
                    messagebox.showinfo('Hoàn tất', f'Đã tạo file: {out_path}\nMở thư mục outputs để xem.')
                else:
                    raise RuntimeError('Không tạo được file kết quả')
        except Exception as e:
            messagebox.showerror('Lỗi khi chuyển đổi', str(e))
            self.status.config(text=f'Lỗi: {e}')
        finally:
            self.btn_convert.config(state=tk.NORMAL)

if __name__ == '__main__':
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()
