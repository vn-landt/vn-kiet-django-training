# -*- coding: utf-8 -*-
from __future__ import print_function
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import os


def cleanup_orphaned_files():
    SERVICE_ACCOUNT_FILE = 'service-account.json'
    scope = ['https://www.googleapis.com/auth/drive']

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
        drive_service = build('drive', 'v3', credentials=creds)

        print("Searching for files owned by Service Account...")

        # CHỈ TÌM những file mà Service Account là CHỦ SỞ HỮU
        query = "'me' in owners"

        results = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, size)",
            pageSize=100
        ).execute()

        items = results.get('files', [])

        if not items:
            print("No owned files found.")
        else:
            print("Found {0} files owned by this account.".format(len(items)))
            for item in items:
                try:
                    # Xóa vĩnh viễn
                    print(u"Deleting owned file: {0} (Size: {1})".format(item['name'], item.get('size', '0')))
                    drive_service.files().delete(fileId=item['id']).execute()
                except Exception as e:
                    print("Could not delete {0}: {1}".format(item['id'], str(e)))

        # QUAN TRỌNG NHẤT: Dọn sạch thùng rác
        print("Emptying trash to free up quota...")
        drive_service.files().emptyTrash().execute()
        print("Success! Quota should be reset now.")

    except Exception as e:
        print("An error occurred: {0}".format(str(e)))


if __name__ == "__main__":
    cleanup_orphaned_files()