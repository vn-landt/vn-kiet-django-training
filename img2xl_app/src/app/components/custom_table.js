document.addEventListener("DOMContentLoaded", function() {
    // 1. Load dữ liệu ban đầu trực tiếp (Không dùng split('|') nữa)
    // Vì Backend giờ đã trả về mảng 2 chiều (2D Array) rất chuẩn
    var rawData = window.DJANGO_TABLE_DATA || [['', '', '', '']];

    var spreadsheetDiv = document.getElementById('spreadsheet');
    if (spreadsheetDiv) {
        window.mySpreadsheet = jspreadsheet(spreadsheetDiv, {
            data: rawData, // Nạp thẳng dữ liệu vào
            minDimensions: [11, 5],
            defaultColWidth: 150,
            tableOverflow: true,
            tableWidth: "100%",
            tableHeight: "400px",
        });
    }
});

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

// Xử lý Chia Cột hoặc Xóa Ký Tự theo phạm vi
function handleRangeAction(actionType) {
    const startInput = document.getElementById('range-start').value;
    const endInput = document.getElementById('range-end').value;
    const char = document.getElementById('special-char').value;

    if (!startInput || !endInput || !char) {
        alert("Vui lòng nhập đủ thông tin!");
        return;
    }

    const start = parseCoords(startInput);
    const end = parseCoords(endInput);

    if (!start || !end || end.row < start.row || (end.row === start.row && end.col < start.col)) {
        alert("Phạm vi không hợp lệ!");
        return;
    }

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
                    }
                    else if (actionType === 'split-row') {
                        tempData[r][c] = textBefore;
                        let newRow = new Array(tempData[r].length).fill("");
                        newRow[c] = textAfter;
                        tempData.splice(r + 1, 0, newRow);
                    }
                    else if (actionType === 'remove') {
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
    // Lấy mảng 2 chiều nguyên bản từ jspreadsheet
    var currentData = mySpreadsheet.getData();

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
        // Gửi thẳng mảng 2 chiều lên server
        body: JSON.stringify({ 'table_data': currentData })
    })
    .then(response => response.json())
    .then(data => {
        if (saveBtn) {
            saveBtn.innerText = 'Save Changes';
            saveBtn.disabled = false;
        }
        if (data.status === 'success') alert('Lưu thành công!');
        else alert('Lỗi: ' + data.message);
    })
    .catch(error => {
        console.error('Lỗi:', error);
        if (saveBtn) saveBtn.disabled = false;
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