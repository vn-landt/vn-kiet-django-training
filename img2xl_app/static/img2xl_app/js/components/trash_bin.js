// -*- coding: utf-8 -*-
/**
 * Logic điều khiển giao diện Thùng rác
 */

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
        confirmButtonText: 'Đồng ý',
        cancelButtonText: 'Hủy'
    }).then((result) => {
        if (result.isConfirmed) {
            executeRestore(type, [id]);
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

    if (ids.length === 0) return;

    Swal.fire({
        title: 'Khôi phục ' + ids.length + ' mục đã chọn?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#28a745',
        confirmButtonText: 'Khôi phục ngay',
        cancelButtonText: 'Hủy'
    }).then((result) => {
        if (result.isConfirmed) {
            executeRestore(type, ids);
        }
    });
}

/**
 * Hàm điều hướng thực thi khôi phục và hiển thị kết quả
 */
function executeRestore(type, ids) {
    // Hiển thị loading
    Swal.fire({
        title: 'Đang xử lý...',
        allowOutsideClick: false,
        onBeforeOpen: () => { Swal.showLoading(); }
    });

    // Gọi tới service
    apiRestoreItems(type, ids)
        .done(function(response) {
            Swal.fire({
                title: 'Thành công!',
                text: response.message,
                icon: 'success'
            }).then(() => {
                location.reload(); // Load lại trang để cập nhật danh sách
            });
        })
        .fail(function(xhr) {
            var errorMsg = "Đã có lỗi xảy ra.";
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMsg = xhr.responseJSON.message;
            }
            Swal.fire('Thất bại', errorMsg, 'error');
        });
}