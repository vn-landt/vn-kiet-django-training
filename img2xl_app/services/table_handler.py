# -*- coding: utf-8 -*-
import json
import zlib


class TableFileHandler(object):
    """
    Class quản lý việc lưu trữ mảng 2 chiều.
    Sử dụng zlib để nén dữ liệu thành nhị phân (giảm 90% dung lượng)
    và lưu trực tiếp vào BlobField để lách giới hạn 1MB của GAE.
    """

    def __init__(self, result_instance):
        self.result = result_instance

    def save_data(self, table_data):
        """Nhận mảng 2 chiều, nén zlib và lưu vào instance"""
        if not isinstance(table_data, list):
            print("Lỗi: Dữ liệu không phải là List")
            return False

        try:
            # Chuyển thành chuỗi JSON, hỗ trợ tiếng Việt
            json_str = json.dumps(table_data, ensure_ascii=False)
            if isinstance(json_str, unicode):
                json_str = json_str.encode('utf-8')

            # Nén chuỗi (mức độ nén cao nhất: 9)
            compressed_data = zlib.compress(json_str, 9)

            # Gán vào trường dữ liệu và lưu
            self.result.table_data_compressed = compressed_data
            self.result.save()
            return True
        except Exception as e:
            print("Lỗi khi nén và lưu dữ liệu:", e)
            return False

    def load_data(self):
        """Đọc BlobField, giải nén và trả về mảng 2 chiều"""
        if not getattr(self.result, 'table_data_compressed', None):
            return []

        try:
            # Giải nén
            decompressed_str = zlib.decompress(self.result.table_data_compressed)
            # Parse lại thành List
            return json.loads(decompressed_str.decode('utf-8'))
        except Exception as e:
            print("Lỗi khi giải nén dữ liệu:", e)
            return []

    def delete_file(self):
        """
        Vì dữ liệu lưu chung với Model, khi Model bị xóa (result.delete()),
        trường này cũng sẽ bị xóa theo nên ta không cần làm gì ở đây.
        """
        pass