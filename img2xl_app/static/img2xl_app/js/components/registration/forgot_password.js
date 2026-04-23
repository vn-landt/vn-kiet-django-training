// -*- coding: utf-8 -*-

document.addEventListener('DOMContentLoaded', function () {
	const emailInput = document.getElementById('id_email');
	const actionOtpBtn = document.getElementById('actionOtpBtn');
	const otpInput = document.getElementById('otp_code_input');
	const resendLink = document.getElementById('resend-link');
	const submitBtn = document.getElementById('submitBtn');
	const newPass = document.getElementById('new_password');
	const confirmPass = document.getElementById('confirm_new_password');

	
	// --- 1. Sự kiện kiểm tra Email ---
	emailInput.addEventListener('blur', function () {
		setTimeout(() => {
			const email = this.value.trim();
			const emailError = document.getElementById('email-error');
			const otpSection = document.getElementById('otp-section');
			const reqEmail = document.getElementById('req-email');
	
			// 1. Nếu trống hoặc đã xác thực OTP xong thì không làm gì
			if (!email || states.otpVerified) return;
	
			// 2. Kiểm tra định dạng Email bằng Regex
			const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
			if (!emailRegex.test(email)) {
				states.emailExists = false; // Hoặc một biến trạng thái định dạng riêng nếu bạn có
				emailError.innerText = "Định dạng email không hợp lệ!";
				emailError.style.display = "block";
				
				emailInput.classList.remove('is-valid');
				emailInput.classList.add('is-invalid');
				
				otpSection.style.display = "none";
				updateTooltipItem(reqEmail, false);
				validateFinal();
				return; // DỪNG LẠI, không gọi API nữa
			}
	
			// 3. Nếu định dạng đúng, tiến hành gọi API kiểm tra tồn tại
			apiCheckEmailExists(email).then(data => {
				if (data.is_taken) {
					states.emailExists = true;
					emailError.style.display = "none";
					
					emailInput.classList.remove('is-invalid');
					emailInput.classList.add('is-valid');
					
					otpSection.style.display = "block";
					updateTooltipItem(reqEmail, true);
				} else {
					states.emailExists = false;
					emailError.innerText = "Email này chưa được đăng ký!";
					emailError.style.display = "block";
					
					emailInput.classList.remove('is-valid');
					emailInput.classList.add('is-invalid');
					
					otpSection.style.display = "none";
					updateTooltipItem(reqEmail, false);
				}
				validateFinal();
			});
		}, 500);
	});
	// --- 2. Sự kiện mã OTP ---
	actionOtpBtn.addEventListener('click', function () {
		if (!states.codeSent) {
			// Gửi OTP
			if (resendCount >= MAX_RESEND) {
				document.getElementById('otp-status-msg').innerText = "Hết lượt gửi mã.";
				return;
			}
			actionOtpBtn.disabled = true;
			apiSendOtp(emailInput.value).then(data => {
				if (data.success) {
					states.codeSent = true;
					resendCount++;
					localStorage.setItem('forgot_otp_count', resendCount);
					actionOtpBtn.innerText = "Xác nhận mã";
					actionOtpBtn.disabled = false;
					document.getElementById('resend-text').style.display = "block";
					startResendTimer(60);
				}
			});
		} else {
			// Xác nhận OTP
			apiVerifyOtp(otpInput.value.trim()).then(data => {
				if (data.success) {
					states.otpVerified = true;
					document.getElementById('otp-section').classList.add('verified');
					document.getElementById('password-reset-section').style.display = "block";
					otpInput.readOnly = true;
					actionOtpBtn.disabled = true;
					updateTooltipItem(document.getElementById('req-otp'), true);
					validateFinal();
				}
			});
		}
	});
	
	resendLink.addEventListener('click', (e) => {
		e.preventDefault();
		if (countdown <= 0) actionOtpBtn.click();
	});
	
	// --- 3. Sự kiện Mật khẩu ---
	newPass.addEventListener('input', checkPasswordMatch);
	confirmPass.addEventListener('input', checkPasswordMatch);
	
	// --- 4. Gửi đổi mật khẩu cuối cùng ---
	submitBtn.addEventListener('click', function () {
		const btnText = this.querySelector('.btn-text');
		const loader = this.querySelector('.loader');
		
		submitBtn.disabled = true;
		if (btnText) btnText.style.display = "none";
		if (loader) loader.style.display = "block";
		
		apiResetPasswordFinal(emailInput.value, newPass.value)
			.then(async (data) => {
				if (data.success) {
					await Swal.fire({title: 'Thành công!', icon: 'success', confirmButtonText: 'Đăng nhập ngay'});
					window.location.href = "/login/";
				} else {
					await Swal.fire({title: 'Thất bại!', text: data.message, icon: 'error'});
					submitBtn.disabled = false;
					if (btnText) btnText.style.display = "block";
					if (loader) loader.style.display = "none";
				}
			});
	});
});