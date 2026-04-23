# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from django.utils import timezone

from djangae.fields import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from img2xl_app.models import ExtractedResult, UploadedFile, Notification
from img2xl_app.services.table_handler import TableFileHandler


@login_required
def documents_view(request):
	sort = request.GET.get('sort', 'recent')
	user = request.user
	
	# 1. Lấy danh sách bảng tính (dùng cho Sidebar 20%)
	results_query = ExtractedResult.objects.filter(user=user, is_deleted=False)
	
	# 2. Lấy TOÀN BỘ ảnh của user (dùng cho Gallery 80%)
	# Điều này đảm bảo ảnh vẫn hiện dù bảng tính bị xóa
	all_images_query = UploadedFile.objects.filter(user=user, is_deleted=False)
	
	# Logic sắp xếp cho bảng tính
	if sort == 'oldest':
		results = results_query.order_by('created_at')
		all_images = all_images_query.order_by('uploaded_at')
	else:
		results = results_query.order_by('-updated_at')
		all_images = all_images_query.order_by('-uploaded_at')
	
	return render(request, 'img2xl_app/documents.html', {
		'results': results,  # Dùng cho sidebar
		'all_images': all_images,  # Dùng cho gallery ảnh
		'extractedResult': all_images.count(),  # Đếm ảnh thay vì đếm bảng
		'current_sort': sort
	})


@require_POST
def create_spreadsheet_blank(request):
	"""Tạo bảng trống """
	name = request.POST.get('name', 'Untitled Spreadsheet')
	user = request.user
	
	# Tạo thẳng ExtractedResult với source_file_ids rỗng
	res_obj = ExtractedResult.objects.create(
		user=user,
		title=name,
		source_file_ids=[],  # Bảng trống
		status='success',
		is_draft=True
	)
	
	empty_data = [["" for _ in range(5)] for _ in range(5)]
	handler = TableFileHandler(res_obj)
	handler.save_data(empty_data)
	
	# Thông báo tạo bảng tính trống thành công
	Notification.objects.create_notification(
		user=request.user,
		title=u"Tạo bảng trống!",
		message=u"Đã tạo bảng tính trống!",
		level='success',
		linked_to=reverse('result_detail', kwargs={'result_id': res_obj.id})
	)
	
	return JsonResponse(
		{'status': 'success', 'redirect_url': reverse('result_detail', args=[res_obj.id])})


@login_required
@require_POST
def update_title_api(request, result_id):
	"""API: Đổi tên bảng tính"""
	result = get_object_or_404(ExtractedResult, id=result_id, user=request.user)
	old_title = result.title  # Lưu lại tên cũ để dùng cho thông báo
	new_title = request.POST.get('title')
	
	if new_title:
		result.title = new_title
		result.save()
		
		msg = u"Đã đổi tên bảng '{0}' thành '{1}'!".format(old_title, new_title)
		
		Notification.objects.create_notification(
			user=request.user,
			title=u"Cập nhật thành công",
			message=msg,
			level='success',
			linked_to=reverse('result_detail', kwargs={'result_id': result.id})
		)
		
		return JsonResponse({'status': 'success'})
	
	# Trường hợp lỗi
	return JsonResponse(
		{'status': 'error', 'message': u'Tiêu đề không được để trống'},
		status=400
	)


# Xoá bảng tính ở documents/
@login_required
@require_POST
def delete_result_api(request, result_id):
	"""API: Xóa mềm bảng tính"""
	result = get_object_or_404(ExtractedResult, id=result_id, user=request.user)
	
	# THỰC HIỆN SOFT DELETE
	result.is_deleted = True
	# Hẹn giờ xóa vĩnh viễn (ví dụ 30 ngày sau)
	result.delete_at = timezone.now() + timedelta(days=30)
	result.save()
	
	# Thông báo
	Notification.objects.create_notification(
		user=request.user,
		title=u"Đã chuyển vào thùng rác!",
		message=u"Bảng tính '{}' đã được chuyển vào mục lưu trữ và sẽ bị xóa vĩnh viễn sau 30 ngày".format(
			result.title),
		level='warning',
		linked_to='/trash-bin/'
	)
	
	return JsonResponse({'status': 'success'})


@login_required
@require_POST
def delete_image_api(request, img_id):
	"""API: Xóa mềm 1 ảnh (Soft Delete)"""
	# Vẫn lấy ảnh như cũ, đảm bảo đúng chủ sở hữu
	image = get_object_or_404(UploadedFile, id=img_id, user=request.user)
	
	# THỰC HIỆN SOFT DELETE
	image.is_deleted = True
	image.delete_at = timezone.now()  # Đánh dấu thời điểm xóa ngay bây giờ
	image.save()
	
	# Thông báo (Bạn có thể sửa lại nội dung cho chính xác hơn)
	Notification.objects.create_notification(
		user=request.user,
		title=u"Đã chuyển vào thùng rác!",
		message=u"Ảnh '{}' đã được xoá khỏi thư viện và sẽ bị xóa vĩnh viễn sau 30 ngày.".format(
			image.filename),
		level='info',
		linked_to='/trash-bin/'
	)
	
	return JsonResponse({
		'status': 'success',
		'message': 'Image moved to trash'
	})


@login_required
@require_POST
def bulk_delete_images_api(request):
	"""API: Xóa mềm nhiều ảnh cùng lúc"""
	try:
		# 1. Lấy dữ liệu JSON từ request.body
		data = json.loads(request.body)
		ids = data.get('ids', [])
		
		if not ids:
			return JsonResponse({'status': 'error', 'message': u'Không có ID nào được cung cấp'},
								status=400)
		
		# 2. Tính toán thời gian xóa vĩnh viễn (ví dụ: 30 ngày sau)
		scheduled_delete_at = timezone.now() + timedelta(days=30)
		
		# 3. Thực hiện cập nhật hàng loạt (Bulk Update)
		# Chỉ cập nhật những ảnh thuộc về user hiện tại
		updated_count = UploadedFile.objects.filter(
			id__in=ids,
			user=request.user
		).update(
			is_deleted=True,
			delete_at=scheduled_delete_at
		)
		
		if updated_count > 0:
			# 4. Thông báo cho người dùng
			Notification.objects.create_notification(
				user=request.user,
				title=u"Đã chuyển vào thùng rác!",
				message=u"Hệ thống đã chuyển {} ảnh vào thùng rác và sẽ xoá vĩnh viễn sau 30 ngày.".format(
					updated_count),
				level='warning',
				linked_to='/trash-bin/'
			)
		
		return JsonResponse({
			'status': 'success',
			'count': updated_count,
			'message': u'Đã chuyển các ảnh vào thùng rác'
		})
	
	except ValueError:
		return JsonResponse({'status': 'error', 'message': u'Dữ liệu JSON không hợp lệ'},
							status=400)
	except Exception as e:
		return JsonResponse({'status': 'error', 'message': unicode(e)}, status=500)


def update_image_info(request):
	if request.method == "POST":
		img_id = request.POST.get('id')
		new_name = request.POST.get('filename')
		duration = request.POST.get('duration')  # 'keep', '0', '5', '60', '1440'
		
		try:
			img_obj = UploadedFile.objects.get(id=img_id, user=request.user)
			
			# 1. Cập nhật tên
			img_obj.filename = new_name
			
			# 2. Cập nhật thời gian xóa nếu không chọn "Giữ nguyên"
			if duration != 'keep':
				duration_int = int(duration)
				if duration_int > 0:
					img_obj.delete_at = timezone.now() + timedelta(minutes=duration_int)
				else:
					img_obj.delete_at = None  # Chuyển sang vĩnh viễn
				# Thông báo xoá hàng loạt ảnh
				Notification.objects.create_notification(
					user=request.user,
					title=u"Tự động xoá ảnh!",
					message=u"Một số ảnh đã được chỉnh thời gian tự động xoá!.",
					level='info',
					linked_to='/documents/'
				)
			
			img_obj.save()
			return JsonResponse({'status': 'success'})
		
		except Exception as e:
			logging.error(u"Error updating image info: %s", str(e))
			return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
	
	return JsonResponse({'status': 'error'}, status=405)


def bulk_update_time(request):
	if request.method == "POST":
		ids = request.POST.getlist('ids[]')
		duration_min = int(request.POST.get('duration', 0))
		user = request.user
		
		# 1. Tính toán thời điểm xóa mới
		new_expiry = None
		if duration_min > 0:
			new_expiry = timezone.now() + timedelta(minutes=duration_min)
		
		try:
			# 2. Cập nhật hàng loạt tất cả các ID thuộc về User này
			# Lệnh .update() thực hiện 1 câu lệnh SQL duy nhất, cực kỳ tối ưu
			UploadedFile.objects.filter(
				id__in=ids,
				user=user
			).update(delete_at=new_expiry)
			
			# Thông báo xoá hàng loạt ảnh
			Notification.objects.create_notification(
				user=request.user,
				title=u"Tự động xoá ảnh!",
				message=u"Một số ảnh đã được chỉnh thời gian tự động xoá!.",
				level='info',
				linked_to='/documents/'
			)
			
			return JsonResponse({'status': 'success', 'count': len(ids)})
		except Exception as e:
			return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
	
	return JsonResponse({'status': 'error'}, status=405)
