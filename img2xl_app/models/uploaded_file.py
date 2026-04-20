# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UploadedFile(models.Model):
	"""
	Đóng vai trò là 'Media Library'.
	Lưu trữ các ảnh đã upload, giới hạn 50 tấm/user.
	"""
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files',
							 null=True)
	filename = models.CharField(max_length=255)
	mime_type = models.CharField(max_length=100, blank=True, null=True)
	image_url = models.TextField()
	file_size = models.PositiveIntegerField(default=0)
	uploaded_at = models.DateTimeField(default=timezone.now)
	
	# Dùng để đánh dấu khi ảnh bị 'dọn dẹp' để nhường chỗ cho ảnh mới (tấm thứ 51)
	is_deleted = models.BooleanField(default=False)
	
	# TRƯỜNG MỚI: Lưu thời điểm sẽ bị xóa.
	# Nếu là Null/None nghĩa là "Don't autodelete"
	delete_at = models.DateTimeField(blank=True, null=True)
	
	def __unicode__(self):
		return u"%s (Hết hạn: %s)" % (self.filename, self.delete_at)
