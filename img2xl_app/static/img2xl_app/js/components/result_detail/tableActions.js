// -*- coding: utf-8 -*-


const TableCoordinateHelper = {
	parse: parseCoords, // parseCoords lấy từ utils.js
	ask: function (msg, def = "A1") {
		const input = prompt(msg, def);
		if (input === null) return null;
		const coords = this.parse(input.trim());
		if (!coords || coords.col < 0 || coords.row < 0) {
			alert("Lỗi tọa độ!");
			return this.ask(msg, def);
		}
		return coords;
	}
};

/**
 * Xử lý AI trích xuất ảnh
 */
async function onImageCropped(blob, languagesStr, originalFileName, deleteDuration) {
	const {value: targetCoordsStr} = await Swal.fire({
		title: 'Chọn ô bắt đầu',
		input: 'text',
		inputLabel: 'Dữ liệu AI sẽ được chèn từ ô này (Ví dụ: A1, B5...)',
		inputValue: 'A1',
		showCancelButton: true,
		confirmButtonText: 'Tiếp tục',
		cancelButtonText: 'Hủy',
		inputValidator: (value) => {
			if (!value) return 'Bạn cần nhập tọa độ ô!';
			const regex = /^[A-Z]+\d+$/i;
			if (!regex.test(value)) return 'Tọa độ không hợp lệ (Ví dụ: A1, B10)';
		}
	});
	
	
	if (!targetCoordsStr) return;
	const coordsObj = parseCoords(targetCoordsStr); // Dùng từ utils.js
	
	// 2. Hiển thị Loading
	Swal.fire({
		title: 'Đang xử lý...', allowOutsideClick: false, didOpen: () => {
			Swal.showLoading();
		}
	});
	
	const formData = new FormData();
	formData.append('file', blob, 'extracted_part.jpg');
	formData.append('original_filename', originalFileName);
	formData.append('save_db', 'false');
	formData.append('result_id', window.CURRENT_RESULT_ID);
	formData.append('languages', languagesStr || 'all');
	formData.append('deleteDuration', deleteDuration);
	
	apiExtractImagePart(formData)
		.then(data => {
			Swal.close();
			if (data.status === 'success') {
				updateTableDisplay(data.table, coordsObj);
				triggerAutoSave();
				Swal.fire({icon: 'success', title: 'Đã chèn dữ liệu!', toast: true, position: 'top-end', timer: 3000});
			} else if (data.status === 'limit_exceeded') {
				Swal.fire({
					title: 'Kho lưu trữ đầy!',
					text: data.message,
					icon: 'warning',
					confirmButtonText: 'Đến trang dọn dẹp'
				})
					.then((result) => {
						if (result.isConfirmed) window.location.href = data.redirect_url;
					});
			} else {
				Swal.fire({icon: 'error', title: 'Lỗi', text: data.message});
			}
		})
		.catch(() => {
			Swal.close();
			Swal.fire({icon: 'error', title: 'Lỗi kết nối'});
		});
}

function handleCSVUpdate() {
	const fileInput = document.getElementById('csv-upload');
	if (!fileInput || fileInput.files.length === 0) return alert("Vui lòng chọn CSV!");
	const targetCoords = TableCoordinateHelper.ask("Chọn ô bắt đầu:");
	if (!targetCoords) return;
	
	const reader = new FileReader();
	reader.onload = (e) => {
		const rows = e.target.result.split("\n").filter(l => l.trim()).map(row => row.split(","));
		updateTableDisplay(rows, targetCoords);
	};
	reader.readAsText(fileInput.files[0]);
}

/**
 * Xử lý chia cột hoặc xóa ký tự theo vùng chọn
 */
function handleRangeAction(actionType) {
	const startInput = document.getElementById('range-start').value;
	const endInput = document.getElementById('range-end').value;
	const char = document.getElementById('special-char').value;
	
	if (!startInput || !endInput || !char) return alert("Vui lòng nhập đủ thông tin!");
	
	const start = parseCoords(startInput);
	const end = parseCoords(endInput);
	if (!start || !end) return alert("Phạm vi lỗi!");
	
	let tempData = window.mySpreadsheet.getData();
	const rStart = Math.max(0, start.row), rEnd = Math.min(end.row, tempData.length - 1);
	const cStart = Math.max(0, start.col), cEnd = Math.min(end.col, (tempData[0] ? tempData[0].length : 0) - 1);
	
	for (let r = rEnd; r >= rStart; r--) {
		for (let c = cEnd; c >= cStart; c--) {
			let cellValue = tempData[r][c];
			if (cellValue && typeof cellValue === 'string') {
				let lastIdx = cellValue.lastIndexOf(char);
				if (lastIdx !== -1) {
					let textBefore = cellValue.substring(0, lastIdx).trim();
					let textAfter = cellValue.substring(lastIdx).trim();
					if (actionType === 'split-col') {
						tempData[r][c] = textBefore;
						tempData[r].splice(c + 1, 0, textAfter);
					} else if (actionType === 'split-row') {
						tempData[r][c] = textBefore;
						let newRow = new Array(tempData[r].length).fill("");
						newRow[c] = textAfter;
						tempData.splice(r + 1, 0, newRow);
					} else if (actionType === 'remove') {
						tempData[r][c] = cellValue.split(char).join('');
					}
				}
			}
		}
	}
	window.mySpreadsheet.setData(tempData);
}