# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import json
from cStringIO import StringIO
from ..models import UploadedFile, ExtractedResult
from django.utils import timezone
from .gemini_rest import extract_with_gemini


def process_and_save_extraction(uploaded_file_instance):
    """
    Bridge: Process file, call Gemini, parse, and save to model.

    Args:
        uploaded_file_instance (UploadedFile): Model instance already saved

    Returns:
        dict: Result with status, table, etc.
    """
    result_obj = ExtractedResult.objects.create(
        uploaded_file=uploaded_file_instance,
        status='processing'
    )

    try:
        # Call Gemini
        result_text, error = extract_with_gemini(
            uploaded_file_instance.file.path,
            mime_type=uploaded_file_instance.mime_type
        )

        if error:
            result_obj.status = 'failed'
            result_obj.error_message = error
            result_obj.save()
            return {
                'status': 'error',
                'error': error
            }

        # Clean and parse CSV
        cleaned_text = result_text.strip()
        if '```csv' in cleaned_text:
            cleaned_text = cleaned_text.split('```csv')[1].split('```')[0].strip()
        elif '```' in cleaned_text:
            cleaned_text = cleaned_text.split('```')[1].strip()

        table_data = []
        try:
            csv_reader = csv.reader(StringIO(cleaned_text))
            table_data = [row for row in csv_reader]
        except Exception as parse_error:
            result_obj.status = 'failed'
            result_obj.error_message = 'CSV parse failed: ' + str(parse_error)
            result_obj.save()
            return {
                'status': 'error',
                'error': str(parse_error)
            }

        # Save to model
        result_obj.raw_response = result_text
        result_obj.table_data = json.dumps(table_data)
        result_obj.status = 'success'
        result_obj.processed_at = timezone.now()
        result_obj.save()

        return {
            'status': 'success',
            'table': table_data,
            'raw_csv': cleaned_text,
            'result_id': result_obj.id
        }

    except Exception as e:
        result_obj.status = 'failed'
        result_obj.error_message = str(e)
        result_obj.save()
        return {
            'status': 'error',
            'error': str(e)
        }