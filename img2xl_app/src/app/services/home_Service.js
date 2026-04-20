// -*- coding: utf-8 -*-

/**
 * Xóa một bản ghi lịch sử trích xuất
 */
function apiDeleteHistory(resultId) {
	const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
	return fetch(`/home/delete/${resultId}/`, {
		method: 'POST',
		headers: {
			'X-CSRFToken': csrftoken,
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
	const csrftoken = $('meta[name="csrf-token"]').attr('content')
		|| (document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : "");
	return fetch('/extract-only-api/', {
		method: 'POST',
		body: formData,
		headers: {'X-CSRFToken': csrftoken}
	}).then(res => res.json());
}

/**
 * Gửi hàng loạt ảnh để trích xuất
 */
function apiBatchExtractImages(formData) {
	const csrftoken = $('meta[name="csrf-token"]').attr('content');
	return fetch('/batch-extract-api/', {
		method: 'POST',
		body: formData,
		headers: {'X-CSRFToken': csrftoken}
	}).then(res => res.json());
}