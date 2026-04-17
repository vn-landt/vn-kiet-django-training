# -*- coding: utf-8 -*-
from djangae import models
from django.contrib.auth.models import User
from django.utils import timezone

from img2xl_app.models import UploadedFile

try:
	from djangae.db.models.fields import BlobField
except ImportError:
	from django.db.models import BinaryField as BlobField
from djangae.fields import ListField, JSONField
from ..services import TableFileHandler


class ExtractedResult(models.Model):
	"""
	Đóng vai trò là 'Data Worksheet'.
	Một bảng dữ liệu có thể được tạo từ 0, 1 hoặc nhiều ảnh.
	"""
	objects = None
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='extraction_results',
							 null=True)


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
	
	# Bổ trợ xoá mềm
	is_deleted = models.BooleanField(default=False)
	delete_at = models.DateTimeField(blank=True, null=True)
	
	
	def __unicode__(self):
		return u"%s - %s" % (self.title, self.status)
	
	
	def get_related_images(self):
		if not self.source_file_ids or self.is_deleted:  # Nếu bảng tính đã bị xóa mềm, có thể không cần lấy ảnh
			return []
		return UploadedFile.objects.filter(id__in=self.source_file_ids, is_deleted=False)
	
	
	def get_table(self, for_export=False):
		"""Sử dụng OOP Handler để lấy dữ liệu"""
		if not self.id:
			return []
		
		handler = TableFileHandler(self)  # Chuyền cả object vào thay vì self.id
		return handler.load_data(for_export=for_export)
