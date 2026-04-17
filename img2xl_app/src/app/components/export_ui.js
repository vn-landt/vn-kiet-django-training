// -*- coding: utf-8 -*-
// [Quy tắc: 4 hard tabs, max 100 chars]

function openExportModal() {
	const modal = document.getElementById('export-modal');
	if (modal) modal.style.display = 'block';

	const radioExcel = document.querySelector('input[name="export_type"][value="xlsx"]');
	if (radioExcel) {
		radioExcel.checked = true;
		handleTypeChange('xlsx');
	}
}

function closeExportModal() {
	const modal = document.getElementById('export-modal');
	if (modal) modal.style.display = 'none';
}

// Lắng nghe click ngoài vùng modal để đóng
window.addEventListener('click', function(event) {
	const modal = document.getElementById('export-modal');
	if (event.target == modal) closeExportModal();
});

function handleTypeChange(type) {
	const pngSettings = document.getElementById('png-settings');
	const container = document.getElementById('expmdl-preview-container');

	if (type === 'png') {
		pngSettings.style.display = 'block';
		Object.assign(container.style, { display: 'flex', justifyContent: 'center' });
		updatePngPreview();
	} else {
		pngSettings.style.display = 'none';
		Object.assign(container.style, { display: 'block', backgroundColor: 'white' });
		renderExcelPreview();
	}
}

function renderExcelPreview() {
	const data = window.FINAL_TABLE_DATA || [['']];
	const container = document.getElementById('expmdl-preview-container');
	const maxR = Math.min(data.length, 20);
	const maxC = data[0] ? data[0].length : 0;

	let html = '<table class="expmdl-preview-table" id="expmdl-table-render">';
	html += '<tr><td class="expmdl-excel-header"></td>';
	for (let c = 0; c < maxC; c++) {
		html += `<td class="expmdl-excel-header">${expmdl_getColumnLabel(c)}</td>`;
	}
	html += '</tr>';

	for (let r = 0; r < maxR; r++) {
		html += `<tr><td class="expmdl-excel-header">${r + 1}</td>`;
		for (let c = 0; c < maxC; c++) {
			html += `<td>${data[r][c] || ''}</td>`;
		}
		html += '</tr>';
	}
	container.innerHTML = html + '</table>';
}

function autoScalePreview() {
	const container = document.getElementById('expmdl-preview-container');
	const table = document.getElementById('expmdl-table-render');
	if (!container || !table) return;

	const scale = calculateScale(container, table);
	table.style.transform = 'scale(' + scale + ')';
	table.style.transformOrigin = 'center';
}