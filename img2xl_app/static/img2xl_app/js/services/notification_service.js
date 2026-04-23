// -*- coding: utf-8 -*-
/**
 * Service xử lý các yêu cầu API cho thông báo
 */
function apiToggleRead(notiId) {
	return fetch('/notifications/toggle-read/' + notiId + '/', {
		method: 'POST',
		headers: {'X-CSRFToken': getCSRFToken()}
	}).then(res => res.json());
}

function apiDeleteNoti(notiId) {
	return fetch('/notifications/delete/' + notiId + '/', {
		method: 'POST',
		headers: {'X-CSRFToken': getCSRFToken()}
	}).then(res => res.json());
}

function apiMarkAllRead() {
	return fetch('/notifications/mark-all-read/', {
		method: 'POST',
		headers: {'X-CSRFToken': getCSRFToken()}
	}).then(res => res.json());
}

function apiDeleteAll() {
	return fetch('/notifications/delete-all/', {
		method: 'POST',
		headers: {'X-CSRFToken': getCSRFToken()}
	}).then(res => res.json());
}

// Service lấy nội dung HTML của danh sách thông báo
function apiGetNotificationsHtml() {
	return fetch('/api/get-latest-html/', { // Thay URL đúng của bạn
		headers: {'X-CSRFToken': getCSRFToken()}
	}).then(res => {
		if (!res.ok) throw new Error("Network response was not ok");
		return res.text(); // Trả về dạng chuỗi HTML
	});
}