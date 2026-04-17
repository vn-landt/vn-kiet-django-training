// -*- coding: utf-8 -*-

document.addEventListener("DOMContentLoaded", function () {
	const rawData = window.DJANGO_TABLE_DATA || [['', '', '', '']];
	const spreadsheetDiv = document.getElementById('spreadsheet');
	if (spreadsheetDiv) {
		window.mySpreadsheet = jspreadsheet(spreadsheetDiv, {
			data: rawData,
			minDimensions: [11, 5],
			defaultColWidth: 150,
			tableOverflow: true,
			tableWidth: "100%",
			tableHeight: "400px"
		});
	}
});

/**
 * Cầu nối xử lý UI khi lưu dữ liệu
 */
function saveTableData() {
	const currentData = window.mySpreadsheet.getData();
	const $btn = $('.btn-save');
	
	$btn.text('Đang lưu...').prop('disabled', true);
	
	saveTableDataAPI(window.DJANGO_SAVE_URL, currentData)
		.then(data => {
			if (data.status === 'success') alert('Lưu thành công!');
			else alert('Lỗi: ' + data.message);
		})
		.catch(err => console.error('Lỗi:', err))
		.finally(() => {
			$btn.text('Save Changes').prop('disabled', false);
		});
}

/**
 * Xử lý AI Content
 */
function generateAIContent() {
	const promptText = $('#ai-prompt').val();
	const $resultDisplay = $('#ai-result-display');
	const $btn = $('#btn-ai-gen');
	
	if (!promptText) return alert("Vui lòng nhập yêu cầu!");
	
	const originalText = $btn.text();
	$btn.text('...').prop('disabled', true);
	$resultDisplay.val("Đang lấy kết quả...");
	
	generateAIContentAPI(promptText)
		.then(data => {
			if (data.status === 'success') {
				const res = data.result.replace(/`/g, "").trim();
				$resultDisplay.val(res).select();
			} else {
				alert("Lỗi: " + data.message);
			}
		})
		.finally(() => {
			$btn.text(originalText).prop('disabled', false);
		});
}