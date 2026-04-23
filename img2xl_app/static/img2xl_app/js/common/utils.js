// -*- coding: utf-8 -*-

function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie !== '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = cookies[i].trim();
			if (cookie.substring(0, name.length + 1) === (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

// Cấu hình AJAX Header tự động cho toàn dự án
var csrftoken = getCookie('csrftoken');
$.ajaxSetup({
	beforeSend: function (xhr, settings) {
		if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
			xhr.setRequestHeader("X-CSRFToken", csrftoken);
		}
	}
});


/**
 * Chuyển đổi tọa độ Excel (A1) sang số (col: 0, row: 0)
 */
function parseCoords(cellStr) {
	const match = cellStr.toUpperCase().match(/^([A-Z]+)(\d+)$/);
	if (!match) return null;
	let colStr = match[1];
	let row = parseInt(match[2]) - 1;
	let col = 0;
	for (let i = 0; i < colStr.length; i++) {
		col = col * 26 + (colStr.charCodeAt(i) - 64);
	}
	return {col: col - 1, row: row};
}

/**
 * Thiết lập bảo mật CSRF cho toàn bộ các yêu cầu AJAX
 */
function setupCSRF() {
	const token = $('meta[name="csrf-token"]').attr('content');
	$.ajaxSetup({
		beforeSend: function (xhr, settings) {
			const isUnsafe = !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type);
			if (isUnsafe && !this.crossDomain) {
				xhr.setRequestHeader("X-CSRFToken", token);
			}
		}
	});
}

/* Lấy danh sách thông báo mới nhất */
window.triggerHeaderUpdate = function() {
    if (typeof window.refreshNotifications === 'function') {
        window.refreshNotifications();
    }
};