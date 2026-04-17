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
 * Chuyển đổi số thứ tự cột thành nhãn chữ (0 -> A, 1 -> B, 26 -> AA)
 */
function expmdl_getColumnLabel(n) {
	let label = "";
	while (n >= 0) {
		label = String.fromCharCode((n % 26) + 65) + label;
		n = Math.floor(n / 26) - 1;
	}
	return label;
}

/**
 * Tính toán tỷ lệ scale để bảng vừa với container
 */
function calculateScale(container, table) {
	const containerW = container.offsetWidth - 40;
	const containerH = container.offsetHeight - 40;
	return Math.min(containerW / table.scrollWidth, containerH / table.scrollHeight, 1);
}