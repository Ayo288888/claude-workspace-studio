import base64
import io
import os
from typing import Any, Dict, List, Optional, Union
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

    # Handle Images (for Claude Vision API)
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
        b64 = base64.b64encode(file_bytes).decode("utf-8")
        return {
            "type": "image",
            "name": filename,
            "media_type": mime,
            "base64": b64,
            "content": f"[Image: {filename}]"
        }

    # Handle PDF Documents
    if ext == ".pdf":
        text_parts = []
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for i, page in enumerate(pdf.pages):
                    extracted = page.extract_text() or ""
                    text_parts.append(f"--- Page {i+1} ---\n{extracted}")
            content = "\n\n".join(text_parts) if text_parts else "[Empty PDF document]"
        except Exception as e:
            content = f"[Error reading PDF {filename}: {str(e)}]"
            
        return {
            "type": "text",
            "name": filename,
            "media_type": mime,
            "content": content
        }

    # Handle DOCX Documents
    if ext == ".docx":
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
            content = text if text else "[Empty Word document]"
        except Exception as e:
            content = f"[Error reading DOCX {filename}: {str(e)}]"
            
        return {
            "type": "text",
            "name": filename,
            "media_type": mime,
            "content": content
        }

    # Handle Text / Code / CSV / JSON / Markdown
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

def format_file_for_prompt(files: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
    """
    Safely formats a single processed file or a list of processed files into a clean prompt context block.
    """
    if not files:
        return ""
        
    if isinstance(files, dict):
        file_list = [files]
    else:
        file_list = files

    formatted_blocks = []
    for f in file_list:
        if not isinstance(f, dict):
            continue
        fname = f.get("name", "uploaded_file")
        ftype = f.get("type", "text")
        if ftype == "image":
            formatted_blocks.append(f"[Attached Image: {fname}]")
        else:
            content = f.get("content", "")
            formatted_blocks.append(f"```\n--- File: {fname} ---\n{content}\n```")

    return "\n\n".join(formatted_blocks)
