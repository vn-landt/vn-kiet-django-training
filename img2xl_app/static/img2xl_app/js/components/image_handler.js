// static/js/image_handler.js
let cropper;
window.currentBatchCropIndex = -1;
document.addEventListener('DOMContentLoaded', function () {
	// Lấy tất cả các checkbox có name là "langs"
	const langCheckboxes = document.querySelectorAll('input[name="langs"]');
	const allCheckbox = document.querySelector('input[name="langs"][value="all"]');
	
	langCheckboxes.forEach(checkbox => {
		checkbox.addEventListener('change', function () {
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
		reader.onload = function (e) {
			const img = document.getElementById('imageToEdit');
			img.src = e.target.result;
			
			// Hiển thị Modal
			document.getElementById('editorModal').style.display = 'block';
			
			// Làm mới Cropper nếu đã tồn tại
			if (cropper) {
				cropper.destroy();
			}
			prepareModalUI();
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
	
	const selectedLangs = [];
	document.querySelectorAll('#languageSection input[name="langs"]:checked').forEach((checkbox) => {
		selectedLangs.push(checkbox.value);
	});
	const languagesStr = selectedLangs.join(',');
	const deleteDuration = document.getElementById('deleteDuration').value;
	
	const canvas = cropper.getCroppedCanvas({maxWidth: 2048, maxHeight: 2048});
	
	canvas.toBlob((blob) => {
		document.getElementById('editorModal').style.display = 'none';
		
		// LOGIC MỚI: Kiểm tra nếu đang thao tác trong chế độ Batch và có chỉ số
		if (window.extractMode === 'batch' && window.currentBatchCropIndex !== -1) {
			// Cập nhật lại blob đã cắt vào mảng
			window.batchFiles[window.currentBatchCropIndex].file = blob;
			window.batchFiles[window.currentBatchCropIndex].isCropped = true;
			window.currentBatchCropIndex = -1; // Reset
			renderBatchList(); // Gọi render lại giao diện list
		} else {
			// LOGIC CŨ: Single mode
			if (typeof onImageCropped === 'function') {
				onImageCropped(blob, languagesStr, window.originalFileName || "unknown_part.jpg", deleteDuration);
			} else {
				console.error("Lỗi: Hàm onImageCropped chưa được định nghĩa!");
			}
		}
		
		cropper.destroy();
		cropper = null;
	}, 'image/jpeg', 0.9);
}

// Hàm mới để mở editor từ ảnh đã có preview (cho Single mode)
function prepareModalUI() {
	// 1. Tìm các phần tử cấu hình trong Modal
	const modalLangs = document.querySelector('#editorModal #languageSection');
	const modalDelete = document.querySelector('#editorModal #deleteSection');
	// 2. Tìm nút xác nhận (Sử dụng selector linh hoạt hơn)
	const confirmBtn = document.querySelector('#editorModal .btn-confirm, #editorModal button[onclick*="processAndExtract"]');
	
	// Kiểm tra mode hiện tại
	const isBatch = (window.extractMode === 'batch');
	
	// Ẩn/Hiện ngôn ngữ và thời gian trong Modal
	if (modalLangs) {
		modalLangs.style.display = isBatch ? 'none' : 'block';
	}
	if (modalDelete) {
		modalDelete.style.display = isBatch ? 'none' : 'block';
	}
	
	// Đổi text nút bấm an toàn
	if (confirmBtn) {
		confirmBtn.innerText = isBatch ? "Cắt & Lưu" : "Xác nhận & Trích xuất";
	}
}

function initEditorFromPreview(src, fileName) {
	const img = document.getElementById('imageToEdit');
	if (!img) return;
	
	img.src = src;
	window.originalFileName = fileName;
	
	// Thiết lập giao diện trước khi hiện Modal
	prepareModalUI();
	
	const modal = document.getElementById('editorModal');
	if (modal) modal.style.display = 'block';
	
	if (cropper) cropper.destroy();
	
	// Đợi ảnh load xong mới init Cropper để tránh lỗi kích thước
	img.onload = function () {
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
}
