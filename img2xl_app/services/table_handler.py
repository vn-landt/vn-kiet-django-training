# table_handler.py
# -*- coding: utf-8 -*-
import json
import zlib
import base64
import traceback
from google.appengine.api.datastore_types import Blob


class TableFileHandler(object):
    def __init__(self, result_instance):
        self.result = result_instance

    def save_data(self, table_data):
        if not isinstance(table_data, list):
            return False
        try:
            # 1. Chuyển thành chuỗi UTF-8
            json_str = json.dumps(table_data, ensure_ascii=False)
            if isinstance(json_str, unicode):
                json_str = json_str.encode('utf-8')

            # 2. Nén dữ liệu
            compressed = zlib.compress(json_str, 9)

            # 3. Chuyển sang Base64 ĐỂ TRÁNH LỖI ASCII TRÊN PYTHON 2.7
            # Chúng ta dùng thêm một tiền tố 'B64:' để sau này dễ nhận biết
            safe_data = "B64:" + base64.b64encode(compressed)

            # 4. Ghi vào DB
            model_class = self.result.__class__
            instance = model_class.objects.get(pk=self.result.pk)
            instance.table_data_compressed = Blob(safe_data)
            instance.save()

            print "DEBUG: Save success with Base64 encoding."
            return True
        except Exception as e:
            print "DEBUG: Save Error: %s" % str(e)
            traceback.print_exc()
            return False

    def load_data(self):
        """Hàm load thông minh: Tương thích cả dữ liệu cũ và mới"""
        if not getattr(self.result, 'table_data_compressed', None):
            return []

        try:
            # Lấy dữ liệu thô (có thể là Blob hoặc str)
            raw_data = str(self.result.table_data_compressed)

            # KIỂM TRA ĐỊNH DẠNG
            if raw_data.startswith("B64:"):
                # Dữ liệu mới: Bỏ tiền tố 'B64:' rồi giải mã
                actual_b64 = raw_data[4:]
                binary_data = base64.b64decode(actual_b64)
            else:
                # Dữ liệu cũ (hoặc dữ liệu nén trực tiếp)
                binary_data = raw_data

            # Giải nén zlib
            decompressed = zlib.decompress(binary_data)

            # Decode JSON
            return json.loads(decompressed.decode('utf-8'))

        except Exception as e:
            # Nếu vẫn lỗi, in ra để debug chứ đừng để trống
            print "DEBUG: Load Error: %s" % str(e)
            # Thử phương án cuối: trả về chính nó nếu không nén (đề phòng)
            try:
                return json.loads(raw_data.decode('utf-8'))
            except:
                return []

    def delete_file(self):
        """
        Vì dữ liệu lưu chung với Model, khi Model bị xóa (result.delete()),
        trường này cũng sẽ bị xóa theo nên ta không cần làm gì ở đây.
        """
        pass