// -*- coding: utf-8 -*-
let isProcessingSwal = false;

// Ngăn Dropdown đóng khi đang hiển thị SweetAlert2
$(document).on('hide.bs.dropdown', '.dropdown', function (e) {
	if (isProcessingSwal) e.preventDefault();
});

function syncBadgeCount() {
	const unreadCount = $('.noti-item[data-read="false"]').length;
	const $bell = $('#notiDropdown');
	let $badge = $bell.find('.badge');
	
	if (unreadCount > 0) {
		if ($badge.length === 0) {
			$badge = $('<span class="badge badge-danger position-absolute"></span>')
				.css({'top': 0, 'right': 0, 'font-size': '0.6rem'});
			$bell.append($badge);
		}
		$badge.text(unreadCount);
	} else {
		$badge.remove();
	}
}

function handleNotiToggle(event, notiId) {
	if (event.target.closest('.noti-actions') || event.target.tagName === 'A') return;
	event.stopPropagation();
	
	apiToggleRead(notiId).then(data => {
		if (data.success) {
			const $el = $('#noti-' + notiId);
			if (data.is_read) {
				$el.removeClass('unread-style').attr('data-read', 'true');
			} else {
				$el.addClass('unread-style').attr('data-read', 'false');
			}
			syncBadgeCount();
		}
	});
}

function deleteNoti(event, notiId) {
	event.stopPropagation();
	isProcessingSwal = true;
	
	Swal.fire({
		title: 'Xóa thông báo?',
		icon: 'warning',
		showCancelButton: true,
		confirmButtonColor: '#d33',
		confirmButtonText: 'Xóa'
	}).then((result) => {
		isProcessingSwal = false;
		if (result.isConfirmed) {
			apiDeleteNoti(notiId).then(data => {
				if (data.success) {
					$('#noti-' + notiId).fadeOut(200, function () {
						$(this).remove();
						syncBadgeCount();
						if ($('.noti-item').length === 0) {
							$('#global-noti-list').html('<div class="p-4 text-center">Trống</div>');
						}
					});
				}
			});
		}
	});
}

function handleFilterClick(event, mode) {
	event.stopPropagation();
	const $btn = $(event.currentTarget);
	$btn.addClass('active').siblings().removeClass('active');
	
	$('.noti-item').each(function () {
		const isUnread = $(this).attr('data-read') === 'false';
		(mode === 'unread' ? isUnread : true) ? $(this).show() : $(this).hide();
	});
}