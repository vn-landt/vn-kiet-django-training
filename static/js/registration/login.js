document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById('loginForm');
    var btn = document.getElementById('submitBtn');
    var loader = document.getElementById('loader');
    var btnText = btn.querySelector('.btn-text');

    form.addEventListener('submit', function() {
        // Vô hiệu hóa nút để tránh double-submit
        btn.disabled = true;
        btn.style.opacity = '0.7';

        // Hiển thị hiệu ứng loading
        btnText.style.visibility = 'hidden';
        loader.style.display = 'block';
    });
});