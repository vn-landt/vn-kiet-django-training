// -*- coding: utf-8 -*-

/**
 * Xử lý sau khi Crop ảnh đơn lẻ
 */
async function onImageCropped(blob, languagesStr, originalFileName, deleteDuration) {
	const formData = new FormData();
	formData.append('file', blob, "processed_image.jpg");
	formData.append('original_filename', originalFileName || "image_" + Date.now() + ".jpg");
	formData.append('save_db', 'true');
	formData.append('languages', languagesStr || 'all');
	formData.append('deleteDuration', deleteDuration);
	
	Swal.fire({title: 'Đang xử lý...', allowOutsideClick: false, didOpen: () => Swal.showLoading()});
	
	apiExtractSingleImage(formData)
		.then(data => {
			Swal.close();
			if (data.status === 'success') {
				window.location.href = "/result/" + data.result_id + "/";
			} else if (data.status === 'limit_exceeded') {
				Swal.fire({
					title: 'Kho lưu trữ đầy!',
					text: data.message, // Thông báo từ backend: "Kho lưu trữ ảnh đã đầy (50/50)..."
					icon: 'warning',
					showCancelButton: true,
					confirmButtonColor: '#3085d6',
					cancelButtonColor: '#d33',
					confirmButtonText: 'Dọn dẹp ngay',
					cancelButtonText: 'Để sau'
				}).then((result) => {
					if (result.isConfirmed) {
						// Điều hướng người dùng đến trang quản lý tài liệu để xóa ảnh
						window.location.href = data.redirect_url;
					}
				});
			} else {
				Swal.fire('Lỗi', data.message, 'error');
			}
		})
		.catch(() => {
			Swal.close();
			Swal.fire('Lỗi kết nối', 'Không thể kết nối máy chủ.', 'error');
		});
}

/**
 * Bắt đầu trích xuất hàng loạt
 */
async function startBatchProcessing() {
	if (window.batchFiles.length === 0) return;
	
	const languagesStr = Array.from(document.querySelectorAll('input[name="langs"]:checked')).map(cb => cb.value).join(',');
	const deleteDuration = document.getElementById('deleteDuration').value;
	const formData = new FormData();
	
	window.batchFiles.forEach((item) => {
		formData.append('files', item.file);
	});
	formData.append('languages', languagesStr);
	formData.append('deleteDuration', deleteDuration);
	
	Swal.fire({
		title: 'Đang xử lý...',
		html: `Đang phân tích ${window.batchFiles.length} ảnh...`,
		allowOutsideClick: false,
		didOpen: () => Swal.showLoading()
	});
	
	try {
		const result = await apiBatchExtractImages(formData);
		Swal.close();
		if (result.status === 'success') {
			window.location.href = "/result/" + result.result_id + "/";
		} else {
			Swal.fire('Lỗi', result.message, 'error');
		}
	} catch (err) {
		Swal.close();
		Swal.fire('Lỗi', 'Lỗi kết nối máy chủ.', 'error');
	}
}