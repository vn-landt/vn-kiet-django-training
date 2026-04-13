// Biến cờ để kiểm soát việc đóng dropdown
let isProcessingSwal = false;

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

// Hàm đếm số lượng chưa đọc thực tế và cập nhật lên chuông
function syncBadgeCount() {
    // Đếm tất cả item có data-read="false"
    const unreadCount = document.querySelectorAll('.noti-item[data-read="false"]').length;
    const bellContainer = document.getElementById('notiDropdown');
    let badge = bellContainer.querySelector('.badge');

    if (unreadCount > 0) {
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'badge badge-danger position-absolute';
            badge.style = 'top: 0; right: 0; font-size: 0.6rem;';
            bellContainer.appendChild(badge);
        }
        badge.innerText = unreadCount;
    } else {
        if (badge) badge.remove();
    }
}

// --- 2. Xử lý chính ---

function handleNotiToggle(event, notiId) {
    // Nếu bấm vào nút xóa hoặc nút link thì không chạy toggle
    if (event.target.closest('.noti-actions') || event.target.tagName === 'A') return;

    // Ngăn đóng menu khi click
    event.stopPropagation();

    fetch('/notifications/toggle-read/' + notiId + '/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const el = document.getElementById('noti-' + notiId);
            if (data.is_read) {
                el.classList.remove('unread-style');
                el.setAttribute('data-read', 'true');
            } else {
                el.classList.add('unread-style');
                el.setAttribute('data-read', 'false');
            }
            syncBadgeCount(); // Cập nhật số trên chuông ngay lập tức
        }
    });
}

function deleteNoti(event, notiId) {
    event.stopPropagation(); // Không đóng menu khi hiện Swal
    isProcessingSwal = true; // Bật cờ chặn đóng menu

    Swal.fire({
        title: 'Xóa thông báo?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        confirmButtonText: 'Xóa'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/notifications/delete/' + notiId + '/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCSRFToken() }
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    const el = document.getElementById('noti-' + notiId);
                    $(el).fadeOut(200, function() {
                        $(this).remove();
                        syncBadgeCount(); // Cập nhật lại số đếm
                        if (document.querySelectorAll('.noti-item').length === 0) {
                            document.getElementById('global-noti-list').innerHTML = '<div class="p-4 text-center text-muted">Trống</div>';
                        }
                    });
                }
            });
        }
    });
}

// --- 3. Lọc & Đồng bộ hàng loạt ---

function handleFilterClick(event, mode) {
    // 1. Ngăn dropdown bị đóng
    event.stopPropagation();

    // 2. Xử lý hiệu ứng giao diện (Toggle class Active)
    const container = event.currentTarget.parentElement;
    // Tìm tất cả các nút con và xóa class active
    const buttons = container.querySelectorAll('.btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Thêm class active vào nút vừa được click
    event.currentTarget.classList.add('active');

    // 3. Thực hiện lọc dữ liệu
    const items = document.querySelectorAll('.noti-item');
    items.forEach(item => {
        if (mode === 'unread') {
            // Hiện nếu chưa đọc, ẩn nếu đã đọc
            item.getAttribute('data-read') === 'false' ? $(item).show() : $(item).hide();
        } else {
            // Hiện tất cả
            $(item).show();
        }
    });
}

function markAllRead(event) {
    if(event) event.stopPropagation();
    fetch('/notifications/mark-all-read/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCSRFToken() }
    }).then(res => res.json()).then(data => {
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
    if(event) event.stopPropagation();
    isProcessingSwal = true; // Bật cờ chặn đóng menu
    Swal.fire({
        title: 'Xóa sạch thông báo?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Xóa hết'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/notifications/delete-all/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCSRFToken() }
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    document.getElementById('global-noti-list').innerHTML = '<div class="p-4 text-center text-muted">Trống</div>';
                    syncBadgeCount();
                }
            });
        }
    });
}