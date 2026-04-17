# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import urllib

from PIL import Image
import io, os
import json
import base64
from google.appengine.api import urlfetch

from img2xl_app.models import UploadedFile


IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")


def compress_image(content):
	try:
		img = Image.open(io.BytesIO(content))
		
		if img.mode in ("RGBA", "P"):
			img = img.convert("RGB")
		
		img.thumbnail((768, 768))
		
		output = io.BytesIO()
		img.save(output, format='JPEG', quality=70)
		
		return output.getvalue()
	
	except Exception as e:
		print("Preprocess error:", e)
		return content


def _save_uploaded_file(user, uploaded_file, filename, expiry_date=None):
	"""
	Quy trình: Đọc file -> Nén -> Upload ImgBB -> Lưu DB -> Trả về Object
	"""
	try:
		# 1. Đọc dữ liệu từ file object (Django UploadedFile)
		file_bytes = uploaded_file.read()
		mime_type = uploaded_file.content_type
		
		# 2. Nén ảnh (Sử dụng hàm compress_image bạn đã có hoặc hàm xử lý bytes)
		# Mục đích: Giảm dung lượng để upload nhanh hơn và tiết kiệm bộ nhớ ImgBB
		compressed_bytes = compress_image(io.BytesIO(file_bytes))
		if hasattr(compressed_bytes, "getvalue"):
			compressed_bytes = compressed_bytes.getvalue()
		
		# 3. Upload lên ImgBB bằng hàm bạn vừa viết
		image_url, error = upload_to_imgbb(compressed_bytes)
		if error:
			return None, u"Lỗi upload ảnh: " + str(error)
		
		# 4. Lưu thông tin vào Database (Model UploadedFile)
		# Việc lưu này giúp bạn quản lý được user nào đã upload bao nhiêu, khi nào xóa
		uf = UploadedFile.objects.create(
			user=user,
			filename=filename,
			mime_type=mime_type,
			image_url=image_url,
			file_size=len(compressed_bytes),
			delete_at=expiry_date
		)
		
		return uf, None
	
	except Exception as e:
		logging.error("Error in _save_uploaded_file: %s", str(e))
		return None, str(e)


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
