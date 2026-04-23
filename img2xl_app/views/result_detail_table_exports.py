# -*- coding: utf-8 -*-
import csv
import os
import re
import io

from PIL.Image import Image
from PIL.ImageDraw import ImageDraw
from PIL.ImageFont import ImageFont
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from typing import io

from img2xl_app.models import ExtractedResult
from img2xl_app.services.sheets_export import export_to_google_sheets



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
    
    return render(request, 'img2xl_app/includes/export_ui.html', {
        'result': result,
        'preview_data': preview_data,
        'total_rows': len(draft_table_data),
        'total_cols': max(len(r) for r in draft_table_data) if draft_table_data else 0
    })


def _export_excel(result, table_data, start_coords=None, end_coords=None):
    # 1. Xử lý tên file: bienlai1.png -> bienlai1
    original_name = result.title
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


