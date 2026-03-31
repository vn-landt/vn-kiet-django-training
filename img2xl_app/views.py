document.addEventListener("DOMContentLoaded", function() {
        var rawData = window.DJANGO_TABLE_DATA || [['', '', '', '']];
    var spreadsheetDiv = document.getElementById('spreadsheet');
    if (spreadsheetDiv) {
        window.mySpreadsheet = jspreadsheet(spreadsheetDiv, {
            data: rawData,
            minDimensions: [10, 10],
            defaultColWidth: 120,
            tableOverflow: true,
            tableWidth: "100%",
            tableHeight: "400px",
            allowInsertRow: true, // Cho phép thêm dòng
            allowInsertColumn: true, // Cho phép thêm cột
            search: true,
            columnSorting: true,
        });
    }
});

/**
 * Hàm dùng chung để cập nhật dữ liệu lên giao diện (không lưu DB)
 * @param {Array} newData - Mảng 2 chiều chứa dữ liệu mới
 * @param {Object} coords - Tọa độ bắt đầu {col, row}
 */
function updateTableDisplay(newData, coords) {
    if (!window.mySpreadsheet) return;

    let currentData = window.mySpreadsheet.getData();
    let neededRows = coords.row + newData.length;
    let maxColsInNew = Math.max(...newData.map(r => r.length));
    let neededCols = coords.col + maxColsInNew;

    // Tự động thêm dòng/cột nếu dữ liệu mới lớn hơn bảng hiện tại
    if (neededRows > currentData.length) {
        window.mySpreadsheet.insertRow(neededRows - currentData.length);
    }
    if (neededCols > (currentData[0] ? currentData[0].length : 0)) {
        window.mySpreadsheet.insertColumn(neededCols - currentData[0].length);
    }

    // Lấy lại dữ liệu mới nhất sau khi đã mở rộng
    let updatedData = window.mySpreadsheet.getData();
    newData.forEach((rowData, rIdx) => {
        rowData.forEach((val, cIdx) => {
            let targetR = coords.row + rIdx;
            let targetC = coords.col + cIdx;
            if (updatedData[targetR]) {
                updatedData[targetR][targetC] = val;
            }
        });
    });

    window.mySpreadsheet.setData(updatedData);
}

const TableCoordinateHelper = {
    parse: parseCoords,
    ask: function(msg, def = "A1") {
        const input = prompt(msg, def);
        if (input === null) return null;
        const coords = this.parse(input.trim());
        if (!coords || coords.col < 0 || coords.row < 0) { alert("Lỗi tọa độ!"); return this.ask(msg, def); }
        return coords;
    }
};

// Hàm chuyển A1 -> {col: 0, row: 0} (Đã xóa bản trùng lặp bên dưới)
function parseCoords(cellStr) {
    const match = cellStr.toUpperCase().match(/^([A-Z]+)(\d+)$/);
    if (!match) return null;
    let colStr = match[1];
    let row = parseInt(match[2]) - 1;
    let col = 0;
    for (let i = 0; i < colStr.length; i++) {
        col = col * 26 + (colStr.charCodeAt(i) - 64);
    }
    return { col: col - 1, row: row };
}



async function handlePicGenerate() {
    const fileInput = document.getElementById('pic-upload');

    // 1. Thông báo nếu chưa chọn file
    if (fileInput.files.length === 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Thông báo',
            text: 'Vui lòng chọn ảnh trước khi thực hiện!',
            confirmButtonColor: '#3085d6'
        });
        return;
    }

    // Hỏi tọa độ bằng SweetAlert2 (Thay thế TableCoordinateHelper.ask)
    const { value: targetCoords } = await Swal.fire({
        title: 'Chọn ô bắt đầu',
        input: 'text',
        inputLabel: 'Ví dụ: A1, B5, C10...',
        inputValue: 'A1', // Giá trị mặc định
        showCancelButton: true,
        confirmButtonText: 'Tiếp tục',
        cancelButtonText: 'Hủy',
        inputValidator: (value) => {
            if (!value) {
                return 'Bạn cần nhập tọa độ ô!';
            }
            // Regex kiểm tra định dạng ô Excel (VD: A1, AB10)
            const regex = /^[A-Z]+\d+$/i;
            if (!regex.test(value)) {
                return 'Tọa độ không hợp lệ (Ví dụ đúng: A1, B10)';
            }
        }
    });
    if (!targetCoords) return;

    // 2. Hiển thị trạng thái Loading chuyên nghiệp
    Swal.fire({
        title: 'Đang xử lý...',
        text: 'Vui lòng chờ Gemini phân tích dữ liệu',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading(); // Hiển thị vòng xoay
        }
    });

    const btn = document.querySelector('.btn-purple');
    const originalText = btn.innerText;
    btn.innerText = "...";
    btn.disabled = true;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch("/extract-only-api/", {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        // Đóng loading khi có phản hồi
        Swal.close();

        if (data.status === 'success') {
            updateTableDisplay(data.table, targetCoords);

            // Thông báo thành công nhẹ nhàng (Toast)
            const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true
            });
            Toast.fire({
                icon: 'success',
                title: 'Trích xuất thành công!'
            });

        } else {
            // 3. Hiển thị lỗi từ Backend (Lỗi size, định dạng, mặt người...)
            Swal.fire({
                icon: 'error',
                title: 'Không thể trích xuất',
                text: data.message, // Thông báo từ _perform_extraction_logic
                confirmButtonColor: '#d33',
                confirmButtonText: 'Đóng'
            });
        }
    })
    .catch(err => {
        Swal.fire({
            icon: 'error',
            title: 'Lỗi kết nối',
            text: 'Không thể kết nối tới máy chủ. Vui lòng thử lại sau.'
        });
    })
    .finally(() => {
        btn.innerText = originalText;
        btn.disabled = false;
    });
}

function handleCSVUpdate() {
    const fileInput = document.getElementById('csv-upload');
    if (fileInput.files.length === 0) return alert("Vui lòng chọn CSV!");
    const targetCoords = TableCoordinateHelper.ask("Chọn ô bắt đầu:");
    if (!targetCoords) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        const rows = e.target.result.split("\n").filter(l => l.trim()).map(row => row.split(","));
        updateTableDisplay(rows, targetCoords);
    };
    reader.readAsText(fileInput.files[0]);
}

// Xử lý Chia Cột hoặc Xóa Ký Tự theo phạm vi
function handleRangeAction(actionType) {
    const startInput = document.getElementById('range-start').value;
    const endInput = document.getElementById('range-end').value;
    const char = document.getElementById('special-char').value;

    if (!startInput || !endInput || !char) return alert("Vui lòng nhập đủ thông tin!");

    const start = parseCoords(startInput);
    const end = parseCoords(endInput);
    if (!start || !end) return alert("Phạm vi lỗi!");

    let tempData = window.mySpreadsheet.getData();

    // --- BẮT ĐẦU LOGIC THÔNG MINH ---
    const actualMaxRow = tempData.length - 1;
    const actualMaxCol = (tempData[0] ? tempData[0].length : 0) - 1;

    // Nếu người dùng nhập lố, ta ép nó về giới hạn thực tế của bảng
    const rStart = Math.max(0, start.row);
    const rEnd = Math.min(end.row, actualMaxRow);
    const cStart = Math.max(0, start.col);
    const cEnd = Math.min(end.col, actualMaxCol);

    // Kiểm tra nếu sau khi ép, phạm vi không còn hợp lệ (vùng nhập nằm hoàn toàn ngoài bảng)
    if (rStart > rEnd || cStart > cEnd) {
        return alert("Phạm vi bạn nhập nằm ngoài vùng dữ liệu hiện tại!");
    }
    // --- KẾT THÚC LOGIC THÔNG MINH ---

    // Chạy vòng lặp dựa trên phạm vi đã được "ép" (rEnd, rStart, cEnd, cStart)
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
// Hàm lưu dữ liệu thực tế (ĐÃ SỬA: KHÔNG GỘP BẰNG '|')
function saveTableData() {
    if (!window.mySpreadsheet) return;

    // Làm sạch dữ liệu: Biến null/undefined thành chuỗi rỗng
    var currentData = window.mySpreadsheet.getData().map(function(row) {
        return row.map(function(cell) {
            return (cell === null || cell === undefined) ? "" : String(cell);
        });
    });

    var saveBtn = document.querySelector('.btn-save');
    if (saveBtn) {
        saveBtn.innerText = 'Đang lưu...';
        saveBtn.disabled = true;
    }

    fetch(window.DJANGO_SAVE_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ 'table_data': currentData })
    })
    .then(function(res) {
        if (!res.ok) {
            // Nếu gặp lỗi 405 hoặc 500, nhảy xuống .catch
            throw new Error('Server error: ' + res.status);
        }
        return res.json();
    })
    .then(function(data) {
        if (data.status === 'success') alert('Lưu thành công!');
        else alert('Lỗi: ' + data.message);
    })
    .catch(function(err) {
        console.error("Fetch error detail:", err);
        alert('Lỗi hệ thống (Vui lòng xem F12 Console)');
    })
    .finally(function() {
        if (saveBtn) {
            saveBtn.innerText = 'Save Changes';
            saveBtn.disabled = false;
        }
    });
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function generateAIContent() {
    // ... (Giữ nguyên không đổi vì đã hoạt động tốt)
    const promptText = document.getElementById('ai-prompt').value;
    const resultDisplay = document.getElementById('ai-result-display');
    const btn = document.getElementById('btn-ai-gen');

    if (!promptText) {
        alert("Vui lòng nhập yêu cầu!");
        return;
    }

    const originalText = btn.innerText;
    btn.innerText = "...";
    btn.disabled = true;
    resultDisplay.value = "Đang lấy kết quả...";

    fetch('/api/generate-ai-content/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'prompt': promptText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            let aiResult = data.result;
            aiResult = aiResult.replace(/`/g, "").trim();
            resultDisplay.value = aiResult;
            resultDisplay.select();
        } else {
            resultDisplay.value = "Lỗi!";
            alert("Lỗi: " + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        resultDisplay.value = "Lỗi kết nối!";
    })
    .finally(() => {
        btn.innerText = originalText;
        btn.disabled = false;
    });
}
function openExportModal() {
    document.getElementById('export-modal').style.display = 'block';
    // Ép về mặc định Excel khi mở
    const radioExcel = document.querySelector('input[name="export_type"][value="xlsx"]');
    if (radioExcel) radioExcel.checked = true;
    handleTypeChange('xlsx');
}

function closeExportModal() {
    document.getElementById('export-modal').style.display = 'none';
}

function togglePngOptions(show) {
    document.getElementById('png-settings').style.display = show ? 'block' : 'none';
}

// Đóng modal khi click ra ngoài
window.onclick = function(event) {
    let modal = document.getElementById('export-modal');
    if (event.target == modal) closeExportModal();
}

/**
 * Hàm chuyển số cột thành chữ (0 -> A, 1 -> B, 25 -> Z, 26 -> AA)
 */
function getColumnLabel(n) {
    let label = "";
    while (n >= 0) {
        label = String.fromCharCode((n % 26) + 65) + label;
        n = Math.floor(n / 26) - 1;
    }
    return label;
}

/**
 * Khi mở Modal: Mặc định chọn Excel và render preview Excel
 */
function openExportModal() {
    document.getElementById('export-modal').style.display = 'block';
    // Reset radio về Excel mỗi khi mở
    const radioExcel = document.querySelector('input[name="export_type"][value="xlsx"]');
    radioExcel.checked = true;

    // Gọi hàm chuyển đổi để áp dụng giao diện Excel mặc định
    handleTypeChange('xlsx');
}

/**
 * Xử lý thay đổi giữa Excel và PNG
 */
function handleTypeChange(type) {
    const pngSettings = document.getElementById('png-settings');
    const container = document.getElementById('preview-container');

    if (type === 'png') {
        pngSettings.style.display = 'block';

        // Cấu hình cho PNG: Căn giữa tuyệt đối
        container.style.display = 'flex';
        container.style.justifyContent = 'center';
        container.style.alignItems = 'center';
        container.style.overflow = 'hidden'; // Tắt cuộn để scale không bị lệch

        updatePngPreview();
    } else {
        pngSettings.style.display = 'none';

        // Cấu hình cho Excel: Cho phép cuộn ngang dọc
        container.style.display = 'block';
        container.style.overflow = 'auto';

        // Reset các style của PNG
        container.style.backgroundColor = 'white';
        container.style.backgroundImage = 'none';

        renderExcelPreview();
    }
}

/**
 * Render Preview kiểu Excel (Có tiêu đề hàng/cột)
 */
function renderExcelPreview() {
    if (!window.mySpreadsheet) return;
    const data = window.mySpreadsheet.getData();
    const container = document.getElementById('preview-container');

    // 1. Reset các thuộc tính scale của PNG (nếu có)
    container.style.backgroundColor = 'white';
    container.style.backgroundImage = 'none';

    // 2. Tăng giới hạn xem trước lên (ví dụ 20 hàng thay vì 5) để tận dụng thanh cuộn
    const maxR = Math.min(data.length, 20);
    const maxC = data[0] ? data[0].length : 0;

    let html = '<table class="preview-table" id="table-excel-preview">';

    // Header chữ cái (A, B, C...)
    html += '<tr style="position: sticky; top: 0; z-index: 10;">';
    html += '<td class="excel-header" style="background:#f0f0f0; border:1px solid #ccc; position: sticky; left: 0; z-index: 20;"></td>';
    for (let c = 0; c < maxC; c++) {
        html += `<td class="excel-header" style="background:#f0f0f0; border:1px solid #ccc; text-align:center; font-weight:bold; min-width:80px;">${getColumnLabel(c)}</td>`;
    }
    html += '</tr>';

    // Dữ liệu
    for (let r = 0; r < maxR; r++) {
        html += '<tr>';
        // Cột số thứ tự (1, 2, 3...) - Sticky bên trái
        html += `<td class="excel-header" style="background:#f0f0f0; border:1px solid #ccc; text-align:center; font-weight:bold; position: sticky; left: 0; z-index: 5;">${r + 1}</td>`;
        for (let c = 0; c < maxC; c++) {
            let cellVal = data[r][c] || '';
            html += `<td>${cellVal}</td>`;
        }
        html += '</tr>';
    }
    html += '</table>';

    container.innerHTML = html;

    // Đảm bảo bảng không bị scale
    const table = document.getElementById('table-excel-preview');
    if (table) table.style.transform = 'none';
}

/**
 * Render Preview kiểu PNG (Theo vùng chọn và màu nền)
 */
function updatePngPreview() {
    if (!window.mySpreadsheet) return;

    const startCell = document.getElementById('png-start').value || "A1";
    let rows = parseInt(document.getElementById('png-rows').value) || 1;
    let cols = parseInt(document.getElementById('png-cols').value) || 1;
    const bgColor = document.getElementById('bg-color-select').value;
    const container = document.getElementById('preview-container');
    const data = window.mySpreadsheet.getData();
    const startPos = parseCoords(startCell);

    // Giới hạn hiển thị preview tối đa 30x30
    rows = Math.min(rows, 30);
    cols = Math.min(cols, 30);

    let html = '<table id="table-render-preview" style="border-collapse: collapse; border: 1px solid #ddd;">';
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
    // Cập nhật Màu nền trực tiếp trong hàm này
    const table = document.getElementById('table-render-preview');
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
    const container = document.getElementById('preview-container');
    const table = document.getElementById('table-render-preview');

    if (!container || !table) return;

    // Reset để đo kích thước thực
    table.style.transform = 'scale(1)';
    table.style.margin = '0'; // Đảm bảo không bị margin làm lệch

    const containerW = container.offsetWidth - 40;
    const containerH = container.offsetHeight - 40;
    const tableW = table.scrollWidth;
    const tableH = table.scrollHeight;

    const scaleW = containerW / tableW;
    const scaleH = containerH / tableH;
    let scale = Math.min(scaleW, scaleH);

    if (scale > 1) scale = 1;

    // Áp dụng thu nhỏ
    table.style.transform = 'scale(' + scale + ')';
    // Đảm bảo thu nhỏ từ tâm để bảng nằm giữa khung flex
    table.style.transformOrigin = 'center';
}







