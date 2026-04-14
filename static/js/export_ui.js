/**
 * EXPORT UI LOGIC
 * Chứa các hàm xử lý Modal Export và Render Preview
 */

function openExportModal() {
    const modal = document.getElementById('export-modal');
    if (modal) modal.style.display = 'block';

    // Mặc định chọn Excel khi mở
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

// Đóng modal khi click ra ngoài vùng content
window.addEventListener('click', function(event) {
    const modal = document.getElementById('export-modal');
    if (event.target == modal) closeExportModal();
});

function handleTypeChange(type) {
    const pngSettings = document.getElementById('png-settings');
    const container = document.getElementById('expmdl-preview-container');

    if (type === 'png') {
        pngSettings.style.display = 'block';
        container.style.display = 'flex';
        container.style.justifyContent = 'center';
        container.style.alignItems = 'center';
        container.style.overflow = 'hidden';
        updatePngPreview();
    } else {
        pngSettings.style.display = 'none';
        container.style.display = 'block';
        container.style.overflow = 'auto';
        container.style.backgroundColor = 'white';
        container.style.backgroundImage = 'none';
        renderExcelPreview();
    }
}

function renderExcelPreview() {
    if (!window.mySpreadsheet) return;
    const data = window.FINAL_TABLE_DATA || [['']];
    const container = document.getElementById('expmdl-preview-container');

    const maxR = Math.min(data.length, 20); // Xem trước tối đa 20 dòng
    const maxC = data[0] ? data[0].length : 0;

    let html = '<table class="expmdl-preview-table" id="expmdl-table-render">';

    // Header chữ cái (A, B, C...)
    html += '<tr style="position: sticky; top: 0; z-index: 10;">';
    html += '<td class="expmdl-excel-header" style="position: sticky; left: 0; z-index: 20;"></td>';
    for (let c = 0; c < maxC; c++) {
        html += `<td class="expmdl-excel-header">${expmdl_getColumnLabel(c)}</td>`;
    }
    html += '</tr>';

    // Dữ liệu
    for (let r = 0; r < maxR; r++) {
        html += '<tr>';
        html += `<td class="expmdl-excel-header" style="position: sticky; left: 0; z-index: 5;">${r + 1}</td>`;
        for (let c = 0; c < maxC; c++) {
            let cellVal = data[r][c] || '';
            html += `<td>${cellVal}</td>`;
        }
        html += '</tr>';
    }
    html += '</table>';

    container.innerHTML = html;
}

function updatePngPreview() {
    const startCell = document.getElementById('png-start').value || "A1";
    let rows = parseInt(document.getElementById('png-rows').value) || 1;
    let cols = parseInt(document.getElementById('png-cols').value) || 1;
    const bgColor = document.getElementById('bg-color-select').value;
    const container = document.getElementById('expmdl-preview-container');
    const data = window.FINAL_TABLE_DATA || [['']];

    // Hàm parse nội bộ hoặc dùng chung từ file chính
    const startPos = typeof parseCoords === 'function' ? parseCoords(startCell) : {col:0, row:0};

    rows = Math.min(rows, 30);
    cols = Math.min(cols, 30);

    let html = '<table id="expmdl-table-render" style="border-collapse: collapse; border: 1px solid #ddd;">';
    for (let r = 0; r < rows; r++) {
        html += '<tr>';
        for (let c = 0; c < cols; c++) {
            const rIdx = startPos.row + r;
            const cIdx = startPos.col + c;
            const val = (data[rIdx] && data[rIdx][cIdx] !== undefined) ? data[rIdx][cIdx] : '';
            html += `<td style="border: 1px solid #ddd; padding: 8px; min-width: 80px; height: 30px;">${val}</td>`;
        }
        html += '</tr>';
    }
    html += '</table>';
    container.innerHTML = html;

    autoScalePreview();

    const table = document.getElementById('expmdl-table-render');
    if (bgColor === 'black') {
        container.style.backgroundColor = '#333';
        table.style.color = 'white';
        table.style.borderColor = '#555';
        container.style.backgroundImage = 'none';
    } else if (bgColor === 'transparent') {
        container.style.backgroundColor = 'transparent';
        container.style.backgroundImage = 'repeating-conic-gradient(#f0f0f0 0% 25%, #fff 0% 50%)';
        container.style.backgroundSize = '20px 20px';
        table.style.color = 'black';
        table.style.borderColor = '#ddd';
    } else {
        container.style.backgroundColor = 'white';
        container.style.backgroundImage = 'none';
        table.style.color = 'black';
        table.style.borderColor = '#ddd';
    }
}

function autoScalePreview() {
    const container = document.getElementById('expmdl-preview-container');
    const table = document.getElementById('expmdl-table-render');
    if (!container || !table) return;

    table.style.transform = 'scale(1)';
    const containerW = container.offsetWidth - 40;
    const containerH = container.offsetHeight - 40;
    const scale = Math.min(containerW / table.scrollWidth, containerH / table.scrollHeight, 1);

    table.style.transform = 'scale(' + scale + ')';
    table.style.transformOrigin = 'center';
}

function expmdl_getColumnLabel(n) {
    let label = "";
    while (n >= 0) {
        label = String.fromCharCode((n % 26) + 65) + label;
        n = Math.floor(n / 26) - 1;
    }
    return label;
}