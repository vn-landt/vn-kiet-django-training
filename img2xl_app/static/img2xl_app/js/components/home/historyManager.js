// -*- coding: utf-8 -*-

/**
 * Lắng nghe sự kiện click vào nút xóa trong danh sách lịch sử
 */
function initHistoryManager() {
	document.addEventListener('click', function (e) {
		const deleteBtn = e.target.closest('.delete-history-btn');
		if (!deleteBtn) return;
		
		const resultId = deleteBtn.getAttribute('data-id');
		const historyItem = document.getElementById(`item-${resultId}`);
		
		Swal.fire({
			title: 'Xác nhận xóa?',
			text: "Dữ liệu và file ảnh liên quan sẽ bị xóa vĩnh viễn!",
			icon: 'warning',
			showCancelButton: true,
			confirmButtonColor: '#d33',
			confirmButtonText: 'Vâng, xóa nó!'
		}).then((result) => {
			if (result.isConfirmed) {
				deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
				deleteBtn.disabled = true;
				
				apiDeleteHistory(resultId)
					.then(response => {
						if (response.ok || response.redirected) {
							$(historyItem).fadeOut(400, function () {
								$(this).remove();
								if (document.querySelectorAll('.history-item').length === 0) {
									document.querySelector('.history-list').innerHTML = '<p class="text-muted text-center py-3">Chưa có dữ liệu.</p>';
								}
							});
							triggerHeaderUpdate();
						} else {
							throw new Error('Lỗi');
						}
					})
					.catch(() => {
						deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
						deleteBtn.disabled = false;
						Swal.fire('Thất bại', 'Không thể xóa bản ghi.', 'error');
					});
			}
		});
	});
}