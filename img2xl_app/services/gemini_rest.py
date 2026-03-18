# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import urllib2
import json
import base64
from cStringIO import StringIO
from PIL import Image
import os

# from dotenv import load_dotenv
# current_dir = os.path.dirname(os.path.abspath(__file__))
# root_dir = os.path.dirname(os.path.dirname(current_dir))
# dotenv_path = os.path.join(root_dir, '.env')
# # Load các biến từ file .env
# load_dotenv(dotenv_path)

# Thay bằng API key thật của bạn (lấy từ https://aistudio.google.com/app/apikey)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Đừng commit key lên git! Nên dùng os.environ hoặc file .env sau này
# Ví dụ: GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

def extract_with_gemini(file_path_or_content, mime_type=None, custom_prompt=None):
    """
    Gọi Gemini 2.5 Flash qua REST API để trích xuất bảng từ ảnh hoặc PDF.
    Trả về: string (text do Gemini trả về, thường là CSV hoặc bảng dạng text)
             hoặc None nếu lỗi
    """
    # if not GEMINI_API_KEY:
    #     print(dotenv_path)
    #     return None, "API key chưa được cấu hình"

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY

    # Xác định mime_type nếu chưa có
    if mime_type is None:
        ext = os.path.splitext(file_path_or_content)[1].lower() if isinstance(file_path_or_content, basestring) else ""
        if ext in ['.jpg', '.jpeg']:
            mime_type = "image/jpeg"
        elif ext == '.png':
            mime_type = "image/png"
        elif ext == '.pdf':
            mime_type = "application/pdf"
        else:
            mime_type = "image/jpeg"  # mặc định

    # Đọc nội dung file
    if isinstance(file_path_or_content, basestring):  # là đường dẫn file
        if not os.path.exists(file_path_or_content):
            return None, "File không tồn tại: " + file_path_or_content
        with open(file_path_or_content, 'rb') as f:
            content = f.read()
    else:
        content = file_path_or_content  # đã là bytes

    # Optional: resize ảnh để tiết kiệm token (chỉ áp dụng cho ảnh)
    if mime_type.startswith('image/') and len(content) > 200 * 1024:
        try:
            img = Image.open(StringIO(content))
            # Giảm xuống 800px để nhẹ hơn nữa cho môi trường GAE
            img.thumbnail((800, 800))
            output = StringIO()
            # Giảm quality xuống 70-80% để tiết kiệm dung lượng
            img.save(output, format='JPEG', quality=80)
            content = output.getvalue()
        except Exception as e:
            # Thay vì print(e) - đôi khi e chứa dữ liệu thô, hãy in thông báo ngắn
            logging.error("Resize failed")

    base64_data = base64.b64encode(content).decode('utf-8')

    # Prompt tốt cho extract bảng
    default_prompt = (
        """
            You are a high-precision, automated data extraction engine. Your only function is to convert the primary table or list from a file into a pure, machine-parsable CSV string.

**Your Extraction Strategy:**

You must process the data using the following hierarchical strategy. Attempt Step 1 first. Only if it fails, proceed to Step 2.

**Step 1: The "Header-First" Method (Primary Strategy for PDFs & Formal Tables)**

1.  **Find a Header Row:** Scan the entire text for a single line that clearly functions as a table header. Headers typically contain words like "S.N.", "Item", "Description", "Quantity", "Rate", "Amount", "Price", etc.
2.  **Apply Strict Structure:** If a clear header row is identified:
    *   Use that line as your CSV header.
    *   Assume all subsequent lines that follow a consistent pattern are rows of that table. The number of columns is now strictly defined by this header.
    *   Extract every column found. Do not merge or simplify data.
    *   **Crucially, identify and discard any repeated header rows** that may appear in the middle of the data, which is a common issue from multi-page PDF extractions.

**Step 2: The "Flexible List" Method (Fallback for Handwriting & Simple Lists)**

*   **Condition:** Use this method **only if** you cannot identify a clear header row in Step 1.
*   **Action:** Look for a simple itemized list (e.g., lines starting with numbers like `1.`, `(2)`, or bullets).
*   **Structure:**
    *   Create a simple 2 or 3-column CSV with headers like "No.", "Description", and optionally "Details".
    *   Merge any inconsistent data (like quantities that only appear on some lines) into the "Description" column to maintain a valid CSV structure.

**Universal Formatting Rules (Apply to ALL Outputs):**

*   **IMPERATIVE Quoting Rule:** If any cell value contains a comma, the entire value **MUST** be enclosed in double quotes (`"`). This is the most critical rule for preventing parser failure.
    *   **Correct Example:** `1,"Item, with comma",100`
    *   **Incorrect Example:** `1,Item, with comma,100`
*   **Row Consistency:** Every row in the final CSV must have the exact same number of commas. Represent empty cells as an empty field (e.g., `value1,,value3`).
*   **Special Text:** Append ` [CROSSED_OUT]` to any text that is clearly struck-through.
*   **Ignore Noise:** Discard all unrelated text: page numbers, company logos, addresses, paragraphs, signatures, and marginalia.

**Final Output Requirements (Strictly Enforced):**

1.  **If Data Found:** Your response **must ONLY be the pure CSV string**.
2.  **If No Data Found:** Your response **must ONLY be the exact string: `NO_TABLE_FOUND`**.
3.  **DO NOT** include any explanations, summaries, or markdown formatting (like ` ```csv `).
            """
    )
    prompt = custom_prompt or default_prompt

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64_data
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 2048
        }
    }

    try:
        req = urllib2.Request(
            url,
            json.dumps(payload),
            {'Content-Type': 'application/json'}
        )
        response = urllib2.urlopen(req)
        result = json.load(response)

        # Lấy text từ response
        try:
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text.strip(), None
        except (KeyError, IndexError):
            return None, "Không tìm thấy nội dung trong response"

    except urllib2.HTTPError as e:
        try:
            error_body = e.read()
            error_json = json.loads(error_body)
            msg = error_json.get('error', {}).get('message', str(e))
        except:
            msg = str(e)
        return None, "HTTP Error %d: %s" % (e.code, msg)

    except Exception as e:
        return None, "Exception: " + str(e)

