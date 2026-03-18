# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from .forms import UploadFileForm
from .models import UploadedFile
from .services.bridge import process_and_save_extraction

def home(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']

            allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
            if uploaded_file.content_type not in allowed_types:
                return HttpResponse("Error: Only JPG, PNG, PDF allowed.")

            if uploaded_file.size > 10 * 1024 * 1024:
                return HttpResponse("Error: File too large (max 10MB).")

            # Create UploadedFile instance
            uf = UploadedFile.objects.create(
                filename=uploaded_file.name,
                mime_type=uploaded_file.content_type,
                file=uploaded_file,
                file_size=uploaded_file.size
            )

            # Process and save
            extraction_result = process_and_save_extraction(uf)

            if extraction_result['status'] == 'error':
                return HttpResponse("Processing failed: " + extraction_result['error'])

            # Display result
            table = extraction_result['table']
            table_html = "<table border='1'>"
            for row in table:
                table_html += "<tr>"
                for cell in row:
                    table_html += "<td>" + cell.encode('utf-8', 'replace') + "</td>"
                table_html += "</tr>"
            table_html += "</table>"

            return HttpResponse(
                "<h2>Success - Data Saved</h2>"
                "<p>Parsed Table:</p>" + table_html +
                "<p>Raw CSV:</p><pre>" + extraction_result['raw_csv'].encode('utf-8', 'replace') + "</pre>"
                                                                                                   "<p><a href='/'>Upload another</a></p>"
            )

        else:
            return HttpResponse("Invalid form.")
    else:
        form = UploadFileForm()

    return render(request, 'upload.html', {'form': form})