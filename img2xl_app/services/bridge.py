# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import json
from cStringIO import StringIO
from ..models import UploadedFile, ExtractedResult
from django.utils import timezone
from .gemini_rest import extract_image_with_gemini
from .table_handler import TableFileHandler

def process_and_save_extraction(uploaded_file_instance):
    """
    Bridge: Process file, call Gemini, parse, and save to model.

    Args:
        uploaded_file_instance (UploadedFile): Model instance already saved

    Returns:
        dict: Result with status, table, etc.
    """
    result_obj = ExtractedResult.objects.create(
        uploaded_file=uploaded_file_instance,
        status='processing'
    )

    try:
        # Call Gemini
        result_text, error = extract_image_with_gemini(
            uploaded_file_instance.image_url,
            mime_type=uploaded_file_instance.mime_type
        )

        if error:
            result_obj.status = 'failed'
            result_obj.error_message = error
            result_obj.save()
            return {
                'status': 'error',
                'error': error
            }

        # Clean and parse CSV
        cleaned_text = result_text.strip()

        # 1. Gỡ bỏ Markdown block (Phòng hờ AI lì lợm vẫn bọc ```csv)
        if '```csv' in cleaned_text:
            cleaned_text = cleaned_text.split('```csv')[1].split('```')[0].strip()
        elif '```' in cleaned_text:
            cleaned_text = cleaned_text.split('```')[1].strip()

        # 2. Xử lý trường hợp không tìm thấy bảng theo đúng Prompt
        if cleaned_text == 'NO_TABLE_FOUND':
            result_obj.status = 'failed'
            result_obj.error_message = 'AI did not find any table (NO_TABLE_FOUND)'
            result_obj.save()
            return {'status': 'error', 'error': 'Không tìm thấy bảng dữ liệu trong ảnh.'}

        table_data = []
        try:
            # 3. ĐỌC CSV THUẦN TÚY
            csv_reader = csv.reader(
                StringIO(cleaned_text.encode('utf-8') if isinstance(cleaned_text, unicode) else cleaned_text)
            )
            table_data = [row for row in csv_reader]

            # 4. BỘ LỌC RÁC THẦN THÁNH: Loại bỏ câu chào hỏi
            if table_data:
                # Tìm số lượng cột nhiều nhất trong bảng
                max_cols = max(len(row) for row in table_data)

                # Chỉ giữ lại những dòng có từ 2 cột trở lên (Loại bỏ câu "Here is...")
                # Nếu bảng thực sự chỉ có 1 cột, bạn có thể điều chỉnh lại điều kiện này
                if max_cols > 1:
                    table_data = [row for row in table_data if len(row) > 1]

        except Exception as parse_error:
            result_obj.status = 'failed'
            result_obj.error_message = 'Parse failed: ' + str(parse_error)
            result_obj.save()
            return {'status': 'error', 'error': str(parse_error)}

        # Lưu bản ghi lần 1
        result_obj.raw_response = result_text
        result_obj.status = 'success'
        result_obj.processed_at = timezone.now()
        result_obj.save()

        # Gọi Handler để nén zlib và lưu (OOP)
        handler = TableFileHandler(result_obj)
        handler.save_data(table_data)

        return {
            'status': 'success',
            'table': table_data,
            'raw_csv': cleaned_text,
            'result_id': result_obj.id
        }
    except Exception as e:
        result_obj.status = 'failed'
        result_obj.error_message = str(e)
        result_obj.save()
        return {
            'status': 'error',
            'error': str(e)
        }