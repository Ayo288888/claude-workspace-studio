import base64
import io
import os
from typing import Any, Dict, Optional
import pdfplumber
import docx

def get_mime_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    mimes = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".py": "text/x-python",
        ".json": "application/json",
        ".js": "text/javascript",
        ".ts": "text/typescript",
        ".html": "text/html",
        ".css": "text/css",
        ".sql": "text/plain",
        ".csv": "text/csv",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    return mimes.get(ext, "application/octet-stream")

def process_raw_file(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    ext = os.path.splitext(filename)[1].lower()
    mime = get_mime_type(filename)

    # Handle Images
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        return {
            "type": "image",
            "name": filename,
            "media_type": mime,
            "base64": b64,
            "content": f"[Image: {filename}]"
        }

    # Handle PDF
    if ext == ".pdf":
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                extracted = page.extract_text() or ""
                text_parts.append(f"--- Page {i+1} ---\n{extracted}")
        return {
            "type": "text",
            "name": filename,
            "media_type": mime,
            "content": "\n\n".join(text_parts)
        }

    # Handle DOCX
    if ext == ".docx":
        doc = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        return {
            "type": "text",
            "name": filename,
            "media_type": mime,
            "content": text
        }

    # Handle Text / Code / Markdown
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1", errors="replace")

    return {
        "type": "text",
        "name": filename,
        "media_type": mime,
        "content": text
    }

def format_file_for_prompt(file_info: Dict[str, Any]) -> str:
    if file_info["type"] == "image":
        return f"[Attached Image: {file_info['name']}]"
    return f"\n\n```\n--- File: {file_info['name']} ---\n{file_info['content']}\n```\n"
