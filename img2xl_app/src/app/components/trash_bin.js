// -*- coding: utf-8 -*-
$(document).ready(function() {
	// Lắng nghe sự kiện UI
	$('.check-all').on('change', function() {
		var targetType = $(this).data('target');
		var isChecked = $(this).is(':checked');
		$('.item-' + targetType).prop('checked', isChecked);
		updateBatchUI();
	});

	$(document).on('change', '.check-item', updateBatchUI);

	$('a[data-toggle="tab"]').on('shown.bs.tab', function() {
		$('.check-item, .check-all').prop('checked', false);
		updateBatchUI();
	});
});

function updateBatchUI() {
	var count = $('.check-item:checked').length;
	if (count > 0) {
		$('#btn-restore-batch').fadeIn();
		$('#selected-count').text(count);
	} else {
		$('#btn-restore-batch').fadeOut();
	}
}

/**
 * Điều khiển logic UI khi khôi phục
 */
function handleRestore(type, ids, titleText) {
	Swal.fire({
		title: titleText,
		icon: 'question',
		showCancelButton: true,
		confirmButtonColor: '#28a745',
		confirmButtonText: 'Đồng ý'
	}).then((result) => {
		if (result.isConfirmed) {
			executeRestore(type, ids);
		}
	});
}

/**
 * Cầu nối giữa UI và Service
 */
function executeRestore(type, ids) {
	Swal.fire({
		title: 'Đang xử lý...',
		allowOutsideClick: false,
		onBeforeOpen: () => { Swal.showLoading(); }
	});

	// GỌI SERVICE
	restoreItemAPI(type, ids)
		.done(function(response) {
			Swal.fire('Thành công!', response.message, 'success')
				.then(() => { location.reload(); });
		})
		.fail(function(xhr) {
			var msg = (xhr.responseJSON && xhr.responseJSON.message)
				? xhr.responseJSON.message : "Lỗi hệ thống";
			Swal.fire('Thất bại', msg, 'error');
		});
}