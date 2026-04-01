function handleGenerate() {
    // 1. Lấy phần tử input (Đảm bảo ID này trùng với ID trong HTML của bạn)
    const fileInput = document.getElementById('fileInput');

    // 2. KIỂM TRA FILE TRƯỚC KHI LÀM BẤT CỨ BIẾN NÀO KHÁC
    if (!fileInput || fileInput.files.length === 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Chú ý!',
            text: 'Bạn chưa chọn file ảnh nào để trích xuất.',
            confirmButtonText: 'Tôi sẽ chọn ngay',
            confirmButtonColor: '#f39c12'
        });
        return; // Dừng ngay lập tức, không chạy code phía dưới
    }

    // 3. Nếu đã có file, lúc này mới tạo FormData
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // 4. Lấy CSRF Token (Bắt buộc cho Django)
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]') ?
                      document.querySelector('[name=csrfmiddlewaretoken]').value : '';

    // 5. Hiển thị Loading tiếng Việt
    Swal.fire({
        title: 'Đang trích xuất...',
        text: 'AI đang đọc dữ liệu biên lai, vui lòng đợi.',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    // 6. Gửi request
    fetch('/extract-only-api/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrftoken
        }
    })
    .then(response => response.json())
    .then(data => {
        Swal.close();
        if (data.status === 'success') {
            // Xử lý khi thành công (ví dụ: vẽ bảng)
            console.log("Dữ liệu nhận được:", data.table);
            // Gọi hàm renderTable(data.table) của bạn ở đây
        } else {
            // Lỗi từ phía Python (file quá lớn, không phải hóa đơn...)
            Swal.fire({
                icon: 'error',
                title: 'Lỗi xử lý',
                text: data.message, // Tiếng Việt từ views.py trả về
                confirmButtonText: 'Đã hiểu'
            });
        }
    })
    .catch(error => {
        Swal.close();
        console.error("Lỗi Fetch:", error);
        Swal.fire({
            icon: 'error',
            title: 'Lỗi kết nối',
            text: 'Không thể kết nối với máy chủ. Vùi lòng kiểm tra mạng.',
        });
    });
}