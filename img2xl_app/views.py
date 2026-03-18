# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import os
import json
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from .forms import UploadFileForm
from .models import UploadedFile, ExtractedResult
from .services.bridge import process_and_save_extraction
from django.urls import reverse


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

            uf = UploadedFile.objects.create(
                filename=uploaded_file.name,
                mime_type=uploaded_file.content_type,
                file=uploaded_file,
                file_size=uploaded_file.size
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