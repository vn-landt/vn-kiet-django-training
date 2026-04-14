# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json
import base64
import urllib
from google.appengine.api import urlfetch
from PIL import Image
from dotenv import load_dotenv
from .compress_image import compress_image

load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")


# =====================================
# 🔹 Upload ảnh lên ImgBB bằng urlfetch
# =====================================
def upload_to_imgbb(image_bytes):
    url = "https://api.imgbb.com/1/upload"

    # Encode payload chuẩn form-urlencoded
    payload = urllib.urlencode({
        "key": IMGBB_API_KEY,
        "image": base64.b64encode(image_bytes)
    })

    try:
        res = urlfetch.fetch(
            url=url,
            payload=payload,
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            deadline=30
        )

        if res.status_code != 200:
            return None, "HTTP Error: " + str(res.status_code)

        data = json.loads(res.content)

        if not data.get("success"):
            return None, str(data)

        return data["data"]["url"], None

    except urlfetch.Error as e:
        return None, "GAE urlfetch error: " + str(e)
    except Exception as e:
        return None, "Unexpected: " + str(e)


# =====================================
# 🔹 Gọi Gemini bằng urlfetch
# =====================================
def extract_image_with_gemini(image_url, mime_type="image/jpeg", languages='All Languages'):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY

    # 1. Chuyển đổi mã ngôn ngữ thành câu lệnh (Prompt) rõ ràng cho AI
    lang_instruction = u""
    if languages == 'all' or not languages:
        lang_instruction = u"Language Instruction: Please auto-detect the languages in the document and extract the text accordingly."
    else:
        # Nếu languages là 'vie,eng', câu lệnh sẽ là: "... primarily contains these language codes: vie,eng..."
        lang_instruction = "Language Instruction: The document primarily contains text in these languages: " + languages +". Please ensure highly accurate character extraction for these specific languages."

    prompt_text = """
CRITICAL INSTRUCTION:
Before processing, check the image content:
1. If the image contains a human face.
2. If the image is NOT a receipt, invoice, bill, or a structured data table.

If either condition is met, your ONLY response must be: INVALID_DOCUMENT

If the image is a valid document, proceed with the extraction below:
---
You are a high-precision, automated data extraction engine. Your only function is to convert the primary table or list from a file into a pure, machine-parsable CSV string.
    """
    prompt_text += lang_instruction
    prompt_text += """
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

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt_text},
                {
                    "file_data": {
                        "mime_type": mime_type,
                        "file_uri": image_url
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 4096,
        }
    }

    try:
        res = urlfetch.fetch(
            url=url,
            payload=json.dumps(payload),
            method=urlfetch.POST,
            headers={"Content-Type": "application/json"},
            deadline=90  # API AI thường cần timeout dài
        )

        if res.status_code != 200:
            return None, "Gemini HTTP error {}: {}".format(res.status_code, res.content)

        data = json.loads(res.content)

        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return None, "No candidates in response"

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                return None, "No parts in content"

            text = parts[0].get("text", "").strip()
            return text, None

        except Exception as e:
            return None, "Parse error: " + str(e) + "\nRaw: " + res.content

    except urlfetch.Error as e:
        return None, "GAE urlfetch Request failed: " + str(e)
    except Exception as e:
        return None, "Unexpected: " + str(e)


def extract_multi_images_with_gemini(image_urls, languages='all', mime_type="image/jpeg"):
    """
    image_urls: Có thể là 1 string URL hoặc 1 danh sách [url1, url2, ...]
    """
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY

    # Chuyển đổi sang list nếu chỉ có 1 URL
    if isinstance(image_urls, basestring):
        image_urls = [image_urls]

    # 1. Chuyển đổi mã ngôn ngữ thành câu lệnh (Prompt)
    lang_instruction = u""
    if languages == 'all' or not languages:
        lang_instruction = u"Language Instruction: Please auto-detect the languages in the document and extract the text accordingly."
    else:
        lang_instruction = "Language Instruction: The document primarily contains text in những ngôn ngữ này: " + languages + ". Please ensure highly accurate character extraction."

    # 2. Xây dựng Prompt Core
    prompt_text = u"""
CRITICAL INSTRUCTION:
Before processing, check the image content:
1. If any image contains a human face.
2. If the images are NOT receipts, invoices, bills, or structured data tables.
If either condition is met, your ONLY response must be: INVALID_DOCUMENT

If valid, proceed with the extraction:
---
You are a high-precision, automated data extraction engine. Your task is to convert the tables/lists from the provided file(s) into a single, machine-parsable CSV string.

**MULTI-IMAGE LOGIC:**
- If multiple images are provided, they represent consecutive pages of the same document. 
- Merge all data into ONE single CSV. 
- **CRITICAL:** For every row extracted, you MUST append exactly two empty columns at the end of the row (i.e., add two commas `,,` at the end of each line).
"""
    prompt_text += lang_instruction
    prompt_text += u"""
**Your Extraction Strategy:**
Attempt Step 1 first. Only if it fails, proceed to Step 2.

**Step 1: The "Header-First" Method (Primary Strategy)**
1. Find a Header Row in the first image.
2. Apply Strict Structure: Use that header for the entire CSV. Identify and discard any repeated header rows found in subsequent images.
3. Every extracted row must follow the column count of this header, then append two empty columns `,,` at the end.

**Step 2: The "Flexible List" Method (Fallback)**
- Action: Look for itemized lists. Create a 2 or 3-column CSV.
- Structure: Merge inconsistent data into "Description". Append two empty columns `,,` at the end of every row.

**Universal Formatting Rules:**
- **IMPERATIVE Quoting Rule:** If any cell contains a comma, enclose the value in double quotes (`"`).
- **Row Consistency:** Every row must have the exact same number of commas. 
- **Separation Rule:** Remember to add `,,` at the end of each row to separate data as requested.
- **Ignore Noise:** Discard page numbers, logos, and signatures.

**Final Output Requirements:**
1. Your response must ONLY be the pure CSV string.
2. If no data: `NO_TABLE_FOUND`.
3. NO explanations, NO markdown code blocks (```csv).
"""

    # 3. Xây dựng cấu trúc Parts cho Gemini (Prompt + Danh sách ảnh)
    parts = [{"text": prompt_text}]
    for img_url in image_urls:
        parts.append({
            "file_data": {
                "mime_type": mime_type,
                "file_uri": img_url
            }
        })

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": 0.1, # Giảm xuống để trích xuất chính xác hơn
            "maxOutputTokens": 8192, # Tăng lên để chứa đủ dữ liệu nhiều ảnh
        }
    }

    try:
        res = urlfetch.fetch(
            url=url,
            payload=json.dumps(payload),
            method=urlfetch.POST,
            headers={"Content-Type": "application/json"},
            deadline=90
        )

        if res.status_code != 200:
            return None, "Gemini HTTP error {}: {}".format(res.status_code, res.content)

        data = json.loads(res.content)
        try:
            candidates = data.get("candidates", [])
            if not candidates:
                return None, "No candidates in response"

            content = candidates[0].get("content", {})
            res_parts = content.get("parts", [])
            if not res_parts:
                return None, "No parts in content"

            text = res_parts[0].get("text", "").strip()
            return text, None

        except Exception as e:
            return None, "Parse error: " + str(e) + "\nRaw: " + res.content

    except urlfetch.Error as e:
        return None, "GAE urlfetch Request failed: " + str(e)
    except Exception as e:
        return None, "Unexpected: " + str(e)

def generate_text_with_gemini(custom_prompt):
    """
    Hàm này nhận vào một đoạn text và trả về kết quả từ Gemini.
    Dùng cho chức năng 'Generate Formula' hoặc Assistant.
    """
    # Sử dụng model flash để có tốc độ phản hồi nhanh nhất
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY

    custom_prompt = ('No explanation or analysis needed, just give the command to copy and insert into the Excel cell immediately to '
                     'perform this request (excluding special characters, starting with the equals sign =): '
                     +custom_prompt)

    # Cấu trúc payload cho yêu cầu chỉ có văn bản
    payload = {
        "contents": [{
            "parts": [
                {"text": custom_prompt}
            ]
        }],
        "generationConfig": {
            "temperature": 0.7,  # Tăng một chút sáng tạo cho yêu cầu văn bản
            "maxOutputTokens": 2048,
        }
    }

    try:
        res = urlfetch.fetch(
            url=url,
            payload=json.dumps(payload),
            method=urlfetch.POST,
            headers={"Content-Type": "application/json"},
            deadline=60
        )

        if res.status_code != 200:
            return None, "Gemini API Error {}: {}".format(res.status_code, res.content)

        data = json.loads(res.content)

        # Parse kết quả từ cấu trúc JSON của Gemini
        try:
            text = data['candidates'][0]['content']['parts'][0]['text'].strip()
            return text, None
        except (KeyError, IndexError):
            return None, "Could not parse AI response. Raw: " + res.content

    except urlfetch.Error as e:
        return None, "Network error (urlfetch): " + str(e)
    except Exception as e:
        return None, "Unexpected error: " + str(e)