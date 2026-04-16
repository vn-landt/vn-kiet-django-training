# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from img2xl_app.models import ExtractedResult, UploadedFile, Notification


@login_required
def trash_bin_view(request):
    """Hiển thị trang Thùng rác"""
    deleted_results = ExtractedResult.objects.filter(user=request.user, is_deleted=True).order_by('-delete_at')
    deleted_files = UploadedFile.objects.filter(user=request.user, is_deleted=True).order_by('-delete_at')
    return render(request, 'trash_bin.html', {
        'deleted_results': deleted_results,
        'deleted_files': deleted_files,
    })


@login_required
def restore_item_api(request):
    """
    API DUY NHẤT xử lý khôi phục.
    Hỗ trợ: Khôi phục 1 ảnh, nhiều ảnh, 1 bảng, nhiều bảng.
    """
    if request.method == 'POST':
        item_type = request.POST.get('type')
        ids = request.POST.getlist('ids[]')

        if not ids:
            return JsonResponse({'status': 'error', 'message': u'Chưa chọn mục nào'}, status=400)

        try:
            # Lấy số lượng mục được chọn để đưa vào thông báo
            count = len(ids)
            label = u""  # Để phân biệt "ảnh" hay "bảng"

            if item_type == 'image':
                # Khôi phục hàng loạt ảnh
                UploadedFile.objects.filter(id__in=ids, user=request.user).update(
                    is_deleted=False, delete_at=None
                )
                label = u"ảnh"

            elif item_type == 'table':
                # Khôi phục bảng và ảnh liên quan
                tables = ExtractedResult.objects.filter(id__in=ids, user=request.user)
                for table in tables:
                    table.is_deleted = False
                    table.delete_at = None
                    table.save()

                    # Khôi phục luôn ảnh kèm theo bảng
                    if table.source_file_ids:
                        UploadedFile.objects.filter(
                            id__in=table.source_file_ids,
                            user=request.user
                        ).update(is_deleted=False, delete_at=None)

                label = u"bảng"
            else:
                return JsonResponse({'status': 'error', 'message': u'Loại dữ liệu lạ'}, status=400)

            # Tạo nội dung thông báo động
            msg = u"Đã khôi phục %d %s thành công!" % (count, label)

            # --- LƯU THÔNG BÁO VÀO DATABASE ---
            Notification.objects.create_notification(
                user=request.user,
                title=u"Khôi phục dữ liệu",
                message=msg,
                level='success',
                linked_to='/documents/'  # Bạn có thể truyền link trang chủ nếu muốn
            )

            return JsonResponse({'status': 'success', 'message': msg})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': unicode(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': u'Method not allowed'}, status=405)