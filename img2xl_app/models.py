# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone


class UploadedFile(models.Model):
    filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    file = models.FileField(upload_to='uploads/')
    file_size = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return u"%s (%s KB)" % (self.filename, self.file_size // 1024)


class ExtractedResult(models.Model):
    uploaded_file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE, related_name='extraction_results')

    status = models.CharField(max_length=20, default='pending')
    raw_response = models.TextField(blank=True, null=True)
    parsed_table = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    processed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return u"%s - %s" % (self.uploaded_file.filename, self.status)