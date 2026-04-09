function markRead(notiId) {
    fetch('/notifications/mark-read/' + notiId + '/', {
        method: 'POST',
        headers: { 'X-CSRFToken': '{{ csrf_token }}' }
    }).then(res => res.json()).then(data => {
        if (data.success) {
            const el = document.getElementById('noti-' + notiId);
            el.classList.remove('bg-light-blue'); // Bỏ màu nền xanh đánh dấu chưa đọc
            // Cập nhật số đếm badge nếu cần (có thể reload nhẹ hoặc trừ số đi)
        }
    });
}

function deleteNoti(notiId) {
    Swal.fire({
        title: 'Xóa thông báo?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Xóa',
        cancelButtonText: 'Hủy'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch('/notifications/delete/' + notiId + '/', {
                method: 'POST',
                headers: { 'X-CSRFToken': '{{ csrf_token }}' }
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    document.getElementById('noti-' + notiId).remove();
                    // Nếu hết thông báo thì hiện text "Trống"
                }
            });
        }
    });
}