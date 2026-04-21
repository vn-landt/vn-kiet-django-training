// -*- coding: utf-8 -*-
/**
 * Service xử lý các yêu cầu liên quan đến Thùng rác
 */
function apiRestoreItems(type, ids) {
	return $.ajax({
		url: "/trash-bin/api/restore/", // Khớp với name='restore_item_api' trong urls.py
		method: 'POST',
		data: {
			'type': type,
			'ids[]': ids,
		}
	});
}