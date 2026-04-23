// Biến cờ để kiểm soát việc đóng dropdown
let isProcessingSwal = false;


$(document).ready(function () {
	// Hàm này chạy mỗi khi trang load lại
	syncBadgeCount();
});
// Ngăn Dropdown đóng khi đang hiển thị SweetAlert2
$(document).on('hide.bs.dropdown', '.dropdown', function (e) {
	if (isProcessingSwal) {
		e.preventDefault(); // Chặn sự kiện ẩn dropdown
	}
});

// --- 1. Tiện ích ---
function getCSRFToken() {
	const meta = document.querySelector('meta[name="csrf-token"]');
	return meta ? meta.getAttribute('content') : '';
}

window.updateNotificationBadge = function (count) {
	const bellContainer = document.getElementById('notiDropdown');
	if (!bellContainer) return;
	
	let badge = bellContainer.querySelector('.badge');
	
	if (count > 0) {
		if (!badge) {
			badge = document.createElement('span');
			badge.className = 'badge badge-danger position-absolute';
			badge.style = 'top: 0; right: 0; font-size: 0.6rem;';
			bellContainer.appendChild(badge);
		}
		badge.innerText = count > 99 ? '99+' : count;
	} else {
		if (badge) badge.remove();
	}
};

// Hàm đếm số lượng chưa đọc thực tế và cập nhật lên chuông
function syncBadgeCount() {
	const unreadCount = document.querySelectorAll('.noti-item[data-read="false"]').length;
	window.updateNotificationBadge(unreadCount);
}

// Hàm làm mới toàn bộ danh sách từ Server (Dùng window để gọi từ util.js)
window.refreshNotifications = function () {
	const listContainer = document.getElementById('global-noti-list');
	if (!listContainer) return;
	
	// Gọi hàm từ file service.js của bạn
	apiGetNotificationsHtml()
		.then(html => {
			listContainer.innerHTML = html;
			syncBadgeCount(); // Đếm lại sau khi đã thay nội dung mới
		})
		.catch(err => console.error("Lỗi đồng bộ:", err));
};

// --- 2. Xử lý chính (Đã kết hợp Service API) ---

function handleNotiToggle(event, notiId) {
	if (event.target.closest('.noti-actions') || event.target.tagName === 'A') return;
	
	event.stopPropagation();
	
	// Sử dụng service apiToggleRead
	apiToggleRead(notiId).then(data => {
		if (data.success) {
			const el = document.getElementById('noti-' + notiId);
			if (data.is_read) {
				el.classList.remove('unread-style');
				el.setAttribute('data-read', 'true');
			} else {
				el.classList.add('unread-style');
				el.setAttribute('data-read', 'false');
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
		if (result.isConfirmed) {
			// Sử dụng service apiDeleteNoti
			apiDeleteNoti(notiId).then(data => {
				if (data.success) {
					const el = document.getElementById('noti-' + notiId);
					$(el).fadeOut(200, function () {
						$(this).remove();
						syncBadgeCount();
						if (document.querySelectorAll('.noti-item').length === 0) {
							document.getElementById('global-noti-list').innerHTML = '<div class="p-4 text-center text-muted">Trống</div>';
						}
					});
				}
			});
		}
		isProcessingSwal = false; // Reset cờ sau khi đóng Swal
	});
}

// --- 3. Lọc & Đồng bộ hàng loạt ---

function handleFilterClick(event, mode) {
	event.stopPropagation();
	
	const container = event.currentTarget.parentElement;
	const buttons = container.querySelectorAll('.btn');
	buttons.forEach(btn => btn.classList.remove('active'));
	
	event.currentTarget.classList.add('active');
	
	const items = document.querySelectorAll('.noti-item');
	items.forEach(item => {
		if (mode === 'unread') {
			item.getAttribute('data-read') === 'false' ? $(item).show() : $(item).hide();
		} else {
			$(item).show();
		}
	});
}

function markAllRead(event) {
	if (event) event.stopPropagation();
	
	// Sử dụng service apiMarkAllRead
	apiMarkAllRead().then(data => {
		if (data.success) {
			document.querySelectorAll('.noti-item').forEach(el => {
				el.classList.remove('unread-style');
				el.setAttribute('data-read', 'true');
			});
			syncBadgeCount();
		}
	});
}

function deleteAllNotis(event) {
	if (event) event.stopPropagation();
	isProcessingSwal = true;
	
	Swal.fire({
		title: 'Xóa sạch thông báo?',
		icon: 'warning',
		showCancelButton: true,
		confirmButtonText: 'Xóa hết'
	}).then((result) => {
		if (result.isConfirmed) {
			// Sử dụng service apiDeleteAll
			apiDeleteAll().then(data => {
				if (data.success) {
					document.getElementById('global-noti-list').innerHTML = '<div class="p-4 text-center text-muted">Trống</div>';
					syncBadgeCount();
				}
			});
		}
		isProcessingSwal = false; // Reset cờ sau khi đóng Swal
	});
}