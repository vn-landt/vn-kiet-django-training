// 1. Lấy CSRF Token từ Meta Tag (Chắc chắn hơn lấy từ Cookie)
const csrftoken = $('meta[name="csrf-token"]').attr('content');

// 2. Cấu hình tất cả AJAX tự động gửi Token này đi
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$(document).ready(function() {

    // === LOGIC LỌC HÌNH ẢNH (MỚI) ===
    $('.spreadsheet-filter-item, .spreadsheet-filter').on('click', function(e) {
        const id = $(this).data('id').toString(); // Chuyển về string để an toàn

        $('.spreadsheet-filter-item, .spreadsheet-filter').removeClass('active');
        $(this).addClass('active');

        if (id === 'all') {
            $('#gallery-header').text('Tất cả hình ảnh');
            $('.gallery-card').fadeIn(200);
        } else {
            const title = $(this).find('.title-text').text();
            $('#gallery-header').text('Ảnh từ: ' + title);

            $('.gallery-card').hide();

            // Lọc các card có chứa ID này trong danh sách IDs
            // Selector [attr~="value"] tìm chính xác "id" trong chuỗi cách nhau bởi dấu cách
            $(`.gallery-card[data-spreadsheet-ids~="${id}"]`).fadeIn(200);
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
                $.post(`/documents/update-title/${id}/`, { title: result.value }, function(res) {
                    Swal.fire('Đổi tên thành công!', '', 'success').then(() => {
                        location.reload();
                    });
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

    // XEM VÀ SỬA THÔNG TIN ẢNH
    $('.tool-img-info').on('click', function(e) {
        e.stopPropagation();
        const container = $(this).closest('.gallery-card');
        const d = container.data(); // d.id, d.filename, d.deleteAt, d.uploaded, d.size, d.url...

        const sizeFormatted = d.size > 1024 * 1024
            ? (d.size / (1024 * 1024)).toFixed(2) + ' MB'
            : (d.size / 1024).toFixed(2) + ' KB';

        // Tính toán hiển thị thời gian xóa hiện tại
        let deleteText = d.deleteAt && d.deleteAt !== 'None' ? d.deleteAt : 'Không tự động xóa';

        Swal.fire({
            title: '<i class="fas fa-edit text-primary"></i> Quản lý hình ảnh',
            html: `
                <div class="text-left border-top pt-3" style="font-size: 14px;">
                    <div class="form-group mb-2">
                        <label class="font-weight-bold">Tên file (Có thể sửa):</label>
                        <input type="text" id="swal-filename" class="form-control form-control-sm" value="${d.filename}">
                    </div>
                    
                    <p class="mb-2"><strong>Dung lượng:</strong> ${sizeFormatted} | <strong>Ngày tải:</strong> ${d.uploaded}</p>
                    
                    <div class="form-group mb-3 p-2 bg-light rounded border">
                        <label class="font-weight-bold text-danger"><i class="fas fa-clock"></i> Tự động xóa:</label>
                        <div class="small mb-1">Hiện tại: <span class="badge badge-warning">${deleteText}</span></div>
                        <select id="swal-duration" class="form-control form-control-sm">
                            <option value="keep">Giữ nguyên hiện tại</option>
                            <option value="0">Không tự động xoá</option>
                            <option value="30">Sau 30 phút (Tính từ lúc này)</option>
                            <option value="60">Sau 1 giờ (Tính từ lúc này)</option>
                            <option value="1440">Sau 1 ngày (Tính từ lúc này)</option>
                        </select>
                    </div>
    
                    <div class="text-center">
                        <img src="${d.url}" style="max-width: 100%; max-height: 150px; border-radius: 8px; border: 1px solid #ddd;">
                    </div>
                </div>
            `,
            showCancelButton: true,
            confirmButtonText: '<i class="fas fa-save"></i> Lưu thay đổi',
            cancelButtonText: 'Đóng',
            confirmButtonColor: '#28a745',
            cancelButtonColor: '#6c757d',
            reverseButtons: true, // Đưa nút Lưu sang bên trái nút Đóng
            focusConfirm: false,
            preConfirm: () => {
                const newFilename = document.getElementById('swal-filename').value;
                const newDuration = document.getElementById('swal-duration').value;

                if (!newFilename) {
                    Swal.showValidationMessage('Tên file không được để trống');
                    return false;
                }

                // Lấy ID chính xác từ thuộc tính data-img-id
                const imgId = container.data('img-id');

                if (!imgId) {
                    Swal.showValidationMessage('Lỗi hệ thống: Không tìm thấy ID ảnh!');
                    return false;
                }

                // Trả về dữ liệu để thực hiện AJAX
                return {
                    id: imgId,
                    filename: newFilename,
                    duration: newDuration
                };
            }
        }).then((result) => {
            if (result.isConfirmed) {
                // Thực hiện gọi AJAX để update vào DB
                updateImageMetadata(result.value);
            }
        });
    });

    let selectedImageIds = new Set();

    // --- 2. CHỌN ẢNH (SINGLE & BULK) ---
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
                $.post(`/documents/delete-image/${imgId}/`, function() {
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
                    url: '/documents/bulk-delete-images/', // Cập nhật URL API của bạn
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
                $.post(`/documents/delete-result/${id}/`, function() {
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

    // sửa thời gian xoá ảnh hàng loạt
    $('#btn-bulk-edit-time').on('click', function() {
        // 1. Lấy danh sách ID đã chọn (giả sử bạn lưu trong mảng idsArray)
        const idsArray = Array.from(selectedImageIds);

        if (idsArray.length === 0) return;

        Swal.fire({
            title: `<i class="fas fa-history text-warning"></i> Cập nhật ${idsArray.length} ảnh`,
            html: `
                <p class="small text-muted">Chọn thời gian tự động xóa mới cho các mục đã chọn (tính từ thời điểm này):</p>
                <select id="bulk-duration" class="form-control custom-select">
                    <option value="0">Không tự động xoá</option>
                    <option value="30">Sau 30 phút</option>
                    <option value="60">Sau 1 giờ</option>
                    <option value="1440">Sau 1 ngày</option>
                    <option value="10080">Sau 1 tuần</option>
                </select>
            `,
            showCancelButton: true,
            confirmButtonColor: '#ffc107',
            confirmButtonText: 'Cập nhật ngay',
            cancelButtonText: 'Hủy bỏ',
            preConfirm: () => {
                return document.getElementById('bulk-duration').value;
            }
        }).then((result) => {
            if (result.isConfirmed) {
                const newDuration = result.value;

                // 2. Gọi AJAX gửi lên Server
                $.ajax({
                    url: '/documents/bulk-update-time/', // URL bạn sẽ tạo ở bước 3
                    method: 'POST',
                    data: {
                        'ids[]': idsArray,
                        'duration': newDuration,
                    },
                    success: function(response) {
                        Swal.fire('Thành công!', `Đã cập nhật thời gian xóa cho ${idsArray.length} ảnh.`, 'success')
                        .then(() => location.reload());
                    },
                    error: function() {
                        Swal.fire('Lỗi!', 'Không thể cập nhật hàng loạt.', 'error');
                    }
                });
            }
        });
    });
});

// Hàm gọi API cập nhật
function updateImageMetadata(data) {
    $.ajax({
        url: '/documents/update-image-info/',
        method: 'POST',
        // Lưu ý: Đã có ajaxSetup ở trên nên không cần headers ở đây nữa
        data: {
            'id': data.id,
            'filename': data.filename,
            'duration': data.duration
            // TUYỆT ĐỐI KHÔNG để 'csrfmiddlewaretoken': '{{ csrf_token }}' ở đây
        },
        success: function(response) {
            Swal.fire('Thành công!', 'Thông tin ảnh đã được cập nhật.', 'success').then(() => {
                location.reload();
            });
        },
        error: function(xhr) {
            console.error("Lỗi cập nhật thông tin ảnh:", xhr.responseText);
            Swal.fire('Lỗi!', 'Không thể cập nhật thông tin (403 Forbidden).', 'error');
        }
    });
}