# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ..models import UploadedFile, Notification


def global_user_data(request):
	"""
	Hàm gộp tất cả dữ liệu cần thiết cho Header/Sidebar.
	Chỉ tốn 1 lần truy vấn DB cho mỗi trang.
	"""
	if request.user.is_authenticated:
		# 1. Lấy số lượng ảnh (Quota)
		count = UploadedFile.objects.filter(user=request.user, is_deleted=False).count()
		
		# 2. Lấy cấu hình tự động xóa từ UserProfile
		# Lưu ý: Nhờ related_name='profile' trong models, ta có thể truy cập thẳng qua request.user
		try:
			duration = request.user.profile.auto_delete_duration
		except:
			duration = 0  # Phòng trường hợp hiếm là profile chưa được tạo
		
		return {
			'uploaded_count': count,
			'auto_delete_duration': duration,
			'user_profile': getattr(request.user, 'profile', None)
			# Truyền luôn profile ra để lấy avatar nếu cần
		}
	
	return {
		'uploaded_count': 0,
		'auto_delete_duration': 0,
		'user_profile': None
	}


def notification_context(request):
	"""
	Context processor giúp hiển thị số lượng và danh sách thông báo ở Header toàn cục.
	"""
	if request.user.is_authenticated():
		# Chỉ lấy các thông báo chưa xóa (Manager 'objects' đã tự lọc is_deleted=False)
		notifications_qs = Notification.objects.filter(user=request.user)
		
		# Đếm số lượng chưa đọc cho Badge đỏ
		unread_count = notifications_qs.filter(is_read=False).count()
		
		
		return {
			'GLOBAL_NOTIFICATIONS_COUNT': unread_count,
			'GLOBAL_NOTIFICATIONS_LIST': notifications_qs,
		}
	
	# Trả về mặc định nếu user chưa đăng nhập
	return {
		'GLOBAL_NOTIFICATIONS_COUNT': 0,
		'GLOBAL_NOTIFICATIONS_LIST': [],
	}
