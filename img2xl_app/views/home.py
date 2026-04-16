# -*- coding: utf-8 -*-
from datetime import timedelta
from time import timezone

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from img2xl_app.forms import UploadFileForm
from img2xl_app.models import ExtractedResult, Notification


def home(request):
    """
    Chỉ làm nhiệm vụ hiển thị trang chủ và danh sách lịch sử.
    Mọi hoạt động trích xuất đã chuyển sang extract_only_api.
    """
    user = request.user
    recent_results = []

    if user.is_authenticated():
        # Lấy 10 kết quả gần nhất của user
        recent_results = ExtractedResult.objects.filter(
            user=user,
            is_deleted=False
        ).order_by('-created_at')[:10]

    # Không còn xử lý request.method == 'POST' ở đây nữa
    return render(request, 'home.html', {
        'form': UploadFileForm(),
        'recent_results': recent_results
    })

# Xoá bảng tính ở trang home
@login_required
@require_POST  # Đảm bảo chỉ chấp nhận request POST để bảo mật
def delete_result(request, result_id):
    # 1. Tìm đối tượng bảng tính, đảm bảo đúng chủ sở hữu
    result = get_object_or_404(ExtractedResult, id=result_id, user=request.user)

    # 2. THỰC HIỆN SOFT DELETE
    # Chúng ta KHÔNG gọi TableFileHandler(result).delete_file() ở đây nữa.
    # File vật lý sẽ được xóa bởi script dọn dẹp sau 30 ngày.

    result.is_deleted = True
    # Hẹn giờ xóa vĩnh viễn sau 30 ngày (hoặc lấy từ cấu hình UserProfile nếu muốn)
    result.delete_at = timezone.now() + timedelta(days=30)
    result.save()

    # 3. Thông báo cho người dùng
    # Cập nhật nội dung thông báo để người dùng biết họ có 30 ngày để khôi phục
    Notification.objects.create_notification(
        user=request.user,
        title=u"Đã chuyển vào thùng rác!",
        message=u"Bảng tính '{}' đã được chuyển vào mục lưu trữ và sẽ bị xóa vĩnh viễn sau 30 ngày.".format(
            result.title),
        level='warning',
        linked_to='/trash-bin/'
    )

    # 4. Điều hướng quay lại trang chủ hoặc trang danh sách
    return redirect('home')
