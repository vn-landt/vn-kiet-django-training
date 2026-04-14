# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import traceback  # Thêm thư viện này ở đầu file
import io
import logging
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
from django.contrib.auth import update_session_auth_hash

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
            logging.error(u"AI Processing Error: %s", error)
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
        # Thêm filter user=request.user để đảm bảo tính bảo mật
        result = get_object_or_404(ExtractedResult, id=result_id, user=request.user)

        # 1. Khởi tạo Handler để dọn dẹp file vật lý (file .xlsx hoặc .csv lưu trên storage)
        # Theo models.py của bạn, TableFileHandler nhận vào nguyên object 'result'
        try:
            handler = TableFileHandler(result)
            handler.delete_file()
        except Exception as e:
            # Nếu không tìm thấy file vật lý để xóa thì vẫn tiếp tục xóa DB
            pass

        # 2. XÓA DÒNG NÀY: result.uploaded_file.delete()
        # Vì ExtractedResult không còn thuộc tính uploaded_file nữa.

        # 3. Xóa bản ghi bảng tính trong Database
        # Các ảnh liên quan (UploadedFile) sẽ KHÔNG bị ảnh hưởng vì chúng là các record độc lập
        result.delete()

    return redirect('home')


def is_storage_full(user):
    """
    Hàm helper kiểm tra xem user đã đạt giới hạn 50 ảnh chưa.
    Trả về True nếu đã đầy, False nếu còn chỗ.
    """
    if not user.is_authenticated():
        return False  # Hoặc xử lý riêng cho khách (Guest)

    # Đếm số file đang hoạt động (chưa bị xóa) của user
    current_count = UploadedFile.objects.filter(user=user, is_deleted=False).count()
    return current_count >= 50

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


# views.py

@require_POST
def extract_only_api(request):
    user = request.user
    if not user.is_authenticated():
        return JsonResponse({'status': 'error', 'message': u'Vui lòng đăng nhập.'}, status=401)

    # 1. KIỂM TRA HẠN MỨC 50 ẢNH (Luôn kiểm tra vì bước nào cũng lưu vết ảnh)
    if is_storage_full(user):
        return JsonResponse({
            'status': 'limit_exceeded',
            'message': u'Kho lưu trữ ảnh đã đầy (50/50). Hãy xóa bớt ảnh cũ.',
            'redirect_url': reverse('documents_view')
        }, status=403)

    # 2. ĐỌC THAM SỐ TỪ FRONTEND
    # save_db=true: Tạo bảng mới (Home) | save_db=false: Cập nhật bảng hiện tại (Detail)
    is_create_new = request.POST.get('save_db') == 'true'
    current_result_id = request.POST.get('result_id')  # ID bảng đang mở (nếu có)
    languages = request.POST.get('languages', 'all')
    mime_type = request.POST.get('mime_type', 'image/jpeg')

    try:
        delete_duration_min = int(request.POST.get('deleteDuration', 0))
    except (ValueError, TypeError):
        # Nếu lỗi (không phải số), lấy mặc định từ profile
        delete_duration_min = user.profile.auto_delete_duration

    # TÍNH TOÁN THỜI ĐIỂM XÓA
    expiry_date = None
    if delete_duration_min > 0:
        # Thời điểm xóa = Hiện tại + X phút
        expiry_date = timezone.now() + timedelta(minutes=delete_duration_min)


    if 'file' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': u'Chưa có file.'})

    uploaded_file = request.FILES['file']

    imgname = request.POST.get('original_filename', uploaded_file.name)

    # 3. THỰC HIỆN OCR
    table_data, image_url, error = _perform_extraction_logic(uploaded_file, languages)
    if error:
        return JsonResponse({'status': 'error', 'message': error})

    # 4. LUÔN LƯU VẾT ẢNH (UPLOADEDFILE) - Bất kể tạo mới hay cập nhật
    uf = UploadedFile.objects.create(
        user=user,
        filename=imgname,
        mime_type=mime_type,
        image_url=image_url,
        file_size=uploaded_file.size,
        delete_at=expiry_date
    )

    # Cập nhật UsageLog
    usage, _ = UsageLog.objects.get_or_create(user=user, usage_date=timezone.now().date())
    usage.upload_count += 1
    usage.save()

    # 5. XỬ LÝ EXTRACTEDRESULT (BẢNG DỮ LIỆU)
    res_obj = None

    if is_create_new:
        # FLOW 1: TỪ TRANG CHỦ -> TẠO BẢNG MỚI
        res_obj = ExtractedResult.objects.create(
            user=user,
            title=u"Bảng tạo từ " + uf.filename,
            source_file_ids=[uf.id],
            status='success',
            processed_at=timezone.now()  # Đánh dấu đã có bản Final đầu tiên
        )
        # Lưu vào cả Draft và Final
        handler = TableFileHandler(res_obj)
        handler.save_data(table_data, is_final=True)

    elif current_result_id:
        # FLOW 2: TRONG BẢNG CHI TIẾT -> CHỈ CẬP NHẬT DRAFT
        res_obj = get_object_or_404(ExtractedResult, id=current_result_id, user=user)

        # Thêm ID ảnh mới vào danh sách lưu vết của bảng
        if uf.id not in res_obj.source_file_ids:
            res_obj.source_file_ids.append(uf.id)
            res_obj.save()

        # CHỈ cập nhật bản Nháp (Draft), không đè lên bản Chính (Final)
        # Người dùng có thể xóa data này đi, nhưng ID ảnh trong source_file_ids vẫn còn
        handler = TableFileHandler(res_obj)
        handler.save_data(table_data, is_final=False)

    return JsonResponse({
        'status': 'success',
        'result_id': res_obj.id if res_obj else None,
        'table': table_data  # Trả về để JS hiển thị lên bảng
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


def auto_cleanup_task(request):
    now = timezone.now()
    expired_files = UploadedFile.objects.filter(
        is_deleted=False,
        delete_at__isnull=False,
        delete_at__lte=now
    )

    count = 0
    for f in expired_files:
        # 1. Gọi hàm xóa ảnh trên ImgBB (nếu bạn có lưu delete_url)
        # success = delete_image_from_imgbb(f.delete_url)

        # 2. Đánh dấu đã xóa trong DB
        f.is_deleted = True
        f.save()
        count += 1

    return HttpResponse(u"Đã dọn dẹp %d ảnh hết hạn." % count)
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
def settings_view(request):
    # Trả về trang settings, dữ liệu user đã có sẵn trong request.user
    return render(request, 'settings.html')

#documents.html
@login_required
def documents_view(request):
    sort = request.GET.get('sort', 'recent')
    user = request.user

    # 1. Lấy danh sách bảng tính (dùng cho Sidebar 20%)
    results_query = ExtractedResult.objects.filter(user=user)

    # 2. Lấy TOÀN BỘ ảnh của user (dùng cho Gallery 80%)
    # Điều này đảm bảo ảnh vẫn hiện dù bảng tính bị xóa
    all_images_query = UploadedFile.objects.filter(user=user, is_deleted=False)

    # Logic sắp xếp cho bảng tính
    if sort == 'oldest':
        results = results_query.order_by('created_at')
        all_images = all_images_query.order_by('uploaded_at')
    else:
        results = results_query.order_by('-updated_at')
        all_images = all_images_query.order_by('-uploaded_at')

    return render(request, 'documents.html', {
        'results': results,  # Dùng cho sidebar
        'all_images': all_images,  # Dùng cho gallery ảnh
        'extractedResult': all_images.count(),  # Đếm ảnh thay vì đếm bảng
        'current_sort': sort
    })

@login_required
@require_POST
def create_blank_document(request):
    """Tạo bảng trống - KHÔNG cần tạo UploadedFile giả nữa"""
    name = request.POST.get('name', 'Untitled Spreadsheet')
    user = request.user

    # Tạo thẳng ExtractedResult với source_file_ids rỗng
    res_obj = ExtractedResult.objects.create(
        user=user,
        title=name,
        source_file_ids=[], # Bảng trống
        status='success',
        is_draft=True
    )

    empty_data = [["" for _ in range(5)] for _ in range(5)]
    handler = TableFileHandler(res_obj)
    handler.save_data(empty_data)

    return JsonResponse({'status': 'success', 'redirect_url': reverse('result_detail', args=[res_obj.id])})


@login_required
@require_POST
def update_title_api(request, result_id):
    """API: Đổi tên bảng tính"""
    result = get_object_or_404(ExtractedResult, id=result_id, user=request.user)
    new_title = request.POST.get('title')

    if new_title:
        result.title = new_title
        result.save()
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error', 'message': 'Thiếu tiêu đề'}, status=400)


@login_required
@require_POST
def delete_result_api(request, result_id):
    """API: Xóa bảng tính nhưng GIỮ LẠI hình ảnh"""
    result = get_object_or_404(ExtractedResult, id=result_id, user=request.user)

    # Dọn dẹp file vật lý trước
    try:
        # Dựa theo get_table trong model, Handler nhận object (result) chứ không phải result.id
        handler = TableFileHandler(result)
        handler.delete_file()
    except Exception as e:
        # Nếu không có file hoặc có lỗi vật lý, vẫn tiếp tục xóa trong database
        pass

    # Xóa record trong Database
    # Vì source_file_ids chỉ là ListField chứa ID (số nguyên) chứ không phải ForeignKey,
    # việc gọi result.delete() hoàn toàn KHÔNG tự động xóa ảnh trong UploadedFile.
    result.delete()

    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def delete_image_api(request, img_id):
    """API: Xóa 1 ảnh (UploadedFile)"""
    image = get_object_or_404(UploadedFile, id=img_id, user=request.user)

    # Xóa ảnh vật lý (nếu bạn có lưu file trên Storage) - Thêm code của bạn ở đây nếu cần
    # ...

    # Xóa trong database.
    # Như bạn yêu cầu, hành động này không ảnh hưởng đến ListField `source_file_ids`
    # của bảng ExtractedResult. ID cũ vẫn sẽ nằm đó để bạn chạy script cleanup sau.
    image.delete()

    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def bulk_delete_images_api(request):
    """API: Xóa nhiều ảnh cùng lúc"""
    try:
        # Lấy dữ liệu JSON từ request.body (do JS gửi bằng JSON.stringify)
        data = json.loads(request.body)
        ids = data.get('ids', [])

        if ids:
            # Xóa trên Storage (nếu có) trước khi xóa DB
            # images_to_delete = UploadedFile.objects.filter(id__in=ids, user=request.user)
            # for img in images_to_delete:
            #     # Thực hiện xóa file vật lý

            # Xóa hàng loạt trong Database (rất nhanh và tối ưu)
            UploadedFile.objects.filter(id__in=ids, user=request.user).delete()

        return JsonResponse({'status': 'success'})
    except ValueError:  # Bắt lỗi parse JSON
        return JsonResponse({'status': 'error', 'message': 'Dữ liệu không hợp lệ'}, status=400)


def update_image_info(request):
    if request.method == "POST":
        img_id = request.POST.get('id')
        new_name = request.POST.get('filename')
        duration = request.POST.get('duration')  # 'keep', '0', '5', '60', '1440'

        try:
            from .models import UploadedFile
            img_obj = UploadedFile.objects.get(id=img_id, user=request.user)

            # 1. Cập nhật tên
            img_obj.filename = new_name

            # 2. Cập nhật thời gian xóa nếu không chọn "Giữ nguyên"
            if duration != 'keep':
                duration_int = int(duration)
                if duration_int > 0:
                    img_obj.delete_at = timezone.now() + timedelta(minutes=duration_int)
                else:
                    img_obj.delete_at = None  # Chuyển sang vĩnh viễn

            img_obj.save()
            return JsonResponse({'status': 'success'})

        except Exception as e:
            logging.error(u"Error updating image info: %s", str(e))
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error'}, status=405)

def bulk_update_time(request):
    if request.method == "POST":
        ids = request.POST.getlist('ids[]')
        duration_min = int(request.POST.get('duration', 0))
        user = request.user

        # 1. Tính toán thời điểm xóa mới
        new_expiry = None
        if duration_min > 0:
            new_expiry = timezone.now() + timedelta(minutes=duration_min)

        try:
            from .models import UploadedFile
            # 2. Cập nhật hàng loạt tất cả các ID thuộc về User này
            # Lệnh .update() thực hiện 1 câu lệnh SQL duy nhất, cực kỳ tối ưu
            UploadedFile.objects.filter(
                id__in=ids,
                user=user
            ).update(delete_at=new_expiry)

            return JsonResponse({'status': 'success', 'count': len(ids)})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error'}, status=405)


#   settings/
@login_required
def update_account_settings(request):
    if request.method == 'POST':
        profile = request.user.profile

        # 1. Cập nhật thời gian tự động xóa (ép về kiểu int)
        auto_delete = request.POST.get('auto_delete_duration')
        if auto_delete is not None:
            profile.auto_delete_duration = int(auto_delete)

        # 2. Cập nhật Keep EXIF
        # Checkbox trong HTML: nếu tích sẽ gửi 'on', nếu không tích sẽ không gửi gì cả
        # profile.keep_exif = True if request.POST.get('keep_exif') == 'on' else False

        # 3. Lưu vào Database
        profile.save()

        # 4. Thông báo thành công và reload lại trang
        messages.success(request, u"Cài đặt tài khoản của bạn đã được cập nhật thành công!")
        return redirect('settings')  # Hoặc tên URL dẫn đến trang account của bạn

    return redirect('settings')


@login_required
def update_profile_settings(request):
    if request.method == 'POST':
        profile = request.user.profile

        # 1. Xử lý Upload Avatar (Nếu có file mới)
        avatar_file = request.FILES.get('avatar')
        if avatar_file:
            # Đọc file sang bytes
            image_bytes = avatar_file.read()
            # Gọi hàm của bạn
            new_avatar_url, error = upload_to_imgbb(image_bytes)

            if new_avatar_url:
                profile.avatar_url = new_avatar_url
            else:
                messages.error(request, u"Không thể upload ảnh: " + unicode(error))

        # 2. Cập nhật các trường thông tin khác
        profile.full_name = request.POST.get('full_name', '')
        profile.website = request.POST.get('website', '')
        profile.bio = request.POST.get('bio', '')
        profile.is_private = True  # Luôn đóng băng theo yêu cầu

        profile.save()
        messages.success(request, u"Hồ sơ đã được cập nhật thành công!")
        return redirect('settings')

    return redirect('settings')

@login_required
def change_password(request):
    if request.method == 'POST':
        # 1. Lấy dữ liệu từ Form
        old_pass = request.POST.get('old_password')
        new_pass = request.POST.get('new_password')
        confirm_pass = request.POST.get('confirm_password')
        user = request.user

        # 2. Kiểm tra mật khẩu cũ có đúng không
        if not user.check_password(old_pass):
            messages.error(request, u"Mật khẩu cũ không chính xác!")
            return redirect('settings') # Quay lại trang settings/password

        # 3. Kiểm tra 2 mật khẩu mới có khớp nhau không
        if new_pass != confirm_pass:
            messages.error(request, u"Hai mật khẩu mới không khớp nhau!")
            return redirect('settings')

        # 4. Kiểm tra độ dài mật khẩu (tùy chọn nhưng nên có)
        if len(new_pass) < 6:
            messages.error(request, u"Mật khẩu mới phải có ít nhất 6 ký tự!")
            return redirect('settings')

        # 5. Thực thi đổi mật khẩu
        user.set_password(new_pass) # Hàm này tự động băm (hash) mật khẩu
        user.save()

        # 6. CẬP NHẬT SESSION (Rất quan trọng!)
        # Sau khi đổi mật khẩu, Django sẽ làm mới session hash.
        # Nếu không có dòng này, người dùng sẽ bị văng ra trang Login ngay lập tức.
        update_session_auth_hash(request, user)

        messages.success(request, u"Chúc mừng! Mật khẩu đã được thay đổi thành công.")
        return redirect('settings')

    return redirect('settings')