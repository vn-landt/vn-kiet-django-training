# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
import os

SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]


def export_to_google_sheets(table_data, filename):
    """
    Export table (list of lists) to a new Google Sheet.
    Returns: shareable link or error message.
    """
    credentials_path = os.path.join(settings.BASE_DIR, 'service-account.json')

    if not os.path.exists(credentials_path):
        return None, "Service account file not found: service-account.json"

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, SCOPE)
        client = gspread.authorize(creds)

        # Create new spreadsheet
        sheet_title = "Extracted Table - " + filename.replace('.', '_')
        spreadsheet = client.create(sheet_title)

        # Get first worksheet
        worksheet = spreadsheet.sheet1

        # Update with data (starting from A1)
        if table_data:
            worksheet.update('A1', table_data)

        # Get shareable link
        spreadsheet.share('', perm_type='anyone', role='reader')
        sheet_url = spreadsheet.url

        return sheet_url, None

    except Exception as e:
        return None, "Export failed: " + str(e)