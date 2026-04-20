// -*- coding: utf-8 -*-

/**
 * Service xử lý chuyển đổi dữ liệu ảnh
 */
function getCroppedBlob(cropperInstance) {
	return new Promise((resolve) => {
		const canvas = cropperInstance.getCroppedCanvas({
			maxWidth: 2048,
			maxHeight: 2048
		});
		canvas.toBlob((blob) => {
			resolve(blob);
		}, 'image/jpeg', 0.9);
	});
}