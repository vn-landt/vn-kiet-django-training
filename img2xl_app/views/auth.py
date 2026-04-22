# -*- coding: utf-8 -*-
import random

from djangae.fields import json
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from img2xl_app.forms import RegisterForm
from img2xl_app.models import UserProfile, Notification


def check_email_exists(request):
    """Bước 3: Kiểm tra trùng lặp email (AJAX)"""
    email = request.GET.get('email', '').lower().strip()

    if not email:
        return JsonResponse({'is_taken': False})

    # Kiểm tra xem email đã tồn tại trong hệ thống chưa
    is_taken = User.objects.filter(email=email).exists()

    return JsonResponse({'is_taken': is_taken})


def send_otp(request):
    """Bước 5: Tạo và gửi mã OTP qua Gmail (AJAX)"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email', '').lower().strip()

            if not email:
                return JsonResponse({'success': False, 'message': u'Vui lòng nhập email.'}, status=400)

            # Ràng buộc: Giới hạn tối đa 3 lần gửi mã trong 1 phiên (Session)
            otp_count = request.session.get('otp_count', 0)
            if otp_count >= 3:
                return JsonResponse({
                    'success': False,
                    'message': u'Bạn đã hết lượt gửi mã (tối đa 5 lần/1 ngày).'
                }, status=400)

            # Tạo mã 4 số ngẫu nhiên
            otp_code = str(random.randint(1000, 9999))

            # Lưu mã OTP và email mục tiêu vào session để đối chiếu sau này
            request.session['otp_code'] = otp_code
            request.session['otp_target_email'] = email
            request.session['otp_count'] = otp_count + 1
            # Mã có hiệu lực trong 5 phút
            request.session.set_expiry(300)

            # Gửi mail qua SMTP Gmail
            subject = u'[Xác thực] Mã đăng ký tài khoản của bạn'
            message = u'Mã OTP của bạn là: {}. Vui lòng không cung cấp mã này cho bất kỳ ai.'.format(otp_code)

            send_mail(subject, message, settings.EMAIL_HOST_USER, [email])

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False}, status=405)


def verify_otp_ajax(request):
    """Bước 5: Xác nhận mã OTP người dùng nhập (AJAX)"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_otp = data.get('otp')
            saved_otp = request.session.get('otp_code')
            target_email = request.session.get('otp_target_email')

            if saved_otp and user_otp == saved_otp:
                # Đánh dấu session đã xác thực thành công cho email cụ thể này
                request.session['is_otp_verified'] = True
                request.session['verified_email'] = target_email
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'message': u'Mã xác nhận không đúng.'}, status=400)
        except:
            return JsonResponse({'success': False}, status=400)

    return JsonResponse({'success': False}, status=405)


def register(request):
    """Bước 6: Xử lý đăng ký cuối cùng khi nhấn nút Hoàn tất"""
    if request.method == "POST":
        form = RegisterForm(request.POST)

        # Lấy thông tin xác thực từ session
        is_otp_verified = request.session.get('is_otp_verified', False)
        verified_email = request.session.get('verified_email', '')

        if form.is_valid():
            # KIỂM TRA CHÉO BẢO MẬT:
            # 1. Đã qua bước OTP chưa?
            # 2. Email trong form có đúng là email vừa được xác thực OTP không?
            current_email = form.cleaned_data.get('email').lower().strip()

            if is_otp_verified and current_email == verified_email:
                # Lưu User vào Auth User
                user = form.save()

                # Tạo UserProfile đi kèm (Yêu cầu của bạn)
                UserProfile.objects.get_or_create(user=user)

                # Thông báo đăng ký tài khoản thành công
                Notification.objects.create_notification(
                    user=user,
                    title=u"Chào mừng thành viên mới!",
                    # Sửa: Dùng user.username thay vì res_obj.title (vì lúc này chưa có bảng tính nào)
                    message=u"Chào mừng '{}' đã gia nhập Extractor AI.".format(user.username),
                    level='success',  # Sửa lỗi chính tả 'succes' -> 'success'
                    linked_to=None
                )

                # Xóa các dấu vết xác thực trong session sau khi thành công
                keys_to_delete = ['otp_code', 'otp_target_email', 'is_otp_verified', 'verified_email']
                for key in keys_to_delete:
                    if key in request.session:
                        del request.session[key]

                # Đăng nhập và chuyển hướng
                login(request, user)
                return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'img2xl_app/registration/register.html', {'form': form})


def forgot_password_view(request):
    """Hiển thị trang nhập email để lấy lại mật khẩu"""
    return render(request, 'img2xl_app/registration/forgot_password.html')


@csrf_exempt  # Hoặc đảm bảo JS gửi CSRF qua Header
def reset_password_final(request):
    if request.method == "POST":
        data = json.loads(request.body)
        new_password = data.get('password')
        email = data.get('email')

        # Kiểm tra bảo mật: Session phải đã xác thực OTP thành công
        is_verified = request.session.get('is_otp_verified', False)
        verified_email = request.session.get('verified_email', '')

        if is_verified and email.lower().strip() == verified_email.lower().strip():
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()

                # Quan trọng: Xóa session để tránh dùng lại mã cũ
                del request.session['is_otp_verified']
                del request.session['otp_code']

                # Thông báo đặt lại mật khẩu thành công
                Notification.objects.create_notification(
                    user=user,
                    title=u"Đặt lại mật khẩu!",
                    message=u"Đặt lại mật khẩu thành công!",
                    level='success',
                    linked_to=None
                )

                return JsonResponse({'success': True})
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'message': u'Tài khoản không tồn tại.'}, status=404)
        else:
            return JsonResponse({'success': False, 'message': u'Chưa xác thực mã OTP.'}, status=403)

    return JsonResponse({'success': False}, status=405)