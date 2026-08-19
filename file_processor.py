import base64
import io
import json
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
        ".ipynb": "application/x-ipynb+json",
        ".json": "application/json",
        ".js": "text/javascript",
        ".ts": "text/typescript",
        ".tsx": "text/typescript",
        ".jsx": "text/javascript",
        ".html": "text/html",
        ".css": "text/css",
        ".sql": "text/plain",
        ".csv": "text/csv",
        ".yaml": "text/yaml",
        ".yml": "text/yaml",
        ".sh": "text/x-sh",
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

    # Handle Jupyter Notebooks (.ipynb)
    if ext == ".ipynb":
        try:
            nb_data = json.loads(file_bytes.decode("utf-8", errors="replace"))
            cells = nb_data.get("cells", [])
            nb_parts = []
            for idx, cell in enumerate(cells):
                cell_type = cell.get("cell_type", "code")
                src = "".join(cell.get("source", []))
                if cell_type == "markdown":
                    nb_parts.append(f"[Notebook Markdown Cell {idx+1}]\n{src}")
                elif cell_type == "code":
                    nb_parts.append(f"[Notebook Code Cell {idx+1}]\n```python\n{src}\n```")
            content = "\n\n".join(nb_parts) if nb_parts else "[Empty Jupyter Notebook]"
        except Exception:
            content = file_bytes.decode("utf-8", errors="replace")
            
        return {
            "type": "text",
            "name": filename,
            "media_type": mime,
            "content": content
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

    # Handle Code / Data / Text / All Other Files
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
    seamlessly supporting Multimodal Vision (pasted/uploaded images) + Notebooks + Code + Text files.
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
    content_blocks = []
    
    # 1. Attach Images as Native Base64 Vision Blocks
    for f in processed_files:
        if f.get("type") == "image" and f.get("base64"):
            media_type = f.get("media_type", "image/png")
            if media_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
                media_type = "image/png"
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": f["base64"]
                }
            })

    # 2. Attach Non-Image Context as Text
    non_images = [f for f in processed_files if f.get("type") != "image"]
    text_context = format_file_for_prompt(non_images) if non_images else ""
    
    full_text_part = prompt_text
    if text_context:
        full_text_part = full_text_part + "\n\n" + text_context
    if web_context:
        full_text_part = full_text_part + "\n\n" + web_context

    if full_text_part:
        content_blocks.append({
            "type": "text",
            "text": full_text_part
        })

    return content_blocks
