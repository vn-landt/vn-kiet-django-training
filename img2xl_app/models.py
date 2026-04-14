# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from djangae.fields import JSONField  # Import từ djangae
try:
    from djangae.db.models.fields import BlobField
except ImportError:
    # Nếu không tìm thấy, có thể dùng BinaryField mặc định của Django
    from django.db.models import BinaryField as BlobField
from django.utils import timezone
import json
from django.contrib.auth.models import User  # Sử dụng User mặc định của Django
from djangae.fields import JSONField

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files', null=True)
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    image_url = models.TextField()  # Lưu binary trực tiếp vào Datastore
    file_size = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(default=timezone.now)
    is_deleted = models.BooleanField(default=False) # Dùng cho auto-cleanup #35

    def __unicode__(self):
        return u"%s (%s KB)" % (self.filename, self.file_size // 1024)


class ExtractedResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='extraction_results', null=True)
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='extraction_results')

    status = models.CharField(max_length=20, default='pending')
    is_draft = models.BooleanField(default=True)  # Trạng thái Draft/Final #38
    raw_response = models.TextField(blank=True, null=True)
    table_data_compressed = BlobField(blank=True, null=True)

    # TRƯỜNG MỚI: Lưu bản nháp (Auto-save)
    table_data_draft = BlobField(blank=True, null=True)

    error_message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)  # Lưu mốc thời gian auto-save #38

    def __unicode__(self):
        filename = self.uploaded_file.filename if self.uploaded_file else "Unknown"
        return u"%s - %s" % (filename, self.status)

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
    upload_count = models.IntegerField(default=0) # Số ảnh đã up trong ngày #35

    class Meta:
        unique_together = ('user', 'usage_date')