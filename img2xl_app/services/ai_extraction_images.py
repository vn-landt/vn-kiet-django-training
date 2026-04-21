# -*- coding: utf-8 -*-
import io, os
import csv
import json
import logging
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import get_object_or_404
from google.appengine.api import urlfetch

from .table_handler import TableFileHandler
from .upload_image import _save_uploaded_file
from ..models import ExtractedResult, Notification, UsageLog

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


# =====================================================================
# 1. UNIFIED API ENDPOINT
# =====================================================================
def generate_images(user, files, is_create_new, current_result_id, languages,expiry_date):
	"""
	API duy nhất xử lý trích xuất cho cả 1 ảnh hoặc nhiều ảnh.
	Frontend có thể gửi 1 file qua key 'file' hoặc danh sách qua key 'files'.
	"""
	uploaded_ids = []
	image_urls = []
	
	# BƯỚC 1: XỬ LÝ UPLOAD (Nén + Upload ImgBB + Lưu Model UploadedFile)
	for f in files:
		# (Hàm này nên abo gồm: nén -> upload -> create UploadedFile object)
		uf, error = _save_uploaded_file(user, f, f.name, expiry_date)
		if uf:
			uploaded_ids.append(uf.id)
			image_urls.append(uf.image_url)
		else:
			logging.error(u"Upload error for file %s: %s", f.name, error)
	
	if not image_urls:
		return {'status': 'error', 'message': u'Không thể upload ảnh.'}
	
	# BƯỚC 2: GỌI GEMINI (Logic chung cho 1 hoặc nhiều ảnh)
	result_text, ai_error = generate_images_with_gemini(image_urls, languages)
	
	if ai_error:
		return {'status': 'error', 'message': ai_error}
	
	if result_text == "INVALID_DOCUMENT":
		return {'status': 'error', 'message': u'Tài liệu không hợp lệ hoặc chứa khuôn mặt người.'}
	
	# BƯỚC 3: PARSE CSV VÀ LƯU DATABASE
	table_data, parse_error = _parse_csv_to_table(result_text)
	if parse_error:
		return {'status': 'error', 'message': parse_error}
	
	res_obj = None
	
	# Trường hợp 1: Tạo bảng mới hoàn toàn (Home hoặc Batch)
	if is_create_new or not current_result_id:
		title = u"Bảng từ " + files[0].name if len(files) == 1 \
							else (u"Bảng từ batch_img " + timezone.now().strftime("%d/%m/%Y %H:%M"))
		res_obj = ExtractedResult.objects.create(
			user=user,
			title=title,
			source_file_ids=uploaded_ids,
			status='success',
			processed_at=timezone.now()
		)
		handler = TableFileHandler(res_obj)
		handler.save_data(table_data, is_final=True)
		
		# Gửi thông báo
		Notification.objects.create_notification(
			user=user, title=u"Thành công!", message=u"Đã tạo bảng: {}".format(res_obj.title),
			level='success', linked_to=reverse('result_detail', kwargs={'result_id': res_obj.id})
		)
	
	# Trường hợp 2: Cập nhật dữ liệu vào bảng đang mở (Chỉ lưu vào Draft)
	else:
		res_obj = get_object_or_404(ExtractedResult, id=current_result_id, user=user)
		# Thêm ID ảnh mới vào list source
		new_ids = list(set(res_obj.source_file_ids + uploaded_ids))
		res_obj.source_file_ids = new_ids
		res_obj.save()
		
		handler = TableFileHandler(res_obj)
		handler.save_data(table_data, is_final=False)
	
	# Cập nhật Log sử dụng
	usage, _ = UsageLog.objects.get_or_create(user=user, usage_date=timezone.now().date())
	usage.upload_count += len(image_urls)
	usage.save()
	
	return {
		'status': 'success',
		'result_id': res_obj.id,
		'table': table_data
	}

# =====================================================================
# 2. HELPER METHOD
# =====================================================================
def _parse_csv_to_table(result_text):
	"""Làm sạch Markdown và chuyển CSV string thành list python"""
	if not result_text:
		return None, u"Không có dữ liệu trả về từ AI."
	
	cleaned_text = result_text.strip()
	
	# 1. Xử lý Markdown Code Block
	if '```csv' in cleaned_text:
		cleaned_text = cleaned_text.split('```csv')[1].split('```')[0].strip()
	elif '```' in cleaned_text:
		cleaned_text = cleaned_text.split('```')[1].strip()
	
	if cleaned_text == 'NO_TABLE_FOUND' or not cleaned_text:
		return None, u"Không tìm thấy bảng dữ liệu trong ảnh."
	
	try:
		# 2. Sử dụng StringIO cho Python 3 (Xử lý text trực tiếp)
		f = io.StringIO(cleaned_text)
		reader = csv.reader(f, delimiter=',')
		
		# 3. Chuyển thành list và strip() từng ô dữ liệu
		table_data = []
		for row in reader:
			if any(field.strip() for field in row):  # Chỉ lấy dòng có dữ liệu
				clean_row = [field.strip() for field in row]
				table_data.append(clean_row)
		
		# 4. Kiểm tra tính hợp lệ của bảng
		if not table_data:
			return None, u"Dữ liệu bảng trống."
		
		# Lọc bỏ các dòng chỉ có 1 cột nếu bảng có nhiều cột (Tránh dòng rác)
		max_cols = max(len(row) for row in table_data)
		if max_cols > 1:
			table_data = [row for row in table_data if len(row) > 1]
		
		return table_data, None
	
	except Exception as e:
		return None, u"Lỗi phân tích cú pháp CSV: " + str(e)


# =====================================================================
# 3. CORE AI LOGIC (UNIFIED)
# =====================================================================
def generate_images_with_gemini(image_urls, languages='all', mime_type="image/jpeg"):
	"""
	Hàm thống nhất trích xuất dữ liệu từ 1 hoặc nhiều ảnh bằng Gemini 2.5 Flash.
	Chấp nhận: 1 chuỗi URL duy nhất HOẶC 1 danh sách các URL.
	"""
	# 1. CHUẨN HÓA ĐẦU VÀO (Xử lý cả string đơn lẻ hoặc list)
	if isinstance(image_urls, basestring):
		image_urls = [image_urls]
	
	is_multi = len(image_urls) > 1
	api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + GEMINI_API_KEY
	
	# 2. XỬ LÝ CHỈ DẪN NGÔN NGỮ
	lang_instruction = u"Language Instruction: Please auto-detect the languages and extract text accordingly."
	if languages != 'all' and languages:
		lang_instruction = u"Language Instruction: The document primarily contains text in these languages: {}. Please ensure high accuracy.".format(
			languages)
	
	# 3. XÂY DỰNG PROMPT TỔNG HỢP (Gộp logic Multi-page và Single-page)
	prompt_text = u"""
	CRITICAL INSTRUCTION:
	Before processing, check the image content:
	1. If any image contains a human face.
	2. If the images are NOT receipts, invoices, bills, or structured data tables.
	If either condition is met, your ONLY response must be: INVALID_DOCUMENT

	If valid, proceed with extraction:
	---
	You are a high-precision data extraction engine. Convert the tables/lists into a single, machine-parsable CSV string.

	**Your Extraction Strategy:**

	You must process the data using the following hierarchical strategy. Attempt Step 1 first. Only if it fails, proceed to Step 2.

	**Step 1: The "Header-First" Method (Primary Strategy for PDFs & Formal Tables)**

	1.  **Find a Header Row:** Scan the entire text for a single line that clearly functions as a table header. Headers typically contain words like "S.N.", "Item", "Description", "Quantity", "Rate", "Amount", "Price", etc.
	2.  **Apply Strict Structure:** If a clear header row is identified:
	    * Use that line as your CSV header.
	    * Assume all subsequent lines that follow a consistent pattern are rows of that table. The number of columns is now strictly defined by this header.
	    * Extract every column found. Do not merge or simplify data.
	    * **Crucially, identify and discard any repeated header rows** that may appear in the middle of the data.

	**Step 2: The "Flexible List" Method (Fallback for Handwriting & Simple Lists)**

	* **Condition:** Use this method **only if** you cannot identify a clear header row in Step 1.
	* **Action:** Look for a simple itemized list (e.g., lines starting with numbers like `1.`, `(2)`, or bullets).
	* **Structure:**
	    * Create a simple 2 or 3-column CSV with headers like "No.", "Description", and optionally "Details".
	    * Merge any inconsistent data into the "Description" column to maintain a valid CSV structure.

	**Multi-Image/Merging Logic:**
	{multi_logic}

	**Universal Formatting Rules (Apply to ALL Outputs):**

	* **IMPERATIVE Quoting Rule:** If any cell value contains a comma, the entire value **MUST** be enclosed in double quotes (`"`).
	* **Row Consistency:** Every row in the final CSV must have the exact same number of commas. Represent empty cells as an empty field (e.g., `value1,,value3`).
	* **Special Text:** Append ` [CROSSED_OUT]` to any text that is clearly struck-through.
	* **Ignore Noise:** Discard all unrelated text: page numbers, company logos, addresses, signatures, etc.

	**Final Output Requirements (Strictly Enforced):**
	1.  **If Data Found:** Your response **must ONLY be the pure CSV string**.
	2.  **If No Data Found:** Your response **must ONLY be the exact string: `NO_TABLE_FOUND`**.
	3.  **DO NOT** include any explanations, summaries, or markdown formatting.
	    """.format(
		multi_logic=u"- If multiple images are provided, they are consecutive pages. Merge them into ONE single CSV table." if is_multi else u""
	)
	
	# 4. CHUẨN BỊ PARTS (Prompt Text + List Images)
	parts = [{"text": prompt_text + "\n" + lang_instruction}]
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
			"temperature": 0.1,  # Luôn dùng mức thấp nhất để đảm bảo tính chính xác dữ liệu
			"maxOutputTokens": 8192 if is_multi else 4096,
		}
	}
	
	# 5. GỌI API QUA URLFETCH
	try:
		res = urlfetch.fetch(
			url=api_url,
			payload=json.dumps(payload),
			method=urlfetch.POST,
			headers={"Content-Type": "application/json"},
			deadline=90
		)
		
		if res.status_code != 200:
			logging.error(u"Gemini API Error: %s", res.content)
			return None, u"Lỗi kết nối AI ({}).".format(res.status_code)
		
		data = json.loads(res.content)
		
		# Parse kết quả an toàn
		try:
			candidates = data.get("candidates", [])
			if not candidates:
				return None, u"AI không trả về kết quả."
			
			text_result = candidates[0].get("content", {}).get("parts", [{}])[0].get("text",
																					 "").strip()
			return text_result, None
		
		except (KeyError, IndexError) as e:
			logging.error(u"Parsing Error: %s", str(e))
			return None, u"Lỗi xử lý phản hồi từ AI."
	
	except urlfetch.Error as e:
		return None, u"Yêu cầu quá hạn hoặc lỗi mạng: " + str(e)
	except Exception as e:
		return None, u"Lỗi hệ thống: " + str(e)
