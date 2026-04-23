document.addEventListener('DOMContentLoaded', function () {
	var form = document.getElementById('loginForm');
	var btn = document.getElementById('submitBtn');
	var loader = document.getElementById('loader');
	var btnText = btn.querySelector('.btn-text');
	
	form.addEventListener('submit', function () {
		// Vô hiệu hóa nút để tránh double-submit
		btn.disabled = true;
		btn.style.opacity = '0.7';
		
		// Hiển thị hiệu ứng loading
		btnText.style.visibility = 'hidden';
		loader.style.display = 'block';
	});
	
	const passwordField = document.getElementById('id_password');
	
	if (passwordField) {
		// 1. Tạo container bao bọc
		const wrapper = document.createElement('div');
		wrapper.className = 'password-field-container';
		
		// 2. Chèn container vào trước ô input, rồi đưa ô input vào trong container
		passwordField.parentNode.insertBefore(wrapper, passwordField);
		wrapper.appendChild(passwordField);
		
		// 3. Tạo icon con mắt
		const eyeIcon = document.createElement('i');
		eyeIcon.className = 'fa fa-eye toggle-password';
		wrapper.appendChild(eyeIcon);
		
		// 4. Sự kiện click ẩn/hiện
		eyeIcon.addEventListener('click', function () {
			if (passwordField.type === 'password') {
				passwordField.type = 'text';
				this.classList.remove('fa-eye');
				this.classList.add('fa-eye-slash');
			} else {
				passwordField.type = 'password';
				this.classList.remove('fa-eye-slash');
				this.classList.add('fa-eye');
			}
		});
	}
});