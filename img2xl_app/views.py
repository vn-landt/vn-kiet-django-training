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
from django.template.loader import get_template
from xhtml2pdf import pisa  # Dùng cho PDF
import xlsxwriter           # Dùng cho Excel
import io
import json
import re
# Cần import thêm thư viện xử lý ảnh (hãy đảm bảo bạn đã cài 'Pillow' trong requirements.txt)
from PIL import Image, ImageDraw, ImageFont
from django.utils import timezone
from django.contrib.auth.decorators import login_required

def _perform_extraction_logic(uploaded_file, languages='all'):
    """
    Hàm trợ giúp tái sử dụng: Nhận file -> Trả về (table_data, image_url, error)
    Logic này được tách ra từ bridge.py và home để dùng chung.
    """
    try:
        # 1. Kiểm tra Kỹ thuật (Chặn sớm để tiết kiệm tài nguyên)
        MAX_SIZE = 5 * 1024 * 1024  # 5MB
        ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

        if uploaded_file.size > MAX_SIZE:
            return None, None, u"File quá lớn (Tối đa 5MB). Vui lòng chọn ảnh khác."

        if uploaded_file.content_type not in ALLOWED_TYPES:
            return None, None, u"Định dạng file không hỗ trợ (Chỉ nhận JPG, PNG, WebP)."

        file_bytes = uploaded_file.read()

        # 2. Nén ảnh
        compressed_bytes = compress_image(io.BytesIO(file_bytes))
        if hasattr(compressed_bytes, "getvalue"):
            compressed_bytes = compressed_bytes.getvalue()

        # 3. Upload lên ImgBB
        image_url, error = upload_to_imgbb(compressed_bytes)
        if error:
            return None, None, u"Lỗi kết nối máy chủ ảnh. Vui lòng thử lại."

        # 4. Gọi Gemini trích xuất & Kiểm tra nội dung (Mặt người/Hoá đơn)
        result_text, error = extract_image_with_gemini(image_url, uploaded_file.content_type, languages)

        if result_text == "INVALID_DOCUMENT":
            return None, image_url, u"Tài liệu không hợp lệ hoặc không đủ độ rõ nét. Vui lòng chọn ảnh hóa đơn, chứng từ khác."

        if error:
            return None, image_url, u"Hệ thống AI không thể xử lý ảnh này. Vui lòng thử lại."

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


# views.py

def home(request):
    """
    Chỉ làm nhiệm vụ hiển thị trang chủ và danh sách lịch sử.
    Mọi hoạt động trích xuất đã chuyển sang extract_only_api.
    """
    user = request.user
    recent_results = []

    if user.is_authenticated():
        # Lấy 10 kết quả gần nhất của user
        recent_results = ExtractedResult.objects.filter(
            user=user
        ).order_by('-created_at')[:10]

    # Không còn xử lý request.method == 'POST' ở đây nữa
    return render(request, 'home.html', {
        'form': UploadFileForm(),
        'recent_results': recent_results
    })

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

    recent_results = ExtractedResult.objects.order_by('-created_at')
    return render(request, 'result_detail.html', {
        'result': result,
        'table_json': table_json_str,
        'final_table_json': final_table_json_str,
        'recent_results': recent_results,
        'last_draft_time': last_draft_time,
        'last_final_time': last_final_time,
    })

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
    user = request.user
    if 'file' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': u'Chưa chọn file.'})

    # Đọc tham số 'save_db' từ FormData (mặc định là false)
    # Vì FormData gửi lên là string nên ta so sánh với 'true'
    should_save = request.POST.get('save_db') == 'true'

    # Đọc tham số 'languages' từ FormData (nếu không có thì mặc định là 'all')
    languages = request.POST.get('languages', 'all')

    # 1. Logic trích xuất AI dùng chung
    uploaded_file = request.FILES['file']

    table_data, image_url, error = _perform_extraction_logic(uploaded_file, languages)

    if error:
        return JsonResponse({'status': 'error', 'message': error})

    # 2. CHỈ LƯU NẾU CÓ YÊU CẦU (Dành cho trang Home)
    if should_save:
        now_str = timezone.now().strftime('%Y%m%d_%H%M%S')
        uf = UploadedFile.objects.create(
            user=user if user.is_authenticated() else None,
            filename="IMG_%s.jpg" % now_str,
            mime_type='image/jpeg',
            image_url=image_url,
            file_size=uploaded_file.size
        )

        res_obj = ExtractedResult.objects.create(
            user=user if user.is_authenticated() else None,
            uploaded_file=uf,
            status='success',
            processed_at=timezone.now()
        )

        handler = TableFileHandler(res_obj)
        handler.save_data(table_data)

        if user.is_authenticated():
            usage, _ = UsageLog.objects.get_or_create(user=user, usage_date=timezone.now().date())
            usage.upload_count += 1
            usage.save()

        return JsonResponse({
            'status': 'success',
            'result_id': res_obj.id, # Trả về ID để chuyển trang
            'table': table_data
        })

    # 3. NẾU KHÔNG LƯU (Dành cho trang Detail)
    # Chỉ trả về dữ liệu bảng thô
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


# views.py

def export(request, result_id):
    result = get_object_or_404(ExtractedResult, id=result_id)

    # XỬ LÝ KHI NGƯỜI DÙNG ẤN NÚT DOWNLOAD (METHOD POST)
    if request.method == 'POST':
        # LẤY BẢN CHỐT (Final) ĐỂ XUẤT FILE
        final_table_data = result.get_table(for_export=True)

        export_type = request.POST.get('export_type', 'xlsx')

        if export_type == 'png':
            bg_color = request.POST.get('bg_color', 'white')
            start_cell = request.POST.get('start_cell', 'A1')
            try:
                num_rows = int(request.POST.get('num_rows', 5))
                num_cols = int(request.POST.get('num_cols', 5))
            except ValueError:
                num_rows, num_cols = 5, 5

            # Truyền final_table_data vào
            return _export_png(result, final_table_data, bg_color, start_cell, num_rows, num_cols)

        else:
            # Truyền final_table_data vào
            return _export_excel(result, final_table_data)

    # XỬ LÝ KHI TRUY CẬP URL (METHOD GET - Xem Preview)
    # LẤY BẢN NHÁP (Draft) ĐỂ HIỂN THỊ XEM TRƯỚC
    draft_table_data = result.get_table(for_export=False)

    preview_data = [row[:10] for row in draft_table_data[:5]]

    return render(request, 'includes/export_ui.html', {
        'result': result,
        'preview_data': preview_data,
        'total_rows': len(draft_table_data),
        'total_cols': max(len(r) for r in draft_table_data) if draft_table_data else 0
    })

def _export_excel(result, table_data, start_coords=None, end_coords=None):
    # 1. Xử lý tên file: bienlai1.png -> bienlai1
    original_name = result.uploaded_file.filename
    base_name = os.path.splitext(original_name)[0].replace(' ', '_')

    # Dùng lại logic CSV của bạn nhưng với tên file đã sạch
    response = HttpResponse(content_type='text/csv')
    response.write('\xef\xbb\xbf')  # BOM cho tiếng Việt
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % base_name

    writer = csv.writer(response)
    for row in table_data:
        clean_row = []
        for cell in row:
            if cell is None:
                cell_text = u""
            elif not isinstance(cell, unicode):
                cell_text = unicode(str(cell), 'utf-8', errors='ignore')
            else:
                cell_text = cell
            clean_row.append(cell_text.strip().encode('utf-8'))
        if any(clean_row):
            writer.writerow(clean_row)
    return response


def _export_png(result, table_data, bg_color, start_cell, num_rows, num_cols):
    """Xuất PNG dựa trên ô bắt đầu và kích thước vùng chọn"""
    # 1. Xử lý tên file (bỏ đuôi cũ)
    base_name = os.path.splitext(result.uploaded_file.filename)[0].replace(' ', '_')

    # 2. Parse tọa độ ô bắt đầu (VD: A1 -> col:0, row:0)
    def parse_start(s):
        m = re.match(r"([A-Z]+)(\d+)", s.upper())
        if not m: return 0, 0
        col_str, row_str = m.groups()
        col = 0
        for char in col_str: col = col * 26 + (ord(char) - 64)
        return int(row_str) - 1, col - 1

    s_row, s_col = parse_start(start_cell)

    # 3. Giới hạn vùng chọn (Max 30x30)
    num_rows = min(int(num_rows), 30)
    num_cols = min(int(num_cols), 30)

    # 4. Cắt mảng dữ liệu (Slice)
    # Lấy từ hàng s_row đến s_row + num_rows
    sliced_data = []
    for r in range(s_row, s_row + num_rows):
        if r < len(table_data):
            # Lấy từ cột s_col đến s_col + num_cols
            row_data = table_data[r][s_col: s_col + num_cols]
            # Nếu dòng ngắn hơn số cột yêu cầu, bù thêm ô rỗng
            while len(row_data) < num_cols:
                row_data.append(u"")
            sliced_data.append(row_data)
        else:
            # Nếu hết dòng trong data, bù dòng rỗng
            sliced_data.append([u""] * num_cols)

    # 5. Cấu hình vẽ ảnh
    cell_w, cell_h = 140, 45  # Tăng nhẹ size ô
    img_w, img_h = num_cols * cell_w, num_rows * cell_h

    # Màu sắc palette hiện đại
    COLOR_BG = (255, 255, 255) if bg_color != 'black' else (28, 28, 28)
    COLOR_STRIPE = (245, 247, 249) if bg_color != 'black' else (38, 38, 38)
    COLOR_LINE = (220, 225, 230) if bg_color != 'black' else (60, 60, 60)
    COLOR_TEXT = (33, 37, 41) if bg_color != 'black' else (240, 240, 240)

    img = Image.new('RGB', (img_w, img_h), COLOR_BG)
    draw = ImageDraw.Draw(img)

    # Load font (Nhớ copy file .ttf vào thư mục code nhé)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    # Vẽ dữ liệu
    for r_idx, row in enumerate(sliced_data):
        for c_idx, cell_value in enumerate(row):
            x0, y0 = c_idx * cell_w, r_idx * cell_h
            rect = [x0, y0, x0 + cell_w, y0 + cell_h]

            # Vẽ nền xen kẽ (Zebra)
            fill_color = COLOR_STRIPE if r_idx % 2 == 0 else COLOR_BG
            draw.rectangle(rect, fill=fill_color, outline=COLOR_LINE)

            # Xử lý nội dung
            val = cell_value if isinstance(cell_value, unicode) else unicode(str(cell_value), 'utf-8', errors='ignore')
            if len(val) > 20: val = val[:17] + "..."

            # Căn giữa "thần thánh"
            try:
                tw, th = draw.textsize(val, font=font)
                draw.text((x0 + (cell_w - tw) / 2, y0 + (cell_h - th) / 2), val, fill=COLOR_TEXT, font=font)
            except:
                # Fallback nếu textsize lỗi trên bản PIL cũ
                draw.text((x0 + 10, y0 + 12), val, fill=COLOR_TEXT, font=font)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    response = HttpResponse(buf.read(), content_type='image/png')
    response['Content-Disposition'] = 'attachment; filename="%s.png"' % base_name
    return response

@login_required
def profile_view(request):
    # Tạm thời để trống như yêu cầu
    return render(request, 'profile.html')

@login_required
def settings_view(request):
    # Trả về trang settings, dữ liệu user đã có sẵn trong request.user
    return render(request, 'settings.html')