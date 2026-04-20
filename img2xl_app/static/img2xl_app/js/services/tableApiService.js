// -*- coding: utf-8 -*-

/**
 * Lưu dữ liệu bảng (Nháp hoặc Final)
 */
function apiSaveTableData(currentData, isDraft) {
	return fetch(window.DJANGO_SAVE_URL, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-CSRFToken': getCookie('csrftoken')
		},
		body: JSON.stringify({
			'table_data': currentData,
			'is_draft': isDraft
		})
	}).then(res => res.json());
}

/**
 * Gửi vùng ảnh đã crop để AI trích xuất dữ liệu
 */
function apiExtractImagePart(formData) {
	const csrftoken = getCookie('csrftoken');
	return fetch("/extract-only-api/", {
		method: 'POST',
		headers: {'X-CSRFToken': csrftoken},
		body: formData
	}).then(res => res.json());
}

/**
 * Gọi API để tạo nội dung bằng AI từ prompt
 */
function apiGenerateAIContent(promptText) {
	return fetch('/api/generate-ai-content/', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-CSRFToken': getCookie('csrftoken')
		},
		body: JSON.stringify({'prompt': promptText})
	}).then(res => res.json());
}

