// -*- coding: utf-8 -*-

window.extractMode = 'single';
window.batchFiles = [];

/**
 * Thay đổi chế độ trích xuất Single/Batch
 */
window.toggleMode = function () {
	const mode = document.querySelector('input[name="extractMode"]:checked').value;
	const singleRadio = document.querySelector('input[name="extractMode"][value="single"]');
	
	if (mode === 'batch' && !window.isAuthenticated) {
		Swal.fire({
			icon: 'warning',
			title: 'Yêu cầu đăng nhập',
			text: 'Tính năng này dành cho thành viên!',
			confirmButtonText: 'Đăng nhập',
			showCancelButton: true
		}).then((r) => {
			if (r.isConfirmed) window.location.href = "/login/";
		});
		singleRadio.checked = true;
		window.extractMode = 'single';
		return;
	}
	
	window.extractMode = mode;
	const configSection = document.getElementById('globalConfigSection');
	const fileInput = document.getElementById('id_file');
	
	if (mode === 'batch') {
		configSection.classList.remove('config-frozen');
		configSection.querySelectorAll('input, select').forEach(i => i.disabled = false);
		fileInput.setAttribute('multiple', 'multiple');
	} else {
		configSection.classList.add('config-frozen');
		configSection.querySelectorAll('input, select').forEach(i => i.disabled = true);
		fileInput.removeAttribute('multiple');
	}
	
	document.getElementById('singlePreviewArea').style.display = 'none';
	document.getElementById('batchPreviewArea').style.display = 'none';
	document.getElementById('previewPlaceholder').style.display = 'block';
};

/**
 * Hiển thị danh sách ảnh Batch
 */
window.renderBatchList = function () {
    const container = document.getElementById('batchList');
    const countDisplay = document.getElementById('fileCount');
    if (!container) return;
    
    container.innerHTML = '';
    countDisplay.innerText = window.batchFiles.length;
    
    const rowHtml = document.createElement('div');
    rowHtml.className = 'row p-2';
    container.appendChild(rowHtml);
    
    window.batchFiles.forEach((item, index) => {
       // Tạo URL xem trước
       const imageUrl = URL.createObjectURL(item.file);
       
       const html = `
            <div class="col-6 col-md-4 mb-3">
                <div class="batch-item-wrapper">
                    <img src="${imageUrl}" class="batch-img-large ${item.isCropped ? 'img-is-cropped' : ''}">
                    
                    <div class="batch-actions-overlay">
                        <button onclick="cropBatchItem(${index})" class="btn btn-primary btn-sm rounded-circle"><i class="fas fa-crop"></i></button>
                        <button onclick="deleteBatchItem(${index})" class="btn btn-danger btn-sm rounded-circle"><i class="fas fa-times"></i></button>
                    </div>

                    ${item.isCropped ? '<span class="badge badge-success badge-cropped">Đã cắt</span>' : ''}
                    
                    <div class="batch-file-name text-truncate" title="${item.originalName}">${item.originalName}</div>
                </div>
            </div>`;
       rowHtml.insertAdjacentHTML('beforeend', html);

       // Giải phóng bộ nhớ sau khi ảnh đã load để tránh bị lag browser
       const currentImg = rowHtml.lastElementChild.querySelector('img');
       currentImg.onload = () => URL.revokeObjectURL(imageUrl);
    });
};

window.deleteBatchItem = function (index) {
	window.batchFiles.splice(index, 1);
	renderBatchList();
	if (window.batchFiles.length === 0) {
		document.getElementById('batchPreviewArea').style.display = 'none';
		document.getElementById('previewPlaceholder').style.display = 'block';
	}
};

window.cropBatchItem = function (index) {
	window.currentBatchCropIndex = index;
	const item = window.batchFiles[index];
	window.originalFileName = item.originalName;
	initEditor({files: [item.file]});
};

window.clearAllFiles = function () {
	window.batchFiles = [];
	if (typeof renderBatchList === 'function') renderBatchList();
	document.getElementById('batchPreviewArea').style.display = 'none';
	document.getElementById('singlePreviewArea').style.display = 'none';
	document.getElementById('previewPlaceholder').style.display = 'block';
	const fileInput = document.getElementById('id_file');
	if (fileInput) fileInput.value = '';
};