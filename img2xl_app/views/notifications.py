# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from img2xl_app.models import Notification


# Lấy danh sách thông báo mới nah61t
@login_required
def api_get_latest_notifications(request):
    try:
        # Lấy dữ liệu
        notifications = Notification.objects.filter(user=request.user)[:15]
        
        # Render ra file html nhỏ
        return render(request, 'img2xl_app/includes/noti_list_items.html', {
            'notifications': notifications
        })
    except Exception as e:
        # Nếu lỗi, nó sẽ in ra màn hình terminal của bạn
        print("Lỗi View: ", str(e))
        from django.http import HttpResponse
        return HttpResponse(str(e), status=500)


# 1. Đánh dấu một thông báo là đã đọc
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
