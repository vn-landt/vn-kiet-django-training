// -*- coding: utf-8 -*-

document.addEventListener('DOMContentLoaded', function () {
	const emailInput = document.getElementById('id_email');
	const pass1 = document.getElementById('id_password1');
	const pass2 = document.getElementById('id_password2');
	const actionOtpBtn = document.getElementById('actionOtpBtn');
	const resendLink = document.getElementById('resend-link');
	const otpInput = document.getElementById('otp_code_input');
	
	// 1. Kiểm tra mật khẩu khi nhập
	pass1.addEventListener('input', checkPasswordsMatch);
	pass2.addEventListener('input', checkPasswordsMatch);
	
	// 2. Kiểm tra Email duy nhất khi rời ô nhập
	emailInput.addEventListener('blur', function () {
		const email = this.value.trim();
		if (!email || registrationStates.otpVerified) return;
		
		apiCheckEmailUnique(email).then(data => {
			const emailError = document.getElementById('email-error');
			const emailSuccess = document.getElementById('email-success');
			const otpSection = document.getElementById('otp-section');
			const reqEmail = document.getElementById('req-email');
			
			if (data.is_taken) {
				registrationStates.emailUnique = false;
				emailError.innerText = "Email này đã được sử dụng!";
				emailError.style.display = "block";
				emailSuccess.style.display = "none";
				emailInput.classList.add('is-invalid');
				otpSection.style.display = "none";
				updateTooltipStatus(reqEmail, false);
			} else {
				registrationStates.emailUnique = true;
				emailError.style.display = "none";
				emailSuccess.style.display = "block";
				emailInput.classList.replace('is-invalid', 'is-valid');
				otpSection.style.display = "block";
				updateTooltipStatus(reqEmail, true);
			}
			validateRegistrationForm();
		});
	});
	
	// 3. Xử lý gửi hoặc xác nhận OTP
	actionOtpBtn.addEventListener('click', function () {
		const otpStatusMsg = document.getElementById('otp-status-msg');
		
		if (!registrationStates.codeSent) {
			if (otpResendCount >= MAX_RESEND) {
				otpStatusMsg.innerText = "Hết lượt gửi mã (Tối đa 3 lần!).";
				otpStatusMsg.style.color = "#e74c3c";
				return;
			}
			actionOtpBtn.disabled = true;
			otpStatusMsg.innerText = "Đang gửi...";
			
			apiSendOtp(emailInput.value).then(data => {
				if (data.success) {
					registrationStates.codeSent = true;
					otpResendCount++;
					localStorage.setItem('otp_resend_count', otpResendCount);
					actionOtpBtn.innerText = "Xác nhận mã";
					actionOtpBtn.disabled = false;
					document.getElementById('resend-text').style.display = "block";
					otpStatusMsg.innerText = "Đã gửi mã!";
					otpStatusMsg.style.color = "#2ecc71";
					startOtpTimer(60);
				} else {
					otpStatusMsg.innerText = data.message;
					otpStatusMsg.style.color = "#e74c3c";
					actionOtpBtn.disabled = false;
				}
			});
		} else {
			apiVerifyOtp(otpInput.value.trim()).then(data => {
				if (data.success) {
					registrationStates.otpVerified = true;
					otpStatusMsg.innerText = "Mã chính xác!";
					otpStatusMsg.style.color = "#2ecc71";
					document.getElementById('otp-section').classList.add('verified');
					otpInput.readOnly = true;
					actionOtpBtn.disabled = true;
					document.getElementById('resend-text').style.display = "none";
					updateTooltipStatus(document.getElementById('req-otp'), true);
					validateRegistrationForm();
				} else {
					otpStatusMsg.innerText = "Mã sai, hãy thử lại.";
					otpStatusMsg.style.color = "#e74c3c";
					otpInput.focus();
				}
			});
		}
	});
	
	// 4. Gửi lại mã OTP
	resendLink.addEventListener('click', function (e) {
		e.preventDefault();
		registrationStates.codeSent = false;
		otpInput.value = "";
		actionOtpBtn.click();
	});
});