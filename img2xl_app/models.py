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


class UploadedFile(models.Model):
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    file_blob = BlobField()  # Lưu binary trực tiếp vào Datastore
    file_size = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return u"%s (%s KB)" % (self.filename, self.file_size // 1024)


class ExtractedResult(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='extraction_results')

    status = models.CharField(max_length=20, default='pending')
    raw_response = models.TextField(blank=True, null=True)
    table_data = JSONField(default=list, blank=True, null=True)  # Djangae hỗ trợ JSONField
    error_message = models.TextField(blank=True, null=True)

    processed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return u"%s - %s" % (self.uploaded_file.filename, self.status)

    def get_table(self):
        if self.table_data:
            return self.table_data
        return []