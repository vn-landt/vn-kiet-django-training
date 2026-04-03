// Hàm lấy CSRF Token từ Cookie (Dùng cho Django)
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

// Cấu hình Ajax luôn gửi kèm CSRF Token
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$(document).ready(function() {

    // 2. Xử lý nút Like (Toggle)
    $('.list-item-like').on('click', function() {
        var icon = $(this).find('span');
        if (icon.hasClass('far')) {
            icon.removeClass('far fa-heart').addClass('fas fa-heart btn-liked');
        } else {
            icon.removeClass('fas fa-heart btn-liked').addClass('far fa-heart');
        }
    });

    // 3. Thanh tìm kiếm nhanh (Client-side)
    $("#imageSearch").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $(".pad-content-listing .col-xl-2").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });

    // 4. Các nút Edit/Share/Codes (Để trống URL như yêu cầu)
    $('.tool-edit, .list-item-share, .tool-codes').on('click', function(e) {
        // e.preventDefault(); // Uncomment nếu không muốn chuyển trang khi URL trống
        console.log("Action triggered for ID:", $(this).closest('.list-item').data('id'));
    });
});

$(document).ready(function() {
    let selectedIds = [];

    // 1. TRÌNH XEM ẢNH: ZOOM + SCROLL + CLICK OUTSIDE
    let scale = 1;
    const overlay = $(`
        <div id="pv-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); z-index:9999; cursor:zoom-out; align-items:center; justify-content:center;">
            <div id="pv-container" style="transition: transform 0.1s ease; cursor:default;">
                <img id="pv-img" src="" style="max-width:90vw; max-height:90vh; border-radius:4px; box-shadow:0 0 20px rgba(0,0,0,0.5);">
            </div>
            <div style="position:fixed; bottom:20px; left:50%; transform:translateX(-50%); color:white; background:rgba(0,0,0,0.5); padding:5px 15px; border-radius:20px; pointer-events:none; font-size:12px;">
                Cuộn chuột để Phóng to/Thu nhỏ | Click ra ngoài để đóng
            </div>
        </div>
    `).appendTo('body');

    $('.preview-trigger').on('click', function(e) {
        e.stopPropagation();
        const src = $(this).attr('src');
        scale = 1;
        $('#pv-img').attr('src', src);
        $('#pv-container').css('transform', `scale(${scale})`);
        overlay.css('display', 'flex').hide().fadeIn(200);
    });

    // Đóng khi ấn ra ngoài (vùng overlay)
    overlay.on('click', function(e) {
        if (e.target.id === 'pv-overlay' || e.target.id === 'pv-container') {
            overlay.fadeOut(200);
        }
    });

    // Phóng to/thu nhỏ bằng con lăn chuột
    overlay.on('wheel', function(e) {
        e.preventDefault();
        const delta = e.originalEvent.deltaY;
        if (delta > 0) {
            if (scale > 0.5) scale -= 0.1; // Thu nhỏ
        } else {
            if (scale < 5) scale += 0.1; // Phóng to
        }
        $('#pv-container').css('transform', `scale(${scale})`);
    });

    // Ngăn chặn sự kiện click vào ảnh gây đóng overlay
    $('#pv-img').on('click', function(e) {
        e.stopPropagation();
    });

    // 2. Chọn hàng loạt (Toggle Selection)
    $('.tool-select').on('click', function(e) {
        e.stopPropagation();
        const item = $(this).closest('.list-item');
        const id = item.data('id');
        const icon = $(this).find('span');

        item.toggleClass('is-selected');

        if (item.hasClass('is-selected')) {
            selectedIds.push(id);
            icon.removeClass('fa-square').addClass('fa-check-square');
        } else {
            selectedIds = selectedIds.filter(i => i !== id);
            icon.removeClass('fa-check-square').addClass('fa-square');
        }
        updateBulkBar();
    });

    function updateBulkBar() {
        if (selectedIds.length > 0) {
            $('#bulk-actions-bar').removeClass('d-none');
            $('#selected-count').text(selectedIds.length);
        } else {
            $('#bulk-actions-bar').addClass('d-none');
        }
    }

    // 3. Xóa đơn lẻ với SweetAlert2
    $('.tool-delete').on('click', function() {
        const item = $(this).closest('.list-item');
        const id = item.data('id');

        Swal.fire({
            title: 'Bạn có chắc chắn?',
            text: "Dữ liệu này sẽ không thể khôi phục!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Vâng, xóa nó!'
        }).then((result) => {
            if (result.isConfirmed) {
                // Giả lập gọi API xóa (Bạn thay bằng AJAX tới view bulk_delete_api)
                $.post('/api/bulk-delete/', JSON.stringify({ids: [id]}), function() {
                    item.fadeOut();
                    Swal.fire('Đã xóa!', 'Tài liệu đã được gỡ bỏ.', 'success');
                });
            }
        });
    });

    // Xóa hàng loạt
    $('#btn-bulk-delete').on('click', function() {
        Swal.fire({
            title: `Xóa ${selectedIds.length} mục?`,
            icon: 'danger',
            showCancelButton: true,
            confirmButtonText: 'Xóa tất cả'
        }).then((result) => {
            if (result.isConfirmed) {
                // Ajax call tới view bulk_delete_api
                console.log("Xóa list:", selectedIds);
                location.reload(); // Reload để cập nhật UI
            }
        });
    });

    // 4. Copy Link (Share)
    $('.list-item-share').on('click', function() {
        const url = $(this).closest('.list-item').data('url');
        navigator.clipboard.writeText(url).then(() => {
            Swal.fire({
                toast: true,
                position: 'top-end',
                icon: 'success',
                title: 'Đã copy link ảnh!',
                showConfirmButton: false,
                timer: 1500
            });
        });
    });

    // 5. Tool Edit (Hiển thị Form nhỏ)
    $('.tool-edit').on('click', function(e) {
        e.stopPropagation();
        const item = $(this).closest('.list-item');
        const d = item.data(); // Lấy toàn bộ data attributes

        Swal.fire({
            title: '<i class="fas fa-file-alt"></i> Chi tiết tài liệu',
            html: `
                <div class="text-left border-top pt-3">
                    <p class="mb-2"><strong><i class="fas fa-tag"></i> Tên:</strong> ${d.filename}</p>
                    <p class="mb-2"><strong><i class="fas fa-fingerprint"></i> ID:</strong> #${d.id}</p>
                    <p class="mb-2"><strong><i class="far fa-calendar-plus"></i> Ngày tạo:</strong> ${d.created}</p>
                    <p class="mb-3"><strong><i class="fas fa-history"></i> Cập nhật:</strong> ${d.updated}</p>
                    
                    <div class="d-flex flex-column gap-2 mt-3">
                        <a href="${d.url}" target="_blank" class="btn btn-outline-info btn-block mb-2">
                            <i class="fas fa-external-link-alt"></i> Go to image online
                        </a>
                        <a href="${d.spreadsheetUrl}" class="btn btn-outline-success btn-block mb-2">
                            <i class="fas fa-table"></i> Go to spreadsheet
                        </a>
                    </div>
                </div>
            `,
            showCancelButton: true,
            cancelButtonText: 'Đóng',
            confirmButtonColor: '#007bff',
            focusConfirm: false
        }).then((result) => {

        });
    });

    // 6. Tạo bảng tính trống (Bản hoàn chỉnh)
    $('#btn-create-blank').on('click', function() {
        Swal.fire({
            title: 'Đặt tên bảng tính',
            input: 'text',
            inputPlaceholder: 'Ví dụ: Báo cáo tháng 4',
            showCancelButton: true,
            confirmButtonText: 'Tạo ngay',
            cancelButtonText: 'Hủy',
            inputValidator: (value) => {
                if (!value) {
                    return 'Bạn cần nhập tên bảng tính!';
                }
            }
        }).then((result) => {
            if (result.isConfirmed && result.value) {
                const fileName = result.value;

                // Hiển thị loading trong khi chờ Server xử lý
                Swal.fire({
                    title: 'Đang khởi tạo...',
                    allowOutsideClick: false,
                    didOpen: () => {
                        Swal.showLoading();
                    }
                });

                // Gửi AJAX tới Django
                $.ajax({
                    url: '/documents/create-blank/', // Đảm bảo URL này khớp với urls.py
                    type: 'POST',
                    data: {
                        'name': fileName,
                        'csrfmiddlewaretoken': '{{ csrf_token }}' // Lưu ý xem phần ghi chú bên dưới
                    },
                    success: function(response) {
                        if (response.status === 'success') {
                            Swal.fire({
                                icon: 'success',
                                title: 'Thành công!',
                                text: 'Đang chuyển hướng tới bảng tính...',
                                timer: 1500,
                                showConfirmButton: false
                            }).then(() => {
                                // Chuyển hướng tới trang detail của bản ghi vừa tạo
                                window.location.href = response.redirect_url;
                            });
                        } else {
                            Swal.fire('Lỗi!', response.message || 'Không thể tạo bảng tính.', 'error');
                        }
                    },
                    error: function() {
                        Swal.fire('Lỗi kết nối!', 'Vui lòng kiểm tra lại đường truyền.', 'error');
                    }
                });
            }
        });
    });

    $('#btn-cancel-select').on('click', function() {
        $('.list-item').removeClass('is-selected');
        selectedIds = [];
        updateBulkBar();
    });
});