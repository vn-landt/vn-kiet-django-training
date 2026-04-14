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
def extract_with_gemini(image_url, mime_type="image/jpeg", custom_prompt=None):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY

    # ... (Giữ nguyên phần text prompt của bạn ở đây) ...
    prompt_text = """... (prompt của bạn) ..."""

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