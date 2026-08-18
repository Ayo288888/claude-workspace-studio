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

    # Handle Images (for Claude Vision API & Pasted Images)
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"] or mime.startswith("image/"):
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
    Safely formats a single processed file or a list of processed files into a clean prompt context string.
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

def build_anthropic_message_content(
    prompt_text: str,
    processed_files: List[Dict[str, Any]],
    web_context: str = ""
) -> Union[str, List[Dict[str, Any]]]:
    """
    Constructs the exact Claude Messages API content payload,
    seamlessly supporting Multimodal Vision (pasted/uploaded images) + Text files.
    """
    has_images = any(f.get("type") == "image" for f in processed_files)
    
    if not has_images:
        text_context = format_file_for_prompt(processed_files)
        full = prompt_text
        if text_context:
            full = full + "\n\n" + text_context
        if web_context:
            full = full + "\n\n" + web_context
        return full

    # Multimodal Vision Content Blocks
    blocks: List[Dict[str, Any]] = []
    
    # 1. Attach image blocks
    for f in processed_files:
        if f.get("type") == "image" and f.get("base64"):
            blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": f.get("media_type", "image/png"),
                    "data": f.get("base64")
                }
            })
        elif f.get("type") == "text":
            blocks.append({
                "type": "text",
                "text": f"--- Attached File: {f.get('name')} ---\n{f.get('content')}"
            })

    # 2. Main text query + web context
    user_query = prompt_text
    if web_context:
        user_query += f"\n\n{web_context}"
    blocks.append({
        "type": "text",
        "text": user_query
    })
    
    return blocks
