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

// 2. Cấu hình AJAX Header tự động
var csrftoken = getCookie('csrftoken');

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        // Chỉ gửi token cho các request "không an toàn" (POST, PUT, DELETE)
        // và không gửi cho các request sang domain khác (crossDomain)
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
$(document).ready(function() {
    // 1. Xử lý "Chọn tất cả" cho từng tab riêng biệt
    $('.check-all').on('change', function() {
        var targetType = $(this).data('target');
        var isChecked = $(this).is(':checked');
        $('.item-' + targetType).prop('checked', isChecked);
        updateBatchUI();
    });

    // 2. Cập nhật UI khi chọn từng item lẻ
    $(document).on('change', '.check-item', function() {
        updateBatchUI();
    });

    // 3. Reset checkbox khi chuyển Tab (để tránh khôi phục nhầm loại)
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        $('.check-item, .check-all').prop('checked', false);
        updateBatchUI();
    });
});

/**
 * Cập nhật hiển thị của nút Khôi phục hàng loạt
 */
function updateBatchUI() {
    var selectedItems = $('.check-item:checked');
    var count = selectedItems.length;

    if (count > 0) {
        $('#btn-restore-batch').fadeIn();
        $('#selected-count').text(count);
    } else {
        $('#btn-restore-batch').fadeOut();
    }
}

/**
 * Khôi phục 1 mục duy nhất
 */
function restoreSingle(type, id) {
    Swal.fire({
        title: 'Xác nhận khôi phục?',
        text: type === 'table' ? "Bảng và các ảnh liên quan sẽ quay lại danh sách chính." : "Ảnh sẽ được khôi phục.",
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        confirmButtonText: 'Đồng ý'
    }).then((result) => {
        if (result.isConfirmed) {
            sendRestoreRequest(type, [id]);
        }
    });
}

/**
 * Khôi phục nhiều mục đã chọn thông qua checkbox
 */
function handleBatchRestore() {
    var activeTab = $('.nav-tabs .nav-link.active').attr('href'); // #tables hoặc #images
    var type = activeTab === '#tables' ? 'table' : 'image';

    var ids = [];
    $('.item-' + type + ':checked').each(function() {
        ids.push($(this).val());
    });

    Swal.fire({
        title: 'Khôi phục ' + ids.length + ' mục đã chọn?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        confirmButtonText: 'Khôi phục ngay'
    }).then((result) => {
        if (result.isConfirmed) {
            sendRestoreRequest(type, ids);
        }
    });
}

/**
 * Hàm gửi AJAX chung đến restore_item_api
 */
function sendRestoreRequest(type, ids) {
    // Hiển thị loading
    Swal.fire({
        title: 'Đang xử lý...',
        allowOutsideClick: false,
        onBeforeOpen: () => { Swal.showLoading(); }
    });

    $.ajax({
        url: "/trash-bin/api/restore/", // Khớp với name='restore_item_api'
        method: 'POST',
        data: {
            'type': type,
            'ids[]': ids,
        },
        success: function(response) {
            Swal.fire({
                title: 'Thành công!',
                text: response.message,
                icon: 'success'
            }).then(() => {
                location.reload(); // Load lại trang để cập nhật danh sách
            });
        },
        error: function(xhr) {
            var errorMsg = "Đã có lỗi xảy ra.";
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMsg = xhr.responseJSON.message;
            }
            Swal.fire('Thất bại', errorMsg, 'error');
        }
    });
}