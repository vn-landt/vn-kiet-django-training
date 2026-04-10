window.originalFileName = "";
const csrftoken = $('meta[name="csrf-token"]').attr('content');
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
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

            // LƯU TÊN FILE GỐC VÀO BIẾN TOÀN CỤC TẠI ĐÂY
            window.originalFileName = this.files[0].name; // Cập nhật vào window

            // Hiển thị tên file trên giao diện
            fileNameDisplay.innerText = "📄 File: " + file.name;

            const reader = new FileReader();
            reader.onload = function(e) {
                imagePreview.src = e.target.result;
                previewContainer.style.display = 'block';
                previewPlaceholder.style.display = 'none';
                previewContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            };
            reader.readAsDataURL(file);
        }
    });

    // 3. Khi nhấn nút "Bắt đầu trích xuất"
    extractBtn.addEventListener('click', function() {
        if (fileInput.files && fileInput.files[0]) {
            // Khi gọi initEditor, biến originalFileName đã có giá trị tên file gốc
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

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

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
