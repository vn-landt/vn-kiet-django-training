// -*- coding: utf-8 -*-

document.addEventListener('DOMContentLoaded', function () {
	// 1. Khởi tạo các module
	initHistoryManager();
	toggleMode();
	
	const fileInput = document.getElementById('id_file');
	const selectBtn = document.getElementById('selectBtn');
	
	// 2. Xử lý chọn file
	selectBtn.addEventListener('click', function (e) {
		e.preventDefault();
		e.stopPropagation();
		fileInput.click();
	});
	
	fileInput.addEventListener('change', function (e) {
		const files = e.target.files;
		if (!files || files.length === 0) return;
		
		document.getElementById('previewPlaceholder').style.display = 'none';
		
		if (window.extractMode === 'single') {
			const file = files[0];
			window.originalFileName = file.name;
			const reader = new FileReader();
			reader.onload = (event) => {
				document.getElementById('imagePreview').src = event.target.result;
				document.getElementById('fileNameDisplay').innerText = file.name;
				document.getElementById('singlePreviewArea').style.display = 'block';
				document.getElementById('batchPreviewArea').style.display = 'none';
			};
			reader.readAsDataURL(file);
		} else {
			for (let i = 0; i < files.length; i++) {
				if (window.batchFiles.length < 10) {
					window.batchFiles.push({file: files[i], originalName: files[i].name, isCropped: false});
				}
			}
			renderBatchList();
			document.getElementById('batchPreviewArea').style.display = 'block';
			document.getElementById('singlePreviewArea').style.display = 'none';
		}
		this.value = '';
	});
	
	// 3. Xử lý nút trích xuất
	document.getElementById('extractBtn').addEventListener('click', function () {
		const imgDisplay = document.getElementById('imagePreview');
		if (imgDisplay.src) initEditorFromPreview(imgDisplay.src, window.originalFileName);
	});
	
	document.getElementById('batchExtractBtn').addEventListener('click', startBatchProcessing);
	
	// 4. Tạo bảng trống
	$('#btn-create-blank').on('click', function () {
		Swal.fire({
			title: 'Đặt tên bảng tính',
			input: 'text',
			showCancelButton: true,
			confirmButtonText: 'Tạo ngay',
			inputValidator: (v) => {
				if (!v) return 'Cần nhập tên!';
			}
		}).then((result) => {
			if (result.isConfirmed && result.value) {
				Swal.showLoading();
				apiCreateBlankSpreadsheet(result.value).done(res => {
					if (res.status === 'success') window.location.href = res.redirect_url;
					else Swal.fire('Lỗi', res.message, 'error');
				});
			}
		});
	});
});