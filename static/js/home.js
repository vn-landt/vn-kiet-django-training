// Biến toàn cục để quản lý trạng thái
window.extractMode = 'single';
window.batchFiles = [];
window.originalFileName = "";
const csrftoken = $('meta[name="csrf-token"]').attr('content');
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// Thêm đoạn này vào cuối file home.js hoặc bên trong DOMContentLoaded
document.addEventListener('click', function(e) {
    // Kiểm tra nếu click vào nút xóa hoặc icon bên trong nút xóa
    const deleteBtn = e.target.closest('.delete-history-btn');

    if (deleteBtn) {
        const resultId = deleteBtn.getAttribute('data-id');
        const historyItem = document.getElementById(`item-${resultId}`);
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        Swal.fire({
            title: 'Xác nhận xóa?',
            text: "Dữ liệu và file ảnh liên quan sẽ bị xóa vĩnh viễn!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Vâng, xóa nó!',
            cancelButtonText: 'Hủy'
        }).then((result) => {
            if (result.isConfirmed) {
                // Hiển thị trạng thái đang xóa
                deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                deleteBtn.disabled = true;

                // Gửi request xóa tới server
                // Lưu ý: URL '/delete/ID/' phải khớp với urls.py của bạn
                fetch(`/home/delete/${resultId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    if (response.ok || response.redirected) {
                        // Hiệu ứng ẩn dòng bị xóa
                        $(historyItem).fadeOut(400, function() {
                            $(this).remove();

                            // Nếu không còn item nào, hiện thông báo trống
                            if (document.querySelectorAll('.history-item').length === 0) {
                                document.querySelector('.history-list').innerHTML = '<p class="text-muted text-center py-3">Chưa có dữ liệu.</p>';
                            }
                        });

                        Swal.fire({
                            title: 'Đã xóa!',
                            text: 'Bản ghi của bạn đã được dọn dẹp.',
                            icon: 'success',
                            timer: 1500,
                            showConfirmButton: false
                        });
                    } else {
                        throw new Error('Lỗi phản hồi từ server');
                    }
                })
                .catch(error => {
                    console.error(error);
                    deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
                    deleteBtn.disabled = false;
                    Swal.fire('Thất bại', 'Không thể xóa bản ghi lúc này. Vui lòng thử lại.', 'error');
                });
            }
        });
    }
});


$(document).ready(function() {
    // === TẠO BẢNG TRỐNG ===
    $('#btn-create-blank').on('click', function () {
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
                    didOpen: () => {
                        Swal.showLoading();
                    }
                });

                $.ajax({
                    url: '/create-spreadsheet-blank/',
                    type: 'POST',
                    data: {'name': result.value},
                    success: function (response) {
                        if (response.status === 'success') {
                            window.location.href = response.redirect_url;
                        } else {
                            Swal.fire('Lỗi!', response.message || 'Không thể tạo bảng tính.', 'error');
                        }
                    },
                    error: function (xhr) {
                        Swal.fire('Lỗi kết nối!', 'Vui lòng kiểm tra lại.', 'error');
                    }
                });
            }
        });
    });
});

/**
 * Hàm gọi khi hoàn tất Crop ảnh từ Trang chủ (Tạo bảng mới)
 * Đã cập nhật logic kiểm tra hạn mức 50 ảnh.
 */
function onImageCropped(blob, languagesStr, originalFileName, deleteDuration) {
    const formData = new FormData();
    formData.append('file', blob, "processed_image.jpg");

    // Đảm bảo tên file không bị rỗng nếu có sự cố
    const finalName = originalFileName || "image_" + Date.now() + ".jpg";
    formData.append('original_filename', finalName);    formData.append('save_db', 'true'); // Yêu cầu backend tạo mới ExtractedResult và lưu UploadedFile

    formData.append('mime_type', blob.type);
    // Gắn chuỗi ngôn ngữ vào form data
    formData.append('languages', languagesStr || 'all');

    formData.append('deleteDuration', deleteDuration);

    const csrftoken = $('meta[name="csrf-token"]').attr('content')
                   || (document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : "");

    // Hiển thị trạng thái đang xử lý
    Swal.fire({
        title: 'Đang xử lý...',
        text: 'AI đang phân tích bảng biểu...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    fetch('/extract-only-api/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': csrftoken }
    })
    .then(response => response.json())
    .then(data => {
        Swal.close();

        // 1. Xử lý khi thành công
        if (data.status === 'success') {
            window.location.href = "/result/" + data.result_id + "/";
        }

        // 2. Xử lý khi kho lưu trữ 50 ảnh đã đầy
        else if (data.status === 'limit_exceeded') {
            Swal.fire({
                title: 'Kho lưu trữ đầy!',
                text: data.message, // Thông báo từ backend: "Kho lưu trữ ảnh đã đầy (50/50)..."
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Dọn dẹp ngay',
                cancelButtonText: 'Để sau'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Điều hướng người dùng đến trang quản lý tài liệu để xóa ảnh
                    window.location.href = data.redirect_url;
                }
            });
        }

        // 3. Xử lý các lỗi khác (AI fail, định dạng file...)
        else {
            Swal.fire('Lỗi hệ thống', data.message, 'error');
        }
    })
    .catch(error => {
        Swal.close();
        Swal.fire('Lỗi kết nối', 'Không thể kết nối máy chủ. Vui lòng thử lại.', 'error');
    });
}
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('id_file');
    const selectBtn = document.getElementById('selectBtn');

    // Sửa lỗi hiện folder 2 lần
    selectBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        fileInput.click();
    });

    fileInput.addEventListener('change', function(e) {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        document.getElementById('previewPlaceholder').style.display = 'none';

        if (window.extractMode === 'single') {
            // Chế độ 1 ảnh: Chỉ lấy ảnh đầu tiên và hiện Preview
            const file = files[0];
            window.originalFileName = file.name;

            const reader = new FileReader();
            reader.onload = function(event) {
                document.getElementById('imagePreview').src = event.target.result;
                document.getElementById('fileNameDisplay').innerText = file.name;
                document.getElementById('singlePreviewArea').style.display = 'block';
                document.getElementById('batchPreviewArea').style.display = 'none';
            };
            reader.readAsDataURL(file);
        } else {
            // Chế độ nhiều ảnh
            for (let i = 0; i < files.length; i++) {
                if (window.batchFiles.length < 10) {
                    window.batchFiles.push({ file: files[i], originalName: files[i].name, isCropped: false });
                }
            }
            renderBatchList();
            document.getElementById('singlePreviewArea').style.display = 'none';
            document.getElementById('batchPreviewArea').style.display = 'block';
        }
        this.value = '';
    });

    // Nút Bắt đầu trích xuất cho 1 ảnh (Mở modal)
    document.getElementById('extractBtn').addEventListener('click', function() {
        // fileInput lúc này đã bị reset value nên ta tạo fake input chứa file đã lưu trong preview
        const imgDisplay = document.getElementById('imagePreview');
        if (imgDisplay.src) {
            // Tái sử dụng hàm mở editor từ image_handler.js
            initEditorFromPreview(imgDisplay.src, window.originalFileName);
        }
    });

    document.getElementById('batchExtractBtn').addEventListener('click', startBatchProcessing);
});

/**
 * Hàm thay đổi chế độ: 1 ảnh <-> Nhiều ảnh
 * Được gọi từ thuộc tính onchange của Radio Button
 */
window.toggleMode = function() {
    const mode = document.querySelector('input[name="extractMode"]:checked').value;
    window.extractMode = mode;

    const config = document.getElementById('globalConfigSection');
    const fileInput = document.getElementById('id_file');

    if (mode === 'batch') {
        config.style.display = 'block'; // Hiện ngôn ngữ/thời gian ngay lập tức
        fileInput.setAttribute('multiple', 'multiple');
    } else {
        config.style.display = 'none'; // Ẩn khi về chế độ 1 ảnh
        fileInput.removeAttribute('multiple');
    }
    // Reset giao diện khi chuyển tab
    document.getElementById('singlePreviewArea').style.display = 'none';
    document.getElementById('batchPreviewArea').style.display = 'none';
    document.getElementById('previewPlaceholder').style.display = 'block';
};

/**
 * Hiển thị danh sách ảnh trong chế độ Batch
 */
window.renderBatchList = function() {
    const container = document.getElementById('batchList');
    const countDisplay = document.getElementById('fileCount');
    if (!container) return;

    container.innerHTML = '';
    countDisplay.innerText = window.batchFiles.length;

    window.batchFiles.forEach((item, index) => {
        const imageUrl = URL.createObjectURL(item.file);
        const html = `
            <div class="col-12 mb-2 p-2 border rounded d-flex align-items-center justify-content-between bg-white shadow-sm">
                <div class="d-flex align-items-center flex-grow-1" style="min-width: 0;">
                    <img src="${imageUrl}" class="rounded mr-3" style="width: 60px; height: 60px; object-fit: cover; border: 1px solid #eee;">
                    <div style="min-width: 0;">
                        <div class="text-truncate font-weight-bold" title="${item.originalName}">${item.originalName}</div>
                        ${item.isCropped ? '<small class="badge badge-success">Đã cắt chỉnh</small>' : '<small class="text-muted">Ảnh gốc</small>'}
                    </div>
                </div>
                <div class="ml-2 d-flex">
                    <button type="button" class="btn btn-sm btn-outline-primary mr-1" onclick="cropBatchItem(${index})" title="Cắt ảnh">
                        <i class="fas fa-crop"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="deleteBatchItem(${index})" title="Xóa">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', html);
    });
};

window.deleteBatchItem = function(index) {
    window.batchFiles.splice(index, 1);
    renderBatchList();
    if (window.batchFiles.length === 0) {
        document.getElementById('batchPreviewArea').style.display = 'none';
        document.getElementById('previewPlaceholder').style.display = 'block';
    }
};

window.cropBatchItem = function(index) {
    window.currentBatchCropIndex = index;
    const item = window.batchFiles[index];
    window.originalFileName = item.originalName;

    // Giả lập input để hàm initEditor (trong image_handler.js) nhận được file
    const fakeInput = { files: [item.file] };
    initEditor(fakeInput);
};

/**
 * Logic gửi hàng loạt về server
 */
async function startBatchProcessing() {
    if (window.batchFiles.length === 0) {
        return Swal.fire('Thông báo', 'Vui lòng chọn ít nhất 1 ảnh!', 'info');
    }

    const languagesStr = Array.from(document.querySelectorAll('input[name="langs"]:checked')).map(cb => cb.value).join(',');
    const deleteDuration = document.getElementById('deleteDuration').value;
    const csrftoken = $('meta[name="csrf-token"]').attr('content')
                   || (document.querySelector('[name=csrfmiddlewaretoken]') ? document.querySelector('[name=csrfmiddlewaretoken]').value : "");

    Swal.fire({
        title: 'Đang xử lý hàng loạt...',
        html: `Tiến độ: <b>0</b> / ${window.batchFiles.length} ảnh`,
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    let firstResultId = null;

    for (let i = 0; i < window.batchFiles.length; i++) {
        const item = window.batchFiles[i];
        Swal.getHtmlContainer().querySelector('b').innerText = (i + 1);

        const formData = new FormData();
        formData.append('file', item.file, "processed_image.jpg");
        formData.append('original_filename', item.originalName);
        formData.append('languages', languagesStr || 'all');
        formData.append('deleteDuration', deleteDuration);

        if (i === 0) {
            formData.append('save_db', 'true'); // Ảnh đầu tiên tạo record mới
        } else {
            formData.append('save_db', 'false'); // Các ảnh sau đính kèm vào record cũ
            formData.append('result_id', firstResultId);
        }

        try {
            const response = await fetch('/extract-only-api/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrftoken }
            });
            const data = await response.json();

            if (data.status === 'success') {
                if (i === 0) firstResultId = data.result_id;
            } else {
                console.error("Lỗi ảnh " + (i+1) + ": " + data.message);
            }
        } catch (err) {
            console.error("Lỗi kết nối ảnh " + (i+1));
        }
    }

    Swal.close();
    if (firstResultId) {
        window.location.href = "/result/" + firstResultId + "/";
    }
}

// Xoá tất cả ảnh
window.clearAllFiles = function() {
    // 1. Reset mảng dữ liệu
    window.batchFiles = [];

    // 2. Cập nhật lại giao diện danh sách (sẽ làm trống list)
    if (typeof renderBatchList === 'function') {
        renderBatchList();
    }

    // 3. Ẩn khu vực Preview và hiện lại Placeholder (Sửa lỗi null tại đây)
    const batchArea = document.getElementById('batchPreviewArea');
    const placeholder = document.getElementById('previewPlaceholder');
    const singleArea = document.getElementById('singlePreviewArea');

    if (batchArea) batchArea.style.display = 'none';
    if (singleArea) singleArea.style.display = 'none';
    if (placeholder) placeholder.style.display = 'block';

    // Reset input file để có thể chọn lại chính những ảnh vừa xóa
    const fileInput = document.getElementById('id_file');
    if (fileInput) fileInput.value = '';
};