// Hàm lấy CSRF Token từ Cookie
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

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$(document).ready(function() {

    // === LOGIC LỌC HÌNH ẢNH (MỚI) ===
    $('.spreadsheet-filter-item, .spreadsheet-filter').on('click', function(e) {
        // Nếu click vào thẻ <a> hoặc nút action thì không kích hoạt lọc ảnh ở đây
        if ($(e.target).closest('.spreadsheet-title-link, .spreadsheet-actions').length) {
            return;
        }

        const id = $(this).data('id');
        $('.spreadsheet-filter-item, .spreadsheet-filter').removeClass('active');
        $(this).addClass('active');

        if (id === 'all') {
            $('#gallery-header').text('Tất cả hình ảnh');
            $('.gallery-card').fadeIn(200);
        } else {
            const title = $(this).find('.title-text').text();
            $('#gallery-header').text('Ảnh từ: ' + title);
            $('.gallery-card').hide();
            $(`.gallery-card[data-spreadsheet-id="${id}"]`).fadeIn(200);
        }
    });

    // --- 2. SẮP XẾP SIDEBAR (Bảng tính) ---
    $('.btn-sort-sidebar').on('click', function() {
        const type = $(this).data('sort'); // 'updated', 'created', hoặc 'old'
        const $list = $('#sidebar-list');
        const items = $list.children('.spreadsheet-filter-item').get();

        items.sort(function(a, b) {
            let valA, valB;

            if (type === 'updated') {
                // Sắp xếp theo ngày cập nhật (Giảm dần)
                valA = parseInt($(a).attr('data-updated')) || 0;
                valB = parseInt($(b).attr('data-updated')) || 0;
                return valB - valA;
            } else if (type === 'created') {
                // Sắp xếp theo ngày tạo (Giảm dần)
                valA = parseInt($(a).attr('data-created')) || 0;
                valB = parseInt($(b).attr('data-created')) || 0;
                return valB - valA;
            } else {
                // Cũ nhất: Sắp xếp theo ngày tạo (Tăng dần)
                valA = parseInt($(a).attr('data-created')) || 0;
                valB = parseInt($(b).attr('data-created')) || 0;
                return valA - valB;
            }
        });

        // Cập nhật lại giao diện
        $.each(items, function(i, li) {
            $list.append(li);
        });

        // Đổi màu nút trạng thái Active
        $('.btn-sort-sidebar').removeClass('btn-secondary text-white').addClass('btn-outline-secondary');
        $(this).removeClass('btn-outline-secondary').addClass('btn-secondary text-white');
    });

    // --- 3. SẮP XẾP GALLERY (Ảnh 80%) ---
    $('.btn-sort-gallery').on('click', function() {
        const type = $(this).data('sort');
        const $gallery = $('#image-gallery');
        const items = $gallery.children('.gallery-card').get();

        items.sort(function(a, b) {
            const tsA = parseInt($(a).data('timestamp'));
            const tsB = parseInt($(b).data('timestamp'));
            return type === 'new' ? tsB - tsA : tsA - tsB;
        });

        $.each(items, function(i, card) { $gallery.append(card); });
        $('.btn-sort-gallery').removeClass('btn-primary').addClass('btn-outline-primary');
        $(this).removeClass('btn-outline-primary').addClass('btn-primary');
    });

    // --- 4. CHỈNH SỬA TIÊU ĐỀ (Edit Title) ---
    $('.btn-edit-title').on('click', function(e) {
        e.stopPropagation();
        const id = $(this).data('id');
        const oldTitle = $(this).data('title');

        Swal.fire({
            title: 'Đổi tên bảng tính',
            input: 'text',
            inputValue: oldTitle,
            showCancelButton: true,
            confirmButtonText: 'Lưu thay đổi',
            cancelButtonText: 'Hủy'
        }).then((result) => {
            if (result.isConfirmed && result.value) {
                // Gọi AJAX cập nhật title ở đây
                $.post(`/api/update-title/${id}/`, { title: result.value }, function(res) {
                    location.reload(); // Hoặc cập nhật DOM tại chỗ
                });
            }
        });
    });

    // === TRÌNH XEM ẢNH ZOMM ===
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

    overlay.on('click', function(e) {
        if (e.target.id === 'pv-overlay' || e.target.id === 'pv-container') {
            overlay.fadeOut(200);
        }
    });

    overlay.on('wheel', function(e) {
        e.preventDefault();
        const delta = e.originalEvent.deltaY;
        if (delta > 0) {
            if (scale > 0.5) scale -= 0.1;
        } else {
            if (scale < 5) scale += 0.1;
        }
        $('#pv-container').css('transform', `scale(${scale})`);
    });

    $('#pv-img').on('click', function(e) { e.stopPropagation(); });


    // --- 1. XEM CHI TIẾT ẢNH ---
    $('.tool-img-info').on('click', function(e) {
        e.stopPropagation();
        const container = $(this).closest('.gallery-card');
        const d = container.data();
        // Chuyển đổi size sang KB/MB cho dễ đọc
        const sizeFormatted = d.size > 1024 * 1024
            ? (d.size / (1024 * 1024)).toFixed(2) + ' MB'
            : (d.size / 1024).toFixed(2) + ' KB';

        Swal.fire({
            title: '<i class="fas fa-image text-primary"></i> Chi tiết hình ảnh',
            html: `
                <div class="text-left border-top pt-3" style="font-size: 14px;">
                    <p class="mb-2"><strong>Tên file:</strong> ${d.filename}</p>
                    <p class="mb-2"><strong>Định dạng:</strong> ${d.mimeType || 'Không xác định'}</p>
                    <p class="mb-2"><strong>Dung lượng:</strong> ${sizeFormatted}</p>
                    <p class="mb-2"><strong>Ngày tải lên:</strong> ${d.uploaded}</p>
                    <p class="mb-3 text-truncate"><strong>URL:</strong> <a href="${d.url}" target="_blank">${d.url}</a></p>
                    <div class="text-center">
                        <img src="${d.url}" style="max-width: 100%; max-height: 200px; border-radius: 8px; border: 1px solid #ddd;">
                    </div>
                </div>
            `,
            showCancelButton: false,
            confirmButtonText: 'Đóng',
            confirmButtonColor: '#6c757d'
        });
    });

    let selectedImageIds = new Set();

    // --- 2. CHỌN ẢNH (SINGLE & BULK) ---
    // --- 2. CHỌN ẢNH (ĐÃ FIX LOGIC) ---
    $('.tool-img-select').on('click', function(e) {
        e.stopPropagation();

        // SỬA: Lấy từ gallery-card để có ID chuẩn
        const card = $(this).closest('.gallery-card');
        const imgId = card.data('img-id');
        const icon = $(this).find('.icon-check-img');

        // KIỂM TRA LOGIC: Nếu imgId bị undefined, báo lỗi ngay để debug
        if (imgId === undefined) {
            console.error("Lỗi: Không tìm thấy data-img-id trên .gallery-card");
            return;
        }

        if (selectedImageIds.has(imgId)) {
            selectedImageIds.delete(imgId);
            card.removeClass('is-selected');
            icon.removeClass('fa-check-square text-primary').addClass('fa-square');
        } else {
            selectedImageIds.add(imgId);
            card.addClass('is-selected');
            icon.removeClass('fa-square').addClass('fa-check-square text-primary');
        }

        updateImageBulkBar();
    });

    function updateImageBulkBar() {
        const count = selectedImageIds.size;
        const $bar = $('#bulk-actions-bar');

        if (count > 0) {
            $('#selected-count').text(count);
            $bar.addClass('show'); // Dùng class show thay vì d-none
        } else {
            $bar.removeClass('show');
        }
    }

    // Hủy chọn
    $('#btn-cancel-select').on('click', function() {
        selectedImageIds.clear();
        $('.gallery-card').removeClass('is-selected');
        $('.icon-check-img').removeClass('fa-check-square text-primary').addClass('fa-square');
        updateImageBulkBar();
    });

    // --- 3. XÓA ẢNH (ĐƠN LẺ) ---
    $('.tool-img-delete').on('click', function(e) {
        e.stopPropagation();
        const card = $(this).closest('.gallery-card');
        const imgId = card.data('img-id');

        Swal.fire({
            title: 'Xóa ảnh này?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Xóa'
        }).then((result) => {
            if (result.isConfirmed) {
                $.post(`/api/delete-image/${imgId}/`, function() {
                    card.fadeOut(300, function() { $(this).remove(); });
                    selectedImageIds.delete(imgId);
                    updateImageBulkBar();
                });
            }
        });
    });

    // --- 4. XÓA ẢNH HÀNG LOẠT ---
    $('#btn-bulk-delete').on('click', function() {
        const idsArray = Array.from(selectedImageIds);

        Swal.fire({
            title: `Xóa ${idsArray.length} ảnh đã chọn?`,
            text: "Hành động này không thể hoàn tác!",
            icon: 'danger',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            confirmButtonText: 'Xóa tất cả'
        }).then((result) => {
            if (result.isConfirmed) {
                $.ajax({
                    url: '/api/bulk-delete-images/', // Cập nhật URL API của bạn
                    type: 'POST',
                    data: JSON.stringify({ ids: idsArray }),
                    contentType: 'application/json',
                    success: function() {
                        location.reload();
                    },
                    error: function() {
                        Swal.fire('Lỗi!', 'Có lỗi xảy ra khi xóa hàng loạt.', 'error');
                    }
                });
            }
        });
    });

    // --- 5. XÓA BẢNG TÍNH ---
    $('.btn-delete-res').on('click', function(e) {
        e.stopPropagation();
        const id = $(this).data('id');

        Swal.fire({
            title: 'Xóa bảng tính này?',
            text: "Dữ liệu bảng và liên kết ảnh sẽ mất, nhưng ảnh gốc vẫn còn trong kho.",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            confirmButtonText: 'Xóa ngay'
        }).then((result) => {
            if (result.isConfirmed) {
                // Gọi AJAX xóa
                $.post(`/api/delete-result/${id}/`, function() {
                    $(`.spreadsheet-filter-item[data-id="${id}"]`).remove();
                    $(`.gallery-card[data-spreadsheet-id="${id}"]`).remove();
                    Swal.fire('Đã xóa!', '', 'success');
                });
            }
        });
    });

    // === XEM THÔNG TIN LẺ ===
    $('.tool-edit').on('click', function(e) {
        e.stopPropagation();
        const d = $(this).closest('.list-item').data();

        Swal.fire({
            title: '<i class="fas fa-file-alt"></i> Chi tiết tài liệu',
            html: `
                <div class="text-left border-top pt-3">
                    <p class="mb-2"><strong><i class="fas fa-tag"></i> Tên ảnh/Bảng:</strong> ${d.filename}</p>
                    <p class="mb-2"><strong><i class="fas fa-fingerprint"></i> ID Bảng:</strong> #${d.id}</p>
                    <p class="mb-2"><strong><i class="far fa-calendar-plus"></i> Ngày tạo:</strong> ${d.created}</p>
                    <p class="mb-3"><strong><i class="fas fa-history"></i> Cập nhật:</strong> ${d.updated}</p>
                    
                    <div class="d-flex flex-column gap-2 mt-3">
                        <a href="${d.spreadsheetUrl}" class="btn btn-outline-success btn-block mb-2">
                            <i class="fas fa-table"></i> Đi tới trang bảng tính
                        </a>
                    </div>
                </div>
            `,
            showCancelButton: true,
            cancelButtonText: 'Đóng',
            showConfirmButton: false
        });
    });

    // === TẠO BẢNG TRỐNG ===
    $('#btn-create-blank').on('click', function() {
        Swal.fire({
            title: 'Đặt tên bảng tính',
            input: 'text',
            inputPlaceholder: 'Ví dụ: Báo cáo tháng 4',
            showCancelButton: true,
            confirmButtonText: 'Tạo ngay',
            cancelButtonText: 'Hủy',
            inputValidator: (value) => {
                if (!value) return 'Bạn cần nhập tên bảng tính!';
            }
        }).then((result) => {
            if (result.isConfirmed && result.value) {
                Swal.fire({
                    title: 'Đang khởi tạo...',
                    allowOutsideClick: false,
                    didOpen: () => { Swal.showLoading(); }
                });

                $.ajax({
                    url: '/documents/create-blank/',
                    type: 'POST',
                    data: { 'name': result.value },
                    success: function(response) {
                        if (response.status === 'success') {
                            window.location.href = response.redirect_url;
                        } else {
                            Swal.fire('Lỗi!', response.message || 'Không thể tạo bảng tính.', 'error');
                        }
                    },
                    error: function(xhr) {
                        Swal.fire('Lỗi kết nối!', 'Vui lòng kiểm tra lại.', 'error');
                    }
                });
            }
        });
    });

});