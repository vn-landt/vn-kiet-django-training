# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User

import logging

# Khai báo logger để debug trên GAE
logger = logging.getLogger(__name__)


class NotificationManager(models.Manager):
	"""Manager cung cấp hàm tạo thông báo nhanh chóng"""
	
	def create_notification(self, user, title, message, level='info', linked_to=None):
		"""
		Hàm tạo thông báo tập trung.
		Cách dùng: Notification.objects.create_notification(user, u'Tiêu đề', u'Nội dung', ...)
		"""
		# Đảm bảo level nằm trong danh sách cho phép
		valid_levels = [choice[0] for choice in Notification.LEVEL_CHOICES]
		if level not in valid_levels:
			level = 'info'
		
		try:
			return self.create(
				user=user,
				title=title,
				message=message,
				level=level,
				linked_to=linked_to
			)
		except Exception as e:
			logger.error(u"Không thể tạo thông báo: " + unicode(e))
			return None


class Notification(models.Model):
	# Các loại thông báo chuẩn
	LEVEL_CHOICES = (
		('info', u'Thông tin'),
		('success', u'Thành công'),
		('warning', u'Cảnh báo'),
		('error', u'Lỗi'),
	)
	
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
	level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
	title = models.CharField(max_length=255)
	message = models.TextField()
	
	# Đường dẫn liên kết (Ví dụ: dẫn tới file excel hoặc trang kết quả)
	linked_to = models.CharField(max_length=500, null=True, blank=True)
	
	# Trạng thái và thời gian
	is_read = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	
	# Đăng ký Manager mặc định
	objects = NotificationManager()
	
	class Meta:
		ordering = ['-created_at']
		verbose_name = u"Thông báo"
		verbose_name_plural = u"Danh sách thông báo"
	
	def __unicode__(self):
		return u"[%s] %s: %s" % (self.level, self.user.username, self.title)
