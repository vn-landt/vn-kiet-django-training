# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
from cStringIO import StringIO
from .gemini_rest import extract_with_gemini


def process_file_extraction(file_path, mime_type='image/jpeg', custom_prompt=None):
    """
    Bridge function: Extract table from file using Gemini and parse into structured data.

    Args:
        file_path (str): Path to saved file on disk
        mime_type (str): MIME type like 'image/jpeg' or 'application/pdf'
        custom_prompt (str or None): Optional custom prompt

    Returns:
        dict: {
            'status': 'success' or 'error',
            'table': list of lists (rows, first row is header if detected),
            'raw_csv': full CSV string from Gemini,
            'error': error message if failed
        }
    """
    result, error = extract_with_gemini(file_path, mime_type=mime_type, custom_prompt=custom_prompt)

    if error:
        return {
            'status': 'error',
            'table': [],
            'raw_csv': '',
            'error': error
        }

    # Clean Gemini response - often wrapped in ```csv ... ```
    cleaned_text = result.strip()
    if '```csv' in cleaned_text:
        cleaned_text = cleaned_text.split('```csv')[1].split('```')[0].strip()
    elif '```' in cleaned_text:
        cleaned_text = cleaned_text.split('```')[1].strip()

    # Parse CSV to list of lists
    table_data = []
    try:
        csv_reader = csv.reader(StringIO(cleaned_text))
        for row in csv_reader:
            table_data.append(row)
    except Exception as parse_error:
        return {
            'status': 'error',
            'table': [],
            'raw_csv': cleaned_text,
            'error': 'CSV parse failed: ' + str(parse_error)
        }

    return {
        'status': 'success',
        'table': table_data,
        'raw_csv': cleaned_text,
        'error': None
    }