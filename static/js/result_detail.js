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



function handlePicGenerate() {
    const fileInput = document.getElementById('pic-upload');
    if (fileInput.files.length === 0) return alert("Vui lòng chọn ảnh!");
    const targetCoords = TableCoordinateHelper.ask("Chọn ô bắt đầu:");
    if (!targetCoords) return;

    const btn = document.querySelector('.btn-purple');
    btn.innerText = "..."; btn.disabled = true;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch("/extract-only-api/", {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') updateTableDisplay(data.table, targetCoords);
        else alert("Lỗi: " + data.message);
    })
    .finally(() => { btn.innerText = "Generate 1 pic into"; btn.disabled = false; });
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

    for (let r = end.row; r >= start.row; r--) {
        for (let c = end.col; c >= start.col; c--) {
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
