// -*- coding: utf-8 -*-
let cropper;

$(document).ready(function () {
	initLanguageSwitcher();
});

/**
 * Logic chuyển đổi giữa "Tự nhận diện" và ngôn ngữ cụ thể
 */
function initLanguageSwitcher() {
	const $langCheckboxes = $('input[name="langs"]');
	const $allCheckbox = $('input[name="langs"][value="all"]');
	
	$langCheckboxes.on('change', function () {
		if (this.value === 'all' && this.checked) {
			$langCheckboxes.not(this).prop('checked', false);
		} else if (this.value !== 'all' && this.checked) {
			$allCheckbox.prop('checked', false);
		}
		if ($langCheckboxes.filter(':checked').length === 0) {
			$allCheckbox.prop('checked', true);
		}
	});
}

/**
 * Khởi tạo trình cắt ảnh
 */
function startCropper(imgElement) {
	if (cropper) cropper.destroy();
	cropper = new Cropper(imgElement, {
		viewMode: 1,
		dragMode: 'move',
		autoCropArea: 0.8,
		restore: false,
		guides: true,
		center: true,
		highlight: false,
		cropBoxMovable: true,
		cropBoxResizable: true,
		toggleDragModeOnDblclick: false
	});
}

/**
 * Xử lý sau khi người dùng nhấn "Xác nhận"
 */
async function processAndExtract() {
	if (!cropper) return;
	
	const selectedLangs = $('input[name="langs"]:checked').map((_, el) => el.value).get().join(',');
	const deleteDuration = $('#deleteDuration').val();
	
	// GỌI SERVICE XỬ LÝ DỮ LIỆU
	const blob = await getCroppedBlob(cropper);
	
	$('#editorModal').hide();
	
	if (window.extractMode === 'batch' && window.currentBatchCropIndex !== -1) {
		updateBatchFile(blob); // Hàm này nằm trong batch_handler.js
	} else {
		handleSingleExtraction(blob, selectedLangs, deleteDuration);
	}
	
	cropper.destroy();
	cropper = null;
}

function handleSingleExtraction(blob, langs, duration) {
	const fileName = window.originalFileName || "unknown_part.jpg";
	if (typeof onImageCropped === 'function') {
		onImageCropped(blob, langs, fileName, duration);
	}
}

function closeEditor() {
	$('#editorModal').hide();
	$('#id_file').val("");
	if (cropper) cropper.destroy();
}