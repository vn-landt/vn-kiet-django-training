// -*- coding: utf-8 -*-

let autosaveTimeout = null;

/**
 * Khởi tạo bảng jspreadsheet
 */
function initSpreadsheet() {
	const rawData = window.DJANGO_TABLE_DATA || [['', '', '', '']];
	const spreadsheetDiv = document.getElementById('spreadsheet');
	if (spreadsheetDiv) {
		window.mySpreadsheet = jspreadsheet(spreadsheetDiv, {
			data: rawData,
			minDimensions: [10, 22],
			defaultColWidth: 120,
			tableWidth: "100%",
			tableHeight: "600px",
			allowInsertRow: true,
			allowInsertColumn: true,
			search: true,
			columnSorting: true,
			onchange: triggerAutoSave,
			oninsertrow: triggerAutoSave,
			oninsertcolumn: triggerAutoSave,
			ondeleterow: triggerAutoSave,
			ondeletecolumn: triggerAutoSave
		});
	}
}

/**
 * Hàm trì hoãn việc lưu (Debounce)
 */
function triggerAutoSave() {
	const statusEl = document.getElementById('autosave-status');
	if (statusEl) statusEl.innerText = "Đang chờ thay đổi...";
	
	clearTimeout(autosaveTimeout);
	autosaveTimeout = setTimeout(function () {
		performSave(true); // true = is_draft
	}, 2500);
}

/**
 * Thực hiện gửi dữ liệu lên server thông qua Service
 */
function performSave(isDraft) {
	if (!window.mySpreadsheet) return;
	
	const statusEl = document.getElementById('autosave-status');
	const finalTimeEl = document.getElementById('final-save-time-text');
	const currentData = window.mySpreadsheet.getData().map(row =>
		row.map(cell => (cell === null || cell === undefined) ? "" : String(cell))
	);
	
	if (statusEl) {
		statusEl.innerText = isDraft ? "Đang tự động lưu bản nháp..." : "Đang chốt dữ liệu...";
	}
	
	apiSaveTableData(currentData, isDraft)
		.then(data => {
			if (data.status === 'success') {
				if (statusEl) statusEl.innerText = "Đã lưu bản nháp lúc " + data.updated_at;
				
				if (isDraft === false) {
					window.FINAL_TABLE_DATA = JSON.parse(JSON.stringify(currentData));
					if (finalTimeEl) {
						let now = new Date();
						let dateStr = now.toLocaleDateString('vi-VN', {
							day: '2-digit',
							month: '2-digit',
							year: 'numeric'
						});
						let timeStr = now.toLocaleTimeString('vi-VN', {hour12: false});
						finalTimeEl.innerText = dateStr + " " + timeStr;
					}
				}
			}
		})
		.catch(() => {
			if (statusEl) statusEl.innerText = "Lỗi lưu dữ liệu!";
		});
}

/**
 * Cập nhật dữ liệu lên giao diện bảng
 */
function updateTableDisplay(newData, coords) {
	if (!window.mySpreadsheet) return;
	
	let currentData = window.mySpreadsheet.getData();
	let neededRows = coords.row + newData.length;
	let maxColsInNew = Math.max(...newData.map(r => r.length));
	let neededCols = coords.col + maxColsInNew;
	
	if (neededRows > currentData.length) {
		window.mySpreadsheet.insertRow(neededRows - currentData.length);
	}
	if (neededCols > (currentData[0] ? currentData[0].length : 0)) {
		window.mySpreadsheet.insertColumn(neededCols - currentData[0].length);
	}
	
	let updatedData = window.mySpreadsheet.getData();
	newData.forEach((rowData, rIdx) => {
		rowData.forEach((val, cIdx) => {
			let targetR = coords.row + rIdx;
			let targetC = coords.col + cIdx;
			if (updatedData[targetR]) updatedData[targetR][targetC] = val;
		});
	});
	
	window.mySpreadsheet.setData(updatedData);
}