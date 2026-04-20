# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
	"""
	Lưu trữ toàn bộ thông tin bổ sung và cài đặt của người dùng.
	Mỗi User sẽ có duy nhất 1 UserProfile.
	"""
	user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
	
	# --- Profile settings ---
	full_name = models.CharField(max_length=255, blank=True, null=True)
	avatar_url = models.TextField(blank=True, null=True)  # Lưu URL ảnh từ ImgBB hoặc placeholder
	website = models.URLField(max_length=255, blank=True, null=True)
	bio = models.TextField(blank=True, null=True)
	is_private = models.BooleanField(default=False)
	
	# --- Account settings (Khớp với form FE của bạn) ---
	# Lưu số phút: 0 (không xóa), 5, 15, 60 (1h), 1440 (1 ngày), 10080 (1 tuần)
	auto_delete_duration = models.IntegerField(default=0)
	
	keep_exif = models.BooleanField(default=False)
	newsletter_subscribed = models.BooleanField(default=False)
	show_unsafe_content = models.BooleanField(default=False)
	
	# --- Linked Accounts (Dùng để lưu trạng thái kết nối đơn giản) ---
	google_connected = models.BooleanField(default=False)
	facebook_connected = models.BooleanField(default=False)
	twitter_connected = models.BooleanField(default=False)
	
	def __unicode__(self):
		return u"Profile của %s" % self.user.username
	
	
	# --- Signals để tự động tạo Profile khi có User mới ---
	@receiver(post_save, sender=User)
	def create_user_profile(sender, instance, created, **kwargs):
		if created:
			UserProfile.objects.create(user=instance)
	
	
	@receiver(post_save, sender=User)
	def save_user_profile(sender, instance, **kwargs):
		instance.profile.save()
