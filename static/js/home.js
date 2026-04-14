// Ví dụ đoạn JS xử lý nút "Generate"
function handleGenerate() {
    // Hiển thị loading...
    Swal.fire({
        title: 'Đang xử lý...',
        text: 'Vui lòng chờ trong giây lát',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading() }
    });

    // Gọi API của bạn (ví dụ dùng fetch hoặc $.ajax)
    fetch('/extract-only-api/', { method: 'POST', body: formData })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            Swal.close();
            // Render table...
        } else {
            // ĐÂY LÀ PHẦN THÔNG BÁO LỖI CHUYÊN NGHIỆP
            Swal.fire({
                icon: 'error',
                title: 'Thông báo',
                text: data.message, // Thông báo từ Python: "Tài liệu không hợp lệ..."
                confirmButtonText: 'Chọn lại ảnh',
                confirmButtonColor: '#3085d6',
            }).then((result) => {
                if (result.isConfirmed) {
                    // Reset input file để user chọn lại
                    document.getElementById('fileInput').value = "";
                }
            });
        }
    });
}

