// static/js/image_handler.js
let cropper;
document.addEventListener('DOMContentLoaded', function() {
    // Lấy tất cả các checkbox có name là "langs"
    const langCheckboxes = document.querySelectorAll('input[name="langs"]');
    const allCheckbox = document.querySelector('input[name="langs"][value="all"]');

    langCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // 1. Nếu tick vào "Tự nhận diện"
            if (this.value === 'all' && this.checked) {
                langCheckboxes.forEach(cb => {
                    if (cb.value !== 'all') {
                        cb.checked = false; // Bỏ tick các ô khác
                    }
                });
            }
            // 2. Nếu tick vào một ngôn ngữ cụ thể (vie, eng)
            else if (this.value !== 'all' && this.checked) {
                allCheckbox.checked = false; // Bỏ tick "Tự nhận diện"
            }

            // 3. Đảm bảo luôn có ít nhất 1 ô được chọn
            const anyChecked = Array.from(langCheckboxes).some(cb => cb.checked);
            if (!anyChecked) {
                allCheckbox.checked = true; // Trả về mặc định là "Tự nhận diện"
            }
        });
    });
});

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

    // 1. Lấy danh sách ngôn ngữ đã chọn trước khi đóng Modal
    const selectedLangs = [];
    document.querySelectorAll('#languageSection input[name="langs"]:checked').forEach((checkbox) => {
        selectedLangs.push(checkbox.value);
    });
    // Gộp thành chuỗi cách nhau bằng dấu phẩy (vd: "vie,eng" hoặc "all")
    const languagesStr = selectedLangs.join(',');

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
            onImageCropped(blob, languagesStr);
        } else {
            console.error("Lỗi: Hàm onImageCropped(blob) chưa được định nghĩa!");
        }

        // Dọn dẹp
        cropper.destroy();
        cropper = null;
    }, 'image/jpeg', 0.9);
}