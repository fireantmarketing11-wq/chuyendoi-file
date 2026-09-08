# Test đơn giản: chuyển text -> pdf
import os
from converters import text_to_pdf

def test_text_to_pdf_creates_file(tmp_path):
    sample = tmp_path / "example.txt"
    sample.write_text("Xin chào\nThử chuyển thành PDF.")
    out = text_to_pdf(str(sample), output_dir=str(tmp_path))
    assert os.path.exists(out)
    assert out.endswith(".pdf")
