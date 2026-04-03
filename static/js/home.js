document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('id_file');
    const selectBtn = document.getElementById('selectBtn'); // Nút chọn/đổi ảnh
    const extractBtn = document.getElementById('extractBtn'); // Nút thực hiện trích xuất

    const previewContainer = document.getElementById('previewContainer');
    const previewPlaceholder = document.getElementById('previewPlaceholder');
    const imagePreview = document.getElementById('imagePreview');
    const fileNameDisplay = document.getElementById('fileNameDisplay');

    // 1. Khi nhấn nút "Chọn ảnh", luôn mở trình chọn file
    selectBtn.addEventListener('click', function() {
        fileInput.click();
    });

    // 2. Khi file thay đổi (chọn mới hoặc chọn lại)
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const file = this.files[0];

            // Hiển thị tên file
            fileNameDisplay.innerText = "📄 File: " + file.name;

            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;

                // Hiện khung preview, ẩn placeholder
                previewContainer.style.display = 'block';
                previewPlaceholder.style.display = 'none';

                // Cuộn xuống nhẹ để người dùng thấy ảnh nếu màn hình nhỏ
                previewContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            };
            reader.readAsDataURL(file);
        }
    });

    // 3. Khi nhấn nút "Bắt đầu trích xuất" (nút dưới ảnh)
    extractBtn.addEventListener('click', function() {
        if (fileInput.files && fileInput.files[0]) {
            // Gọi hàm initEditor từ file image_handler.js
            initEditor(fileInput);
        } else {
            Swal.fire('Thông báo', 'Vui lòng chọn ảnh trước!', 'info');
        }
    });
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
                fetch(`/delete/${resultId}/`, {
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

/**
 * Hàm gọi khi hoàn tất Crop ảnh (giữ nguyên logic cũ của bạn)
 */
function onImageCropped(blob, languagesStr) {
    const formData = new FormData();
    formData.append('file', blob, "processed_image.jpg");
    formData.append('save_db', 'true');

    // Gắn chuỗi ngôn ngữ vào form data
    formData.append('languages', languagesStr || 'all')

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

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
        if (data.status === 'success') {
            window.location.href = "/result/" + data.result_id + "/";
        } else {
            Swal.fire('Lỗi AI', data.message, 'error');
        }
    })
    .catch(error => {
        Swal.close();
        Swal.fire('Lỗi', 'Không thể kết nối máy chủ.', 'error');
    });
}