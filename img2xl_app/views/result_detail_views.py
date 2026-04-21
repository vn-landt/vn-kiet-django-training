# -*- coding: utf-8 -*-
from datetime import timedelta
from django.utils import timezone

import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from img2xl_app.models import ExtractedResult
from img2xl_app.services.ai_extraction_images import generate_images_with_gemini
from img2xl_app.services.ai_extraction_text import generate_text_with_gemini
from img2xl_app.services.table_handler import TableFileHandler


def result_detail(request, result_id):
    result = get_object_or_404(ExtractedResult, pk=result_id)

    # 1. Lấy dữ liệu từ handler (dạng list của Python)
    raw_table_data = result.get_table(for_export=False)
    raw_final_data = result.get_table(for_export=True)

    # 2. CHUYỂN THÀNH CHUỖI JSON (Sẽ mất ký tự 'u' và biến None thành null)
    # ensure_ascii=False giúp giữ nguyên tiếng Việt
    table_json_str = json.dumps(raw_table_data, ensure_ascii=False)
    final_table_json_str = json.dumps(raw_final_data, ensure_ascii=False)

    # Sử dụng timezone.localtime để chuyển từ UTC sang Asia/Ho_Chi_Minh
    local_draft_time = timezone.localtime(result.updated_at)
    last_draft_time = local_draft_time.strftime('%d/%m/%Y %H:%M:%S')

    # Thời gian bản chính (Modal)
    last_final_time = "Chưa lưu"
    if result.processed_at:
        last_final_time = timezone.localtime(result.processed_at).strftime('%d/%m/%Y %H:%M:%S')

    recent_results = ExtractedResult.objects.filter(
            is_deleted=False
    ).order_by('-created_at')
    return render(request, 'img2xl_app/result_detail.html', {
        'result': result,
        'table_json': table_json_str,
        'final_table_json': final_table_json_str,
        'recent_results': recent_results,
        'last_draft_time': last_draft_time,
        'last_final_time': last_final_time,
    })

@require_POST
def update_table_data(request, result_id):
    if request.method == 'POST':
        result = ExtractedResult.objects.get(pk=result_id, user=request.user)
        data = json.loads(request.body)

        # Lấy flag từ frontend: if is_draft=True -> lưu nháp, if False -> lưu final
        is_draft_request = data.get('is_draft', True)

        handler = TableFileHandler(result)
        # Nếu is_draft_request là False nghĩa là người dùng bấm nút Save Changes (is_final=True)
        success = handler.save_data(data.get('table_data'), is_final=not is_draft_request)

        result.refresh_from_db()  # Lấy dữ liệu mới nhất vừa lưu vào DB

        # Chuyển về giờ Việt Nam và định dạng chuỗi đầy đủ
        local_now = timezone.localtime(result.updated_at)
        full_time_str = local_now.strftime('%d/%m/%Y %H:%M:%S')

        return JsonResponse({
            'status': 'success',
            'updated_at':full_time_str ,  # Trả về giờ VN
            'is_draft': result.is_draft
        })
    
@csrf_protect
def generate_ai_content(request):
    """
    API nhận prompt từ giao diện và trả về văn bản từ Gemini
    """
    if request.method == 'POST':
        try:
            # Parse dữ liệu JSON từ request body
            data = json.loads(request.body)
            prompt_text = data.get('prompt', '')
            target_cell = data.get('cell', '')

            if not prompt_text:
                return JsonResponse({
                    'status': 'error',
                    'message': u'Nội dung yêu cầu không được để trống.'
                })

            # Gọi hàm từ services.py
            # prompt_text có thể cần decode/encode nếu là tiếng Việt trong Py 2.7
            result, error = generate_text_with_gemini(prompt_text)

            if error:
                return JsonResponse({
                    'status': 'error',
                    'message': error
                })
            return JsonResponse({
                'status': 'success',
                'result': result,
                'cell': target_cell
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    return JsonResponse({'status': 'error', 'message': 'Invalid Method'})



