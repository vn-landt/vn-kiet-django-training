# -*- coding: utf-8 -*-
from datetime import timedelta
from django.utils import timezone

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from img2xl_app.services.ai_extraction_images import generate_images


@login_required
@require_POST
def generate_ai_images(request):
	# 1. Trích xuất dữ liệu từ request
	is_create_new = request.POST.get('save_db') == 'true'
	current_result_id = request.POST.get('result_id')
	languages = request.POST.get('languages', 'all')
	
	# Xử lý files
	files = request.FILES.getlist('files')
	if not files and 'file' in request.FILES:
		files = [request.FILES['file']]
	
	# Xử lý thời gian xóa tự động
	try:
		duration = int(request.POST.get('deleteDuration', 0))
		expiry_date = timezone.now() + timedelta(minutes=duration) if duration > 0 else None
	except:
		expiry_date = None
	
	# 2. Gọi Service
	try:
		results = generate_images(
			user=request.user,
			files=files,
			is_create_new=is_create_new,
			current_result_id=current_result_id,
			languages=languages,
			expiry_date=expiry_date
		)
		if results.get('status') == 'error':
			return JsonResponse(results, status=400)
		
		return JsonResponse(results)  # Trả về dict kết quả trực tiếp
	except Exception as e:
		return JsonResponse({'status': 'error', 'message': str(e)}, status=500)