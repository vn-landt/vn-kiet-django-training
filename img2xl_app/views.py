# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import io
import csv
import os
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from .forms import UploadFileForm
from .models import UploadedFile, ExtractedResult
from .services.bridge import process_and_save_extraction
from django.urls import reverse
from .services.sheets_export import export_to_google_sheets
from .services.compress_image import compress_image
from .services.gemini_rest import upload_to_imgbb, generate_text_with_gemini
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .services.table_handler import TableFileHandler

def home(request):
    # List of recent extractions for history
    recent_results = ExtractedResult.objects.order_by('-created_at')[:10]

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
            if uploaded_file.content_type not in allowed_types:
                return HttpResponse("Error: Only JPG, PNG, PDF allowed.")

            if uploaded_file.size > 10 * 1024 * 1024:
                return HttpResponse("Error: File too large (max 10MB).")

            file_bytes = uploaded_file.read()

            # 🔥 (optional) nén nhẹ
            compressed_bytes = compress_image(io.BytesIO(file_bytes))

            if hasattr(compressed_bytes, "getvalue"):
                compressed_bytes = compressed_bytes.getvalue()

            # 🔥 upload lên ImgBB
            image_url, error = upload_to_imgbb(compressed_bytes)

            if error:
                return HttpResponse("Upload failed: " + error)

            # 🔥 KHÔNG lưu blob nữa
            uf = UploadedFile.objects.create(
                filename=uploaded_file.name,
                mime_type=uploaded_file.content_type,
                image_url=image_url,
                file_size=len(compressed_bytes)
            )

            extraction_result = process_and_save_extraction(uf)

            if extraction_result['status'] == 'error':
                return HttpResponse("Processing failed: " + extraction_result['error'])

            table_data = extraction_result['table']

            # Redirect to detail page
            return render(request, 'result_detail.html', {
                'result': ExtractedResult.objects.get(id=extraction_result['result_id']),
                'table': table_data,
                'table_json': json.dumps(table_data)  # <--- THÊM DÒNG NÀY
            })

        else:
            return HttpResponse("Invalid form.")

    else:
        form = UploadFileForm()

    return render(request, 'home.html', {
        'form': form,
        'recent_results': recent_results
    })


def result_detail(request, result_id):
    result = get_object_or_404(ExtractedResult, id=result_id)
    table = result.get_table()
    return render(request, 'result_detail.html', {
        'result': result,
        'table': table,
        'table_json': json.dumps(table)
    })


def download_csv(request, result_id):
    result = get_object_or_404(ExtractedResult, id=result_id)
    table = result.get_table()  # Giờ đã trả về mảng 2 chiều chuẩn

    response = HttpResponse(content_type='text/csv')
    response.write('\xef\xbb\xbf')  # Thêm BOM để Excel đọc đúng tiếng Việt

    filename = result.uploaded_file.filename.replace(' ', '_')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename

    writer = csv.writer(response)

    for row in table:
        # row giờ đây là một List (VD: ['1.', 'Wheel chair', '1'])
        clean_row = []

        for cell in row:
            # Xử lý an toàn cho Python 2.7: Ép kiểu về unicode rồi encode utf-8
            if cell is None:
                cell_text = u""
            elif not isinstance(cell, unicode):
                cell_text = unicode(str(cell), 'utf-8', errors='ignore')
            else:
                cell_text = cell

            clean_row.append(cell_text.strip().encode('utf-8'))

        # Lọc: Chỉ ghi vào CSV nếu dòng đó có ít nhất 1 ô chứa dữ liệu
        if any(clean_row):
            writer.writerow(clean_row)

    return response


def export_to_sheets(request, result_id):
    result = get_object_or_404(ExtractedResult, id=result_id)
    table = result.get_table()

    if not table:
        return HttpResponse("No table data to export.", status=400)

    sheet_url, error = export_to_google_sheets(table, result.uploaded_file.filename)

    if error:
        return HttpResponse("Export failed: " + error)

    # Redirect to the sheet or show link
    return HttpResponse(
        "<h2>Exported to Google Sheets Successfully!</h2>"
        "<p>Open your sheet here: <a href='{url}' target='_blank'>{url}</a></p>"
        "<br><a href='{detail_url}'>Back to result</a>".format(
            url=sheet_url,
            detail_url=reverse('result_detail', args=[result_id])
        )
    )


def delete_result(request, result_id):
    if request.method == 'POST':
        result = get_object_or_404(ExtractedResult, id=result_id)

        # Khởi tạo Handler và dọn dẹp file vật lý trước
        handler = TableFileHandler(result.id)
        handler.delete_file()

        # Sau đó mới xóa Database
        result.uploaded_file.delete()
        result.delete()

    return redirect('home')


@require_POST
def update_table_data(request, result_id):
    """
    API để nhận dữ liệu bảng Excel chỉnh sửa từ frontend và lưu vào Database.
    """
    try:
        result = get_object_or_404(ExtractedResult, id=result_id)

        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        new_table_data = body_data.get('table_data')

        if new_table_data is None:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy dữ liệu.'}, status=400)

        # Gọi Handler xử lý nén và lưu đè
        handler = TableFileHandler(result)
        if handler.save_data(new_table_data):
            return JsonResponse({'status': 'success', 'message': 'Đã lưu thay đổi thành công!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Lưu thất bại.'}, status=500)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_protect
def ai_generate_view(request):
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