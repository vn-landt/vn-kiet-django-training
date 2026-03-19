# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import io
import csv
import os
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.conf import settings
from .forms import UploadFileForm
from .models import UploadedFile, ExtractedResult
from .services.bridge import process_and_save_extraction
from django.urls import reverse
from .services.sheets_export import export_to_google_sheets
from .services.compress_image import compress_image
from .services.gemini_rest import upload_to_imgbb

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

            # Redirect to detail page
            return render(request, 'result_detail.html', {
                'result': ExtractedResult.objects.get(id=extraction_result['result_id']),
                'table': extraction_result['table']
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
        'table': table
    })


def download_csv(request, result_id):
    result = get_object_or_404(ExtractedResult, id=result_id)
    table = result.get_table()

    if not table:
        return HttpResponse("No data to download.", status=404)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % result.uploaded_file.filename.replace(' ', '_')

    writer = csv.writer(response)
    for row in table:
        writer.writerow(row)

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