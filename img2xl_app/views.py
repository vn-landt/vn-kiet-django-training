# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from .forms import UploadFileForm
from .services.bridge import process_file_extraction

def home(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            # Validate file type and size
            allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
            if uploaded_file.content_type not in allowed_types:
                return HttpResponse("Error: Only JPG, PNG, PDF files are allowed.")

            if uploaded_file.size > 10 * 1024 * 1024:
                return HttpResponse("Error: File too large (maximum 10MB).")

            # Save file
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Use bridge to process
            extraction_result = process_file_extraction(
                file_path,
                mime_type=uploaded_file.content_type
            )

            if extraction_result['status'] == 'error':
                return HttpResponse("Extraction failed: " + extraction_result['error'])

            # For now, display parsed table as HTML table
            table_html = "<table border='1'>"
            for row in extraction_result['table']:
                table_html += "<tr>"
                for cell in row:
                    table_html += "<td>" + cell.encode('utf-8', 'replace') + "</td>"
                table_html += "</tr>"
            table_html += "</table>"

            return HttpResponse(
                "<h2>Extraction Successful</h2>"
                "<p>Parsed Table:</p>" + table_html +
                "<p><strong>Raw CSV:</strong></p><pre>" +
                extraction_result['raw_csv'].encode('utf-8', 'replace') +
                "</pre>"
                "<br><a href='/'>Upload another file</a>"
            )

        else:
            return HttpResponse("Invalid form submission.")

    else:
        form = UploadFileForm()

    return render(request, 'upload.html', {'form': form})