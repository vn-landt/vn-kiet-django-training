# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from djangae.fields import ListField, JSONField  # Djangae support

try:
    from djangae.db.models.fields import BlobField
except ImportError:
    from django.db.models import BinaryField as BlobField


class UploadedFile(models.Model):
    """
    Đóng vai trò là 'Media Library'.
    Lưu trữ các ảnh đã upload, giới hạn 50 tấm/user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files', null=True)
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    image_url = models.TextField()
    file_size = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(default=timezone.now)

    # Dùng để đánh dấu khi ảnh bị 'dọn dẹp' để nhường chỗ cho ảnh mới (tấm thứ 51)
    is_deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s (%s KB)" % (self.filename, self.file_size // 1024)


class ExtractedResult(models.Model):
    """
    Đóng vai trò là 'Data Worksheet'.
    Một bảng dữ liệu có thể được tạo từ 0, 1 hoặc nhiều ảnh.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='extraction_results', null=True)

    # TRƯỜNG MỚI: Tên bảng để người dùng dễ quản lý khi xem lịch sử
    title = models.CharField(max_length=255, default="Bảng tính không tên")

    # THAY ĐỔI QUAN TRỌNG:
    # Lưu danh sách ID của các UploadedFile đã dùng để tạo ra bảng này.
    # ListField([1, 2, 3]) cực kỳ nhẹ và tối ưu trên Datastore.
    source_file_ids = ListField(models.IntegerField(), default=[], blank=True)

    status = models.CharField(max_length=20, default='pending')
    is_draft = models.BooleanField(default=True)

    raw_response = models.TextField(blank=True, null=True)
    table_data_compressed = BlobField(blank=True, null=True)
    table_data_draft = BlobField(blank=True, null=True)

    error_message = models.TextField(blank=True, null=True)
    # Thời gian ấn Save Changes
    processed_at = models.DateTimeField(blank=True, null=True)
    # Thời gian lưu lúc tạo
    created_at = models.DateTimeField(default=timezone.now)
    # Thời gian lưu bản draft
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u"%s - %s" % (self.title, self.status)

    def get_related_images(self):
        """
        Hàm tiện ích để lấy các object ảnh gốc từ Media Library.
        Nếu ảnh đã bị xóa (do giới hạn 50 tấm), nó sẽ không xuất hiện trong kết quả.
        """
        if not self.source_file_ids:
            return []
        return UploadedFile.objects.filter(id__in=self.source_file_ids, is_deleted=False)

    def get_table(self, for_export=False):
        """Sử dụng OOP Handler để lấy dữ liệu"""
        if not self.id:
            return []

        # Gọi file handler nằm trong thư mục services
        from .services.table_handler import TableFileHandler
        handler = TableFileHandler(self)  # Chuyền cả object vào thay vì self.id
        return handler.load_data(for_export=for_export)

class UsageLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_logs')
    usage_date = models.DateField(default=timezone.now)
    upload_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'usage_date')