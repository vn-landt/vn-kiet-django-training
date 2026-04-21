// -*- coding: utf-8 -*-

/**
 * Xóa một bản ghi lịch sử trích xuất
 */
function apiDeleteHistory(resultId) {
	return fetch(`/home/delete/${resultId}/`, {
		method: 'POST',
		headers: {
			'X-CSRFToken': getCSRFToken(),
			'X-Requested-With': 'XMLHttpRequest'
		}
	});
}

/**
 * Tạo một bảng tính trống mới
 */
function apiCreateBlankSpreadsheet(name) {
	return $.post('/create-spreadsheet-blank/', {'name': name});
}

/**
 * Gửi ảnh đơn lẻ để trích xuất (Tạo mới Result)
 */
function apiExtractSingleImage(formData) {
	return fetch('/extract-only-api/', {
		method: 'POST',
		body: formData,
		headers: {'X-CSRFToken': getCSRFToken()}
	}).then(res => res.json());
}

/**
 * Gửi hàng loạt ảnh để trích xuất
 */
function apiBatchExtractImages(formData) {
	return fetch('/batch-extract-api/', {
		method: 'POST',
		body: formData,
		headers: {'X-CSRFToken': getCSRFToken()}
	}).then(res => res.json());
}