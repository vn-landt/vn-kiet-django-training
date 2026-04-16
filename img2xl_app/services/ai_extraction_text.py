# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import json
import base64
import urllib
from google.appengine.api import urlfetch
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

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