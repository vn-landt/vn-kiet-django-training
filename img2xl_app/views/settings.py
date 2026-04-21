# -*- coding: utf-8 -*-
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect

from img2xl_app.models import Notification
from img2xl_app.services.upload_image import upload_to_imgbb


@login_required
def settings_view(request):
    # Trả về trang settings, dữ liệu user đã có sẵn trong request.user
    return render(request, 'img2xl_app/settings.html')


@login_required
def update_account_settings(request):
    if request.method == 'POST':
        profile = request.user.profile

        # 1. Cập nhật thời gian tự động xóa (ép về kiểu int)
        auto_delete = request.POST.get('auto_delete_duration')
        if auto_delete is not None:
            profile.auto_delete_duration = int(auto_delete)

        # 2. Cập nhật Keep EXIF
        # Checkbox trong HTML: nếu tích sẽ gửi 'on', nếu không tích sẽ không gửi gì cả
        # profile.keep_exif = True if request.POST.get('keep_exif') == 'on' else False

        # 3. Lưu vào Database
        profile.save()

        # 4. Thông báo thành công và reload lại trang
        # Thông báo đặt lại mật khẩu thành công
        if int(auto_delete) == 0:
            msg = u"Đã đặt thời gian tự động xoá mặc định là: không tự động xoá'{0}' phút!"
        else:
            msg = u"Đã đặt thời gian tự động xoá mặc định là: '{0}' phút!".format(int(auto_delete))
            
        Notification.objects.create_notification(
            user=request.user,
            title=u"Đặt lại thời gian tự động xoá!",
            message=msg,
            level='success',
            linked_to='/settings/'
        )
        return_url = request.META.get('HTTP_REFERER', '/')
        return HttpResponseRedirect(return_url)
    
    return HttpResponseRedirect(request.path_info)


@login_required
def update_profile_settings(request):
    if request.method == 'POST':
        profile = request.user.profile

        # 1. Xử lý Upload Avatar (Nếu có file mới)
        avatar_file = request.FILES.get('avatar')
        if avatar_file:
            # Đọc file sang bytes
            image_bytes = avatar_file.read()
            # Gọi hàm của bạn
            new_avatar_url, error = upload_to_imgbb(image_bytes)

            if new_avatar_url:
                profile.avatar_url = new_avatar_url
            else:
                messages.error(request, u"Không thể upload ảnh: " + unicode(error))

        # 2. Cập nhật các trường thông tin khác
        profile.full_name = request.POST.get('full_name', '')
        profile.website = request.POST.get('website', '')
        profile.bio = request.POST.get('bio', '')
        profile.is_private = True  # Luôn đóng băng theo yêu cầu

        profile.save()
        messages.success(request, u"Hồ sơ đã được cập nhật thành công!")
        return_url = request.META.get('HTTP_REFERER', '/')
        return HttpResponseRedirect(return_url)
    
    return HttpResponseRedirect(request.path_info)


@login_required
def change_password(request):
    if request.method == 'POST':
        # 1. Lấy dữ liệu từ Form
        old_pass = request.POST.get('old_password')
        new_pass = request.POST.get('new_password')
        confirm_pass = request.POST.get('confirm_password')
        user = request.user

        # 2. Kiểm tra mật khẩu cũ có đúng không
        if not user.check_password(old_pass):
            messages.error(request, u"Mật khẩu cũ không chính xác!")
            return redirect('settings') # Quay lại trang settings/password

        # 3. Kiểm tra 2 mật khẩu mới có khớp nhau không
        if new_pass != confirm_pass:
            messages.error(request, u"Hai mật khẩu mới không khớp nhau!")
            return redirect('settings')

        # 4. Kiểm tra độ dài mật khẩu (tùy chọn nhưng nên có)
        if len(new_pass) < 6:
            messages.error(request, u"Mật khẩu mới phải có ít nhất 6 ký tự!")
            return redirect('settings')

        # 5. Thực thi đổi mật khẩu
        user.set_password(new_pass) # Hàm này tự động băm (hash) mật khẩu
        user.save()

        # Thông báo đặt lại mật khẩu thành công
        Notification.objects.create_notification(
            user=user,
            title=u"Đặt lại mật khẩu!",
            message=u"Đặt lại mật khẩu thành công!",
            level='success',
            linked_to='/settings/password/'
        )

        # 6. CẬP NHẬT SESSION (Rất quan trọng!)
        # Sau khi đổi mật khẩu, Django sẽ làm mới session hash.
        # Nếu không có dòng này, người dùng sẽ bị văng ra trang Login ngay lập tức.
        update_session_auth_hash(request, user)
        
        return_url = request.META.get('HTTP_REFERER', '/')
        return HttpResponseRedirect(return_url)
    
    return HttpResponseRedirect(request.path_info)
