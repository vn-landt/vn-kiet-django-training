// static/js/image_handler.js
let cropper;

function initEditor(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = document.getElementById('imageToEdit');
            img.src = e.target.result;

            // Hiển thị Modal
            document.getElementById('editorModal').style.display = 'block';

            // Làm mới Cropper nếu đã tồn tại
            if (cropper) {
                cropper.destroy();
            }

            // Khởi tạo Cropper sau khi ảnh đã load
            cropper = new Cropper(img, {
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.8,
                restore: false,
                guides: true,
                center: true,
                highlight: false,
                cropBoxMovable: true,
                cropBoxResizable: true,
                toggleDragModeOnDblclick: false,
            });
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function closeEditor() {
    document.getElementById('editorModal').style.display = 'none';
    // Reset input file để có thể chọn lại chính ảnh đó nếu muốn
    const fileInput = document.getElementById('id_file');
    if (fileInput) fileInput.value = "";

    if (cropper) {
        cropper.destroy();
    }
}

// Khi người dùng nhấn nút "Xác nhận & Trích xuất" trong Modal
function processAndExtract() {
    if (!cropper) return;

    // Lấy canvas đã cắt
    const canvas = cropper.getCroppedCanvas({
        maxWidth: 2048, // Tối ưu cho AI
        maxHeight: 2048
    });

    canvas.toBlob((blob) => {
        // Đóng modal trước
        document.getElementById('editorModal').style.display = 'none';

        // GỌI HÀM CALLBACK: Hàm này phải được định nghĩa trong home.js hoặc result_detail.js
        if (typeof onImageCropped === 'function') {
            onImageCropped(blob);
        } else {
            console.error("Lỗi: Hàm onImageCropped(blob) chưa được định nghĩa!");
        }

        // Dọn dẹp
        cropper.destroy();
        cropper = null;
    }, 'image/jpeg', 0.9);
}