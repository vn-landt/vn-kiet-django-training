# -*- coding: utf-8 -*-
from datetime import timedelta
from time import timezone

from django.db.models import Count
from django.http import HttpResponse

from img2xl_app.models import UploadedFile, Notification


def auto_cleanup_task(request):
    now = timezone.now()
    in_12h = now + timedelta(hours=12)
    trash_count = 0
    permanent_count = 0
    warringDel_count = 0

    # --- PHẦN 1: DỌN DẸP CÁC FILE ĐÃ HẾT HẠN (QUÁ KHỨ) ---
    expired_files = UploadedFile.objects.filter(
        delete_at__isnull=False,
        delete_at__lte=now
    )

    for f in expired_files:
        if not f.is_deleted:
            # Chuyển vào thùng rác
            f.is_deleted = True
            f.delete_at = now + timedelta(days=30)
            f.save()
            trash_count += 1

        else:
            # Xóa vĩnh viễn
            filename_storage = f.filename
            user_storage = f.user
            f.delete()  # Gọi hàm xóa vật lý nếu cần trước dòng này
            permanent_count += 1

    if trash_count > 0:
        # Thông báo cho người dùng về việc chuyển vào thùng rác
        Notification.objects.create_notification(
            user=request.user,
            title=u"Ảnh đã hết hạn!",
            message=u"Tự động dọn dẹp đã chuyển '{}' ảnh vào thùng rác và sẽ xóa vĩnh viễn sau 30 ngày.".format(trash_count),
            level='warning'
        )

    if permanent_count > 0:
        # Thông báo cho người dùng về việc xóa vĩnh viễn
        Notification.objects.create_notification(
            user=request.ser,
            title=u"Xóa vĩnh viễn!",
            message=u"Tự động dọn dẹp đã xoá '{}' ảnh vĩnh viễn khỏi hệ thống do hết hạn lưu trữ.".format(permanent_count),
            level='error'
        )

    # --- PHẦN 2: TÌM VÀ CẢNH BÁO CÁC FILE SẮP HẾT HẠN (TRONG 12H TỚI) ---
    # Lấy danh sách ảnh sắp đến hạn xóa (bao gồm cả sắp vào thùng rác và sắp xóa thật)
    upcoming_files = UploadedFile.objects.filter(
        delete_at__gt=now,
        delete_at__lte=in_12h
    ).values('user').annotate(total=Count('id'))

    for entry in upcoming_files:
        from django.contrib.auth.models import User
        target_user = User.objects.get(id=entry['user'])
        count = entry['total']
        warringDel_count += 1

    if warringDel_count > 0:
        # Tạo một thông báo tổng hợp duy nhất cho mỗi user để tránh spam
        Notification.objects.create_notification(
            user=request.user,
            title=u"Sắp đến hạn xóa dữ liệu!",
            message=u"Lưu ý: Bạn có {} ảnh sẽ bị xóa hoặc chuyển vào thùng rác trong vòng 12 giờ tới.".format(warringDel_count),
            level='info',
            linked_to='/documents/'  # Đường dẫn đến trang quản lý ảnh của bạn
        )

    return HttpResponse(u"Đã hoàn thành dọn dẹp và gửi cảnh báo 12h.")