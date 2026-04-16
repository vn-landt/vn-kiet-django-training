# -*- coding: utf-8 -*-
# 1. Đánh dấu một thông báo là đã đọc
from django.http import JsonResponse

from img2xl_app.models import Notification


def mark_as_read(request, noti_id):
    if request.method == "POST":
        try:
            noti = Notification.objects.get(id=noti_id, user=request.user)
            noti.is_read = True
            noti.save()
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False}, status=400)

# 2. XÓA VĨNH VIỄN một thông báo
def delete_notification(request, noti_id):
    if request.method == "POST":
        try:
            noti = Notification.objects.get(id=noti_id, user=request.user)
            noti.delete()
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False}, status=400)

# 3. Đánh dấu tất cả là đã đọc
def mark_all_read(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})

# 4. XÓA SẠCH tất cả thông báo
def delete_all_notifications(request):
    if request.method == "POST":
        # Thay vì .update(is_deleted=True), ta dùng .delete() để xóa sạch khỏi DB
        Notification.objects.filter(user=request.user).delete()
        return JsonResponse({'success': True})

# 5. Đảo trạng thái Đọc/Chưa đọc
def toggle_read(request, noti_id):
    if request.method == "POST":
        try:
            noti = Notification.objects.get(id=noti_id, user=request.user)
            noti.is_read = not noti.is_read
            noti.save()
            return JsonResponse({'success': True, 'is_read': noti.is_read})
        except:
            return JsonResponse({'success': False}, status=400)
