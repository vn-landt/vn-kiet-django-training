document.addEventListener("DOMContentLoaded", function() {
    // 1. Load dữ liệu ban đầu và chia cột theo '|'
    var rawData = window.DJANGO_TABLE_DATA || [['', '', '', '']];
    var processedData = rawData.map(row => {
        if (Array.isArray(row)) {
            return row.flatMap(cell => typeof cell === 'string' ? cell.split('|') : cell);
        } else if (typeof row === 'string') {
            return row.split('|');
        }
        return row;
    });

    var spreadsheetDiv = document.getElementById('spreadsheet');
    if (spreadsheetDiv) {
        window.mySpreadsheet = jspreadsheet(spreadsheetDiv, {
            data: processedData,
            minDimensions: [11, 5],
            defaultColWidth: 150,
            tableOverflow: true,
            tableWidth: "100%",
            tableHeight: "400px",
        });
    }
});

// Hàm chuyển A1 -> {col: 0, row: 0}
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

    // Lấy dữ liệu hiện tại
    let tempData = window.mySpreadsheet.getData();

    // Duyệt ngược từ dưới lên trên (quan trọng khi chia dòng để không làm lệch index dòng chưa xử lý)
    for (let r = end.row; r >= start.row; r--) {
        // Duyệt ngược từ phải sang trái (quan trọng khi chia cột)
        for (let c = end.col; c >= start.col; c--) {
            let cellValue = tempData[r][c];

            if (cellValue && typeof cellValue === 'string') {
                let lastIdx = cellValue.lastIndexOf(char);

                if (lastIdx !== -1) {
                    let textBefore = cellValue.substring(0, lastIdx).trim();
                    let textAfter = cellValue.substring(lastIdx).trim(); // Bao gồm cả ký tự đặc biệt

                    if (actionType === 'split-col') {
                        // CHIA CỘT: Chèn thêm 1 cột ngay bên phải và đưa phần textAfter vào
                        tempData[r][c] = textBefore;
                        tempData[r].splice(c + 1, 0, textAfter);
                    }
                    else if (actionType === 'split-row') {
                        // CHIA DÒNG: Tạo 1 mảng mới (dòng mới) và chèn vào dưới dòng r
                        tempData[r][c] = textBefore;

                        // Tạo dòng mới có cùng số lượng cột nhưng chỉ chứa textAfter ở đúng vị trí cột c
                        let newRow = new Array(tempData[r].length).fill("");
                        newRow[c] = textAfter;

                        // Chèn dòng mới vào mảng dữ liệu
                        tempData.splice(r + 1, 0, newRow);
                    }
                    else if (actionType === 'remove') {
                        tempData[r][c] = cellValue.split(char).join('');
                    }
                }
            }
        }
    }

    // Load lại và cập nhật giao diện
    window.mySpreadsheet.setData(tempData);
}

// Giữ nguyên hàm parseCoords
function parseCoords(cellStr) {
    const match = cellStr.toUpperCase().match(/^([A-Z]+)(\d+)$/);
    if (!match) return null;
    let colStr = match[1], row = parseInt(match[2]) - 1, col = 0;
    for (let i = 0; i < colStr.length; i++) col = col * 26 + (colStr.charCodeAt(i) - 64);
    return { col: col - 1, row: row };
}

// Hàm lưu dữ liệu thực tế (Đã sửa để gộp bằng '|')
function saveTableData() {
    var currentData = mySpreadsheet.getData();
    var formattedData = currentData.map(row => row.join('|')); // Gộp lại bằng |

    var saveBtn = document.querySelector('.btn-save'); // Đảm bảo bạn có class này ở nút save
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
        body: JSON.stringify({ 'table_data': formattedData })
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
    const promptText = document.getElementById('ai-prompt').value;
    const resultDisplay = document.getElementById('ai-result-display');
    const btn = document.getElementById('btn-ai-gen');

    if (!promptText) {
        alert("Vui lòng nhập yêu cầu!");
        return;
    }

    // Hiệu ứng chờ
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

            // Loại bỏ dấu backtick (`) nếu Gemini trả về dạng markdown code
            aiResult = aiResult.replace(/`/g, "").trim();

            // Hiển thị vào ô kết quả bên trái nút
            resultDisplay.value = aiResult;

            // Tự động bôi đen để người dùng nhấn Ctrl+C luôn cho tiện
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