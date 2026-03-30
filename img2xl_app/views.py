# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import traceback  # Thêm thư viện này ở đầu file
import io
import csv
import os
import json
from datetime import timedelta

from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.conf import settings
from .forms import UploadFileForm, RegisterForm
from .models import UploadedFile, ExtractedResult, UsageLog
from .services.bridge import process_and_save_extraction
from django.urls import reverse
from .services.sheets_export import export_to_google_sheets
from .services.compress_image import compress_image
from .services.gemini_rest import upload_to_imgbb, generate_text_with_gemini, extract_image_with_gemini
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from .services.table_handler import TableFileHandler
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages

def _perform_extraction_logic(uploaded_file):
    """
    Hàm trợ giúp tái sử dụng: Nhận file -> Trả về (table_data, image_url, error)
    Logic này được tách ra từ bridge.py và home để dùng chung.
    """
    try:
        file_bytes = uploaded_file.read()

        # 1. Nén ảnh (Sử dụng hàm từ services)
        compressed_bytes = compress_image(io.BytesIO(file_bytes))
        if hasattr(compressed_bytes, "getvalue"):
            compressed_bytes = compressed_bytes.getvalue()

        # 2. Upload lên ImgBB
        image_url, error = upload_to_imgbb(compressed_bytes)
        if error:
            return None, None, u"Upload ImgBB failed: " + error

        # 3. Gọi Gemini trích xuất (Sử dụng hàm từ services)
        result_text, error = extract_image_with_gemini(image_url, uploaded_file.content_type)
        if error:
            return None, image_url, u"Gemini AI error: " + error

        # 4. Làm sạch và Parse CSV (Logic từ bridge.py)
        cleaned_text = result_text.strip()
        if '```csv' in cleaned_text:
            cleaned_text = cleaned_text.split('```csv')[1].split('```')[0].strip()
        elif '```' in cleaned_text:
            cleaned_text = cleaned_text.split('```')[1].strip()

        if cleaned_text == 'NO_TABLE_FOUND':
            return None, image_url, u"Không tìm thấy bảng dữ liệu trong ảnh."

        # Parse CSV thành List
        csv_content = cleaned_text.encode('utf-8') if isinstance(cleaned_text, unicode) else cleaned_text
        csv_reader = csv.reader(io.BytesIO(csv_content))
        table_data = [row for row in csv_reader]

        # Bộ lọc rác (Chỉ giữ dòng có > 1 cột)
        if table_data:
            max_cols = max(len(row) for row in table_data)
            if max_cols > 1:
                table_data = [row for row in table_data if len(row) > 1]

        return table_data, image_url, None

    except Exception as e:
        return None, None, str(e)

def home(request):
    user = request.user
    recent_results = []
    if user.is_authenticated():
        recent_results = ExtractedResult.objects.filter(
            user=user
        ).order_by('-created_at')[:10]

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Kiểm tra Quota cho User đã đăng nhập [#35]
            if user.is_authenticated():
                today = timezone.now().date()
                usage, created = UsageLog.objects.get_or_create(user=user, usage_date=today)

                if usage.upload_count >= 10:
                    messages.error(request, "Bạn đã hết lượt upload trong ngày (Tối đa 10 ảnh).")
                    return render(request, 'home.html', {'recent_results': recent_results})
            uploaded_file = request.FILES['file']

            # Kiểm tra định dạng/dung lượng...

            # --- TÁI SỬ DỤNG HÀM LOGIC ---
            table_data, image_url, error = _perform_extraction_logic(uploaded_file)

            if error:
                return HttpResponse(u"Lỗi: " + error)

            # --- LƯU VÀO DATABASE (Chỉ làm ở Home) ---
            uf = UploadedFile.objects.create(
                user=user if user.is_authenticated() else None,
                filename=uploaded_file.name,
                mime_type=uploaded_file.content_type,
                image_url=image_url,
                file_size=uploaded_file.size
            )

            # Tạo bản ghi kết quả và lưu table_data qua Handler
            res_obj = ExtractedResult.objects.create(
                user=user if user.is_authenticated() else None,
                uploaded_file=uf,
                status='success',
                raw_response=u"Initial Extraction",
                processed_at=timezone.now()
            )
            handler = TableFileHandler(res_obj)  #
            handler.save_data(table_data)

            if user.is_authenticated():
                # Cập nhật số lượng dùng trong ngày
                usage.upload_count += 1  # hoặc +1 tùy logic của bạn
                usage.save()

                # [#35] Giới hạn 10 lịch sử (Xóa file thứ 11 trở đi)
                old_files = UploadedFile.objects.filter(user=user).order_by('-uploaded_at')[10:]
                for old_f in old_files:
                    old_f.delete()  # Datastore sẽ xóa các bản ghi liên quan nếu có CASCADE
            return render(request, 'result_detail.html', {
                'result': res_obj,
                'table': table_data,
                'table_json': json.dumps(table_data),
                'recent_results': recent_results
            })
    else:
        form = UploadFileForm()

    return render(request, 'home.html', {'form': form, 'recent_results': recent_results})


def result_detail(request, result_id):
    result = get_object_or_404(ExtractedResult, id=result_id)
    table = result.get_table()

    recent_results = ExtractedResult.objects.order_by('-created_at')
    return render(request, 'result_detail.html', {
        'result': result,
        'table': table,
        'table_json': json.dumps(table),
        'recent_results': recent_results
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
    print "DEBUG: Received POST for ID: %s" % result_id
    try:
        result = get_object_or_404(ExtractedResult, id=result_id)

        # Đảm bảo đọc body an toàn
        raw_body = request.body.decode('utf-8')
        body_data = json.loads(raw_body)
        new_table_data = body_data.get('table_data')

        handler = TableFileHandler(result)
        if handler.save_data(new_table_data):
            return JsonResponse({'status': 'success', 'message': 'OK'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Save failed'}, status=500)

    except Exception as e:
        print "--- TRACEBACK VIEW ERROR ---"
        traceback.print_exc()
        return HttpResponse(
            json.dumps({'status': 'error', 'message': str(e)}),
            content_type='application/json',
            status=500
        )

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

@require_POST
def extract_only_api(request):
    """
    API mới: Chỉ trích xuất dữ liệu trả về JSON, không chuyển trang, không lưu DB phức tạp.
    Dùng cho nút "Generate 1 pic into".
    """
    if 'file' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': u'Chưa chọn file.'})

    # TÁI SỬ DỤNG CÙNG MỘT HÀM LOGIC
    table_data, image_url, error = _perform_extraction_logic(request.FILES['file'])

    if error:
        return JsonResponse({'status': 'error', 'message': error})

    return JsonResponse({
        'status': 'success',
        'table': table_data
    })

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save() # Mật khẩu tự động được băm tại đây
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def cleanup_old_data(request):
    # Chỉ cho phép App Engine Cron gọi vào URL này
    if request.META.get('HTTP_X_APPENGINE_CRON') != 'true':
        return HttpResponseForbidden()

    seven_days_ago = timezone.now() - timedelta(days=7)

    # Tìm các file không có thay đổi trong 7 ngày qua
    old_results = ExtractedResult.objects.filter(updated_at__lt=seven_days_ago)

    count = 0
    for res in old_results:
        res.uploaded_file.delete()  # Xóa file gốc kéo theo kết quả trích xuất
        count += 1

    return HttpResponse("Đã dọn dẹp %d bản ghi cũ." % count)