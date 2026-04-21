// -*- coding: utf-8 -*-

document.addEventListener("DOMContentLoaded", function () {
	// 1. Khởi tạo bảng dữ liệu
	initSpreadsheet();
	
	// 2. Lắng nghe sự kiện upload ảnh gốc
	const picUpload = document.getElementById('pic-upload');
	if (picUpload) {
		picUpload.addEventListener('change', function () {
			if (this.files && this.files[0]) {
				window.originalFileName = this.files[0].name;
				console.log("Đã lưu tên file gốc:", window.originalFileName);
			}
		});
	}
});

/**
 * Nút bấm Chốt dữ liệu (Final)
 */
function saveTableData() {
	Swal.fire({
		title: 'Xác nhận lưu?',
		text: "Dữ liệu sẽ được đánh dấu là Final.",
		icon: 'question',
		showCancelButton: true,
		confirmButtonText: 'Đồng ý'
	}).then((result) => {
		if (result.isConfirmed) {
			performSave(false);
			Swal.fire('Thành công!', 'Dữ liệu đã được chốt.', 'success');
		}
	});
}

/**
 * Gọi AI xử lý nội dung từ Prompt
 */
function generateAIContent() {
	const promptText = document.getElementById('ai-prompt').value;
	const resultDisplay = document.getElementById('ai-result-display');
	const btn = document.getElementById('btn-ai-gen');
	
	if (!promptText) {
		return Swal.fire({
			icon: 'warning',
			title: 'Thông báo',
			text: 'Vui lòng nhập yêu cầu!',
			confirmButtonColor: '#3085d6',
			confirmButtonText: 'Đồng ý'
		});
	}
	const originalText = btn.innerText;
	btn.innerText = "...";
	btn.disabled = true;
	
	apiGenerateAIContent(promptText)
		.then(data => {
			if (data.status === 'success') {
				resultDisplay.value = data.result.replace(/`/g, "").trim();
				resultDisplay.select();
			} else {
				alert("Lỗi: " + data.message);
			}
		})
		.finally(() => {
			btn.innerText = originalText;
			btn.disabled = false;
		});
}