// static/js/home.js

/**
 * Luồng xử lý: image_handler.js (Modal) sau khi cắt xong
 * sẽ gọi hàm này và truyền miếng ảnh đã cắt (blob) vào.
 */
function onImageCropped(blob) {
    const formData = new FormData();
    formData.append('file', blob, "receipt_processed.jpg");
    formData.append('save_db', 'true'); // BẬT CÔNG TẮC LƯU

    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    Swal.fire({
        title: 'Đang trích xuất...',
        text: 'AI đang phân tích ảnh bạn đã chọn.',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    fetch('/extract-only-api/', {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': csrftoken }
    })
    .then(response => response.json())
    .then(data => {
        Swal.close();
        if (data.status === 'success') {
            // Xử lý thành công
            Swal.fire({
                icon: 'success',
                title: 'Hoàn tất!',
                text: 'Đã tìm thấy ' + data.table.length + ' hàng dữ liệu.',
                confirmButtonText: 'Xem chi tiết'
            }).then(() => {
                window.location.href = "/result/" + data.result_id + "/";
            });
        } else {
            Swal.fire('Lỗi AI', data.message, 'error');
            // Reset input để người dùng có thể chọn lại ảnh khác
            document.getElementById('id_file').value = "";
        }
    })
    .catch(error => {
        Swal.close();
        Swal.fire('Lỗi kết nối', 'Không thể gửi dữ liệu lên server.', 'error');
    });
}