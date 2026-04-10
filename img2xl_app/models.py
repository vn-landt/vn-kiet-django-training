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
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

# Khai báo logger để debug trên GAE
logger = logging.getLogger(__name__)

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

    # TRƯỜNG MỚI: Lưu thời điểm sẽ bị xóa.
    # Nếu là Null/None nghĩa là "Don't autodelete"
    delete_at = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return u"%s (Hết hạn: %s)" % (self.filename, self.delete_at)


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