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
    table = result.get_table()  # Giả sử trả về ["|||", "|S.No|..."]

    response = HttpResponse(content_type='text/csv')
    response.write('\xef\xbb\xbf')  # Thêm BOM để Excel đọc đúng tiếng Việt
    filename = result.uploaded_file.filename.replace(' ', '_')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % filename

    writer = csv.writer(response)

    for item in table:
        # 1. Đảm bảo item là chuỗi Unicode (Python 2.7)
        if not isinstance(item, unicode):
            item = unicode(str(item), 'utf-8')

        # 2. Tách cột theo dấu |
        raw_parts = item.split(u'|')

        # 3. LỌC: Chỉ giữ lại những phần tử có nội dung thực sự (loại bỏ ||| rỗng)
        # p.strip() dùng để loại bỏ khoảng trắng dư thừa
        clean_row = [p.strip().encode('utf-8') for p in raw_parts if p.strip()]

        # 4. Kiểm tra: Nếu sau khi lọc mà dòng trống (như dòng "||||||") thì bỏ qua không ghi vào CSV
        if clean_row:
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
        # Tìm kết quả, nếu không có trả về lỗi 404
        result = get_object_or_404(ExtractedResult, id=result_id)

        # Nếu bạn muốn xóa luôn cả record UploadedFile liên quan trong database:
        file_record = result.uploaded_file

        # Xóa kết quả (ExtractedResult)
        result.delete()

        # Xóa file (UploadedFile)
        file_record.delete()

        # Trở về trang chủ và tự động làm mới trang
    return redirect('home')


@require_POST
def update_table_data(request, result_id):
    """
    API để nhận dữ liệu bảng Excel chỉnh sửa từ frontend và lưu vào Database.
    """
    try:
        result = get_object_or_404(ExtractedResult, id=result_id)

        # Đọc dữ liệu JSON gửi lên từ request body
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        new_table_data = body_data.get('table_data')

        if new_table_data is None:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy dữ liệu bảng.'}, status=400)

        # Cập nhật vào record và lưu lại (dùng json.dumps để đồng nhất với file bridge.py)
        result.table_data = json.dumps(new_table_data)
        result.save()

        return JsonResponse({'status': 'success', 'message': 'Đã lưu thay đổi thành công!'})

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