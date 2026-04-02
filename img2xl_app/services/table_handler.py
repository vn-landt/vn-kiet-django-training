# table_handler.py
# -*- coding: utf-8 -*-
import json
import zlib
import base64
import traceback
from google.appengine.api.datastore_types import Blob
from django.utils import timezone


class TableFileHandler(object):
    def __init__(self, result_instance):
        self.result = result_instance

    def save_data(self, table_data, is_final=False):
        """
        is_final = False: Lưu vào bản Nháp (Auto-save)
        is_final = True: Lưu vào bản Chính thức (Nút Save Changes)
        """
        try:
            json_str = json.dumps(table_data, ensure_ascii=False)
            if isinstance(json_str, unicode): json_str = json_str.encode('utf-8')
            compressed = zlib.compress(json_str, 9)
            safe_data = "B64:" + base64.b64encode(compressed)
            blob_data = Blob(safe_data)

            if is_final:
                # Khi nhấn Save Changes: Cập nhật cả 2 để đồng bộ
                self.result.table_data_compressed = blob_data
                self.result.table_data_draft = blob_data
                self.result.is_draft = False

                self.result.processed_at = timezone.now()
            else:
                # Khi Auto-save: Chỉ cập nhật bản Nháp
                self.result.table_data_draft = blob_data

            self.result.save()
            return True
        except:
            return False

    def load_data(self, for_export=False):
        """
        for_export = True: Chỉ lấy dữ liệu Chính thức (Final)
        for_export = False: Ưu tiên lấy bản Nháp để hiển thị trên Web
        """
        # Xác định trường dữ liệu cần lấy
        if for_export:
            raw_blob = self.result.table_data_compressed
        else:
            # Ưu tiên nháp, nếu nháp trống thì lấy final
            raw_blob = self.result.table_data_draft or self.result.table_data_compressed

        if not raw_blob: return []

        try:
            raw_data = str(raw_blob)
            if raw_data.startswith("B64:"):
                binary_data = base64.b64decode(raw_data[4:])
            else:
                binary_data = raw_data
            return json.loads(zlib.decompress(binary_data).decode('utf-8'))
        except:
            return []

    def delete_file(self):
        """
        Vì dữ liệu lưu chung với Model, khi Model bị xóa (result.delete()),
        trường này cũng sẽ bị xóa theo nên ta không cần làm gì ở đây.
        """
        pass