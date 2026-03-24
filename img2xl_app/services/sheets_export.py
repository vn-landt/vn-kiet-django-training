# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import json
from google.appengine.api import urlfetch
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings

SCOPE = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def export_to_google_sheets(table_data, filename):
    credentials_path = os.path.join(settings.BASE_DIR, 'service-account.json')

    try:
        # 1. Lấy Access Token từ Service Account
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, SCOPE)
        access_token = creds.get_access_token().access_token

        auth_headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json'
        }

        # 2. Tạo Spreadsheet mới (Drive API v3)
        create_drive_url = "https://www.googleapis.com/drive/v3/files"
        drive_payload = {
            'name': "Extracted - " + filename.replace('.', '_'),
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }

        res_drive = urlfetch.fetch(
            url=create_drive_url,
            payload=json.dumps(drive_payload),
            method=urlfetch.POST,
            headers=auth_headers,
            validate_certificate=True
        )

        if res_drive.status_code != 200:
            return None, "Drive Create Failed: " + res_drive.content

        spreadsheet_id = json.loads(res_drive.content)['id']

        # 3. Ghi dữ liệu vào Sheet (Sheets API v4)
        # Sử dụng dải ô Sheet1!A1
        update_url = "https://sheets.googleapis.com/v1/spreadsheets/{}/values/Sheet1!A1?valueInputOption=USER_ENTERED".format(
            spreadsheet_id)
        sheets_payload = {
            'values': table_data
        }

        res_sheets = urlfetch.fetch(
            url=update_url,
            payload=json.dumps(sheets_payload),
            method=urlfetch.PUT,
            headers=auth_headers,
            validate_certificate=True
        )

        if res_sheets.status_code != 200:
            return None, "Sheets Update Failed: " + res_sheets.content

        # 4. Chia sẻ quyền "Anyone with link can write"
        perm_url = "https://www.googleapis.com/drive/v3/files/{}/permissions".format(spreadsheet_id)
        perm_payload = {
            'role': 'writer',
            'type': 'anyone'
        }

        urlfetch.fetch(
            url=perm_url,
            payload=json.dumps(perm_payload),
            method=urlfetch.POST,
            headers=auth_headers,
            validate_certificate=True
        )

        sheet_url = "https://docs.google.com/spreadsheets/d/{}".format(spreadsheet_id)
        return sheet_url, None

    except Exception as e:
        import logging
        logging.error("GAE Export Error: " + str(e))
        return None, "Export failed: " + str(e)