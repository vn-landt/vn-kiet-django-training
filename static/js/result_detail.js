// Thêm biến toàn cục để quản lý thời gian chờ
let autosaveTimeout = null;
document.addEventListener("DOMContentLoaded", function() {
        var rawData = window.DJANGO_TABLE_DATA || [['', '', '', '']];
    var spreadsheetDiv = document.getElementById('spreadsheet');
    if (spreadsheetDiv) {
        window.mySpreadsheet = jspreadsheet(spreadsheetDiv, {
            data: rawData,
            minDimensions: [10, 22  ],
            defaultColWidth: 120,
            tableOverflow: true,
            tableWidth: "100%",
            tableHeight: "600px",
            allowInsertRow: true, // Cho phép thêm dòng
            allowInsertColumn: true, // Cho phép thêm cột
            search: true,
            columnSorting: true,
            onchange: function() {
                // Kích hoạt tự động lưu khi có bất kỳ thay đổi nào
                triggerAutoSave();
            },
            oninsertrow: triggerAutoSave,
            oninsertcolumn: triggerAutoSave,
            ondeleterow: triggerAutoSave,
            ondeletecolumn: triggerAutoSave
        });
    }
});

/**
 * Hàm trì hoãn việc lưu (Debounce)
 */
function triggerAutoSave() {
    const statusEl = document.getElementById('autosave-status');
    if (statusEl) statusEl.innerText = "Đang chờ thay đổi...";

    clearTimeout(autosaveTimeout);
    // Chờ 2.5 giây sau khi người dùng ngừng thao tác mới gửi lên server
    autosaveTimeout = setTimeout(function() {
        performSave(true); // true = is_draft
    }, 2500);
}

/**
 * Hàm thực hiện gửi dữ liệu lên server
 * @param {boolean} isDraft - Trạng thái nháp hay chốt
 */
function performSave(isDraft) {
    if (!window.mySpreadsheet) return;

    const statusEl = document.getElementById('autosave-status');
    const finalTimeEl = document.getElementById('final-save-time-text'); // Phần tử trong modal
    const currentData = window.mySpreadsheet.getData().map(row =>
        row.map(cell => (cell === null || cell === undefined) ? "" : String(cell))
    );

    if (statusEl) {
        statusEl.innerText = isDraft ? "Đang tự động lưu bản nháp..." : "Đang chốt dữ liệu...";
    }

    fetch(window.DJANGO_SAVE_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            'table_data': currentData,
            'is_draft': isDraft
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            // 1. Cập nhật dòng trạng thái nháp (Dành cho cả Auto-save và Save Changes)
            if (statusEl) {
                statusEl.innerText = "Đã lưu bản nháp lúc " + data.updated_at;
            }

            // 2. Nếu là Save Changes (is_draft = false)
            if (isDraft === false) {
                // Cập nhật biến Final để Preview thay đổi theo
                window.FINAL_TABLE_DATA = JSON.parse(JSON.stringify(currentData));

                // Cập nhật dòng chữ thời gian bản chính trong Modal
                // Vì data.updated_at chỉ có Giờ:Phút:Giây, bạn có thể cộng thêm ngày từ JS hoặc Backend gửi thêm
                if (finalTimeEl) {
                    let now = new Date();
                    // Định dạng: dd/mm/yyyy HH:mm:ss
                    let dateStr = now.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
                    let timeStr = now.toLocaleTimeString('vi-VN', { hour12: false });
                    finalTimeEl.innerText = dateStr + " " + timeStr;
                }
            }
        }
    })
    .catch(err => {
        if (statusEl) statusEl.innerText = "Lỗi lưu dữ liệu!";
    });
}

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



/**
 * Hàm Callback đã sửa lỗi để hiển thị được lên bảng
 */
async function onImageCropped(blob) {
    // 1. Hỏi tọa độ (Kết quả trả về là STRING, ví dụ: "A1")
    const { value: targetCoordsStr } = await Swal.fire({
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

    // --- BƯỚC QUAN TRỌNG: CHUYỂN STRING THÀNH OBJECT ---
    const coordsObj = parseCoords(targetCoordsStr);
    // --------------------------------------------------

    // 2. Hiển thị Loading
    Swal.fire({
        title: 'Đang xử lý...',
        text: 'Đang phân tích vùng ảnh đã cắt',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    // 3. Chuẩn bị dữ liệu
    const formData = new FormData();
    formData.append('file', blob, 'extracted_part.jpg');
    formData.append('save_db', 'false');

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // 4. Gửi Request
    fetch("/extract-only-api/", {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        Swal.close();

        if (data.status === 'success') {
            // 5. CẬP NHẬT GIAO DIỆN: Dùng coordsObj đã parse thay vì targetCoordsStr
            updateTableDisplay(data.table, coordsObj);

            // Kích hoạt tự động lưu nháp
            triggerAutoSave();

            const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true
            });
            Toast.fire({ icon: 'success', title: 'Đã chèn dữ liệu thành công!' });

        } else {
            Swal.fire({ icon: 'error', title: 'Không thể trích xuất', text: data.message });
        }
    })
    .catch(err => {
        Swal.close();
        Swal.fire({ icon: 'error', title: 'Lỗi kết nối', text: 'Không thể kết nối tới máy chủ.' });
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

// Cập nhật lại hàm Save Changes cũ để nó trở thành nút "Chốt Final"
function saveTableData() {
    // Khi bấm nút này, ta coi như người dùng muốn chốt dữ liệu (Final)
    Swal.fire({
        title: 'Xác nhận lưu?',
        text: "Dữ liệu sẽ được đánh dấu là Final.",
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Đồng ý'
    }).then((result) => {
        if (result.isConfirmed) {
            performSave(false); // isDraft = false
            Swal.fire('Thành công!', 'Dữ liệu đã được chốt.', 'success');
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
