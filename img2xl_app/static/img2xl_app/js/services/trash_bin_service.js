// -*- coding: utf-8 -*-
/**
 * Service xử lý các yêu cầu liên quan đến Thùng rác
 */
function restoreItemAPI(type, ids) {
	// Trả về một Promise (deferred object) để Component xử lý kết quả
	return $.ajax({
		url: "/trash-bin/api/restore/",
		method: 'POST',
		data: {
			'type': type,
			'ids[]': ids
		}
	});
}