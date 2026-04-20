// -*- coding: utf-8 -*-

// Biến trạng thái đăng ký
let registrationStates = {
	passwordMatch: false,
	emailUnique: false,
	otpVerified: false,
	codeSent: false
};

const MAX_RESEND = 3;
let otpResendCount = parseInt(localStorage.getItem('otp_resend_count') || 0);

/**
 * Cập nhật trạng thái valid/invalid cho tooltip
 */
function updateTooltipStatus(element, isValid) {
	if (!element) return;
	if (isValid) {
		element.classList.remove('invalid');
		element.classList.add('valid');
	} else {
		element.classList.remove('valid');
		element.classList.add('invalid');
	}
}

/**
 * Kiểm tra điều kiện để kích hoạt nút Đăng ký
 */
function validateRegistrationForm() {
	const submitBtn = document.getElementById('submitBtn');
	const allOk = registrationStates.passwordMatch &&
		registrationStates.emailUnique &&
		registrationStates.otpVerified;
	
	if (submitBtn) {
		submitBtn.disabled = !allOk;
		submitBtn.style.opacity = allOk ? "1" : "0.5";
	}
}

/**
 * Logic kiểm tra mật khẩu khớp nhau
 */
function checkPasswordsMatch() {
	const pass1 = document.getElementById('id_password1');
	const pass2 = document.getElementById('id_password2');
	const passError = document.getElementById('password-error');
	const reqPw = document.getElementById('req-pw');
	
	const p1 = pass1.value;
	const p2 = pass2.value;
	
	if (p1 && p2 && p1 === p2) {
		registrationStates.passwordMatch = true;
		passError.style.display = "none";
		pass2.classList.replace('is-invalid', 'is-valid');
		updateTooltipStatus(reqPw, true);
	} else {
		registrationStates.passwordMatch = false;
		if (p2) {
			passError.innerText = "Mật khẩu không khớp!";
			passError.style.display = "block";
			pass2.classList.add('is-invalid');
		}
		updateTooltipStatus(reqPw, false);
	}
	validateRegistrationForm();
}

/**
 * Bộ đếm ngược thời gian gửi lại mã
 */
function startOtpTimer(seconds) {
	const timerText = document.getElementById('timer');
	const resendLink = document.getElementById('resend-link');
	let count = seconds;
	
	if (resendLink) resendLink.style.pointerEvents = "none";
	
	const itv = setInterval(() => {
		count--;
		if (timerText) timerText.innerText = `(${count}s)`;
		if (count <= 0) {
			clearInterval(itv);
			if (timerText) timerText.innerText = "";
			if (resendLink) resendLink.style.pointerEvents = "auto";
		}
	}, 1000);
}