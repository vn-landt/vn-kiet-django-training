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

/**
 * Xoay ảnh theo góc độ
 * @param {number} degree - Số độ cần xoay (dương: chiều kim đồng hồ, âm: ngược lại)
 */
function rotateImage(degree) {
    if (cropper) {
        cropper.rotate(degree);
    }
}

/**
 * Lật ảnh theo chiều ngang (trái <-> phải)
 */
function flipImageHorizontal() {
    if (cropper) {
        // Lấy dữ liệu hiện tại để biết trạng thái lật
        const data = cropper.getData();
        // Nếu scaleX là 1 thì đổi thành -1 (lật), nếu -1 thì đổi thành 1 (về thường)
        cropper.scaleX(data.scaleX === 1 ? -1 : 1);
    }
}

function initEditor(input) {
    if (input.files && input.files[0]) {
       const reader = new FileReader();
       reader.onload = function (e) {
          const img = document.getElementById('imageToEdit');
          if(!img) return;
          img.src = e.target.result;
          
          document.getElementById('editorModal').style.display = 'block';
          
          if (cropper) {
             cropper.destroy();
          }
          prepareModalUI();
          
          // Khởi tạo Cropper
          cropper = new Cropper(img, {
             viewMode: 1, // Quan trọng để khi xoay/lật không bị văng vùng chọn ra ngoài
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
    const modal = document.getElementById('editorModal');
    if (modal) modal.style.display = 'none';
    
    const fileInput = document.getElementById('id_file');
    if (fileInput) fileInput.value = "";
    
    if (cropper) {
       cropper.destroy();
       cropper = null; // Đảm bảo giải phóng bộ nhớ
    }
}

function processAndExtract() {
    if (!cropper) return;
    
    const selectedLangs = [];
    document.querySelectorAll('#languageSection input[name="langs"]:checked').forEach((checkbox) => {
       selectedLangs.push(checkbox.value);
    });
    const languagesStr = selectedLangs.join(',');
    
    const deleteDurationEle = document.getElementById('deleteDuration');
    const deleteDuration = deleteDurationEle ? deleteDurationEle.value : '0';
    
    // getCroppedCanvas sẽ tự động tính toán ảnh dựa trên trạng thái xoay và lật hiện tại
    const canvas = cropper.getCroppedCanvas({maxWidth: 2048, maxHeight: 2048});
    
    canvas.toBlob((blob) => {
       const modal = document.getElementById('editorModal');
       if (modal) modal.style.display = 'none';
       
       if (window.extractMode === 'batch' && window.currentBatchCropIndex !== -1) {
          if (window.batchFiles && window.batchFiles[window.currentBatchCropIndex]) {
              window.batchFiles[window.currentBatchCropIndex].file = blob;
              window.batchFiles[window.currentBatchCropIndex].isCropped = true;
          }
          window.currentBatchCropIndex = -1;
          if (typeof renderBatchList === 'function') renderBatchList();
       } else {
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

function prepareModalUI() {
    const modalLangs = document.querySelector('#editorModal #languageSection');
    const modalDelete = document.querySelector('#editorModal #deleteSection');
    const confirmBtn = document.querySelector('#editorModal .btn-confirm, #editorModal button[onclick*="processAndExtract"]');
    
    const isBatch = (window.extractMode === 'batch');
    
    if (modalLangs) modalLangs.style.display = isBatch ? 'none' : 'block';
    if (modalDelete) modalDelete.style.display = isBatch ? 'none' : 'block';
    
    if (confirmBtn) {
       confirmBtn.innerText = isBatch ? "Cắt & Lưu" : "Xác nhận & Trích xuất";
    }
}

function initEditorFromPreview(src, fileName) {
    const img = document.getElementById('imageToEdit');
    if (!img) return;
    
    img.src = src;
    window.originalFileName = fileName;
    
    prepareModalUI();
    
    const modal = document.getElementById('editorModal');
    if (modal) modal.style.display = 'block';
    
    if (cropper) cropper.destroy();
    
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
       // Tránh việc gọi onload nhiều lần nếu src thay đổi
       img.onload = null;
    };
    
    // Trường hợp ảnh đã load xong trước khi gán onload (từ cache)
    if (img.complete) {
        img.onload();
    }
}