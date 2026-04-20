// -*- coding: utf-8 -*-

// Trạng thái hệ thống
let states = {
	emailExists: false,
	otpVerified: false,
	codeSent: false,
	passMatch: false
};

const MAX_RESEND = 3;
let resendCount = parseInt(localStorage.getItem('forgot_otp_count') || 0);
let countdown = 0;

/**
 * Cập nhật trạng thái icon/màu sắc của tooltip
 */
function updateTooltipItem(el, ok) {
	if (!el) return;
	el.className = ok ? "req-item valid" : "req-item invalid";
}

/**
 * Kiểm tra tổng thể để kích hoạt nút Gửi
 */
function validateFinal() {
	const submitBtn = document.getElementById('submitBtn');
	const isReady = states.emailExists && states.otpVerified && states.passMatch;
	
	if (submitBtn) {
		submitBtn.disabled = !isReady;
		submitBtn.style.opacity = isReady ? "1" : "0.5";
		submitBtn.style.cursor = isReady ? "pointer" : "not-allowed";
	}
}

/**
 * Xử lý đếm ngược thời gian gửi lại mã
 */
function startResendTimer(seconds) {
	const resendLink = document.getElementById('resend-link');
	const timerText = document.getElementById('timer');
	
	countdown = seconds;
	if (resendLink) {
		resendLink.style.pointerEvents = "none";
		resendLink.style.color = "#ccc";
	}
	
	const itv = setInterval(() => {
		countdown--;
		if (timerText) timerText.innerText = `(${countdown}s)`;
		
		if (countdown <= 0) {
			clearInterval(itv);
			if (timerText) timerText.innerText = "";
			if (resendLink) {
				resendLink.style.pointerEvents = "auto";
				resendLink.style.color = "#3498db";
			}
		}
	}, 1000);
}

/**
 * Kiểm tra mật khẩu mới và xác nhận mật khẩu có khớp không
 */
function checkPasswordMatch() {
	const newPass = document.getElementById('new_password');
	const confirmPass = document.getElementById('confirm_new_password');
	const passMatchError = document.getElementById('pass-match-error');
	const reqPw = document.getElementById('req-pw');
	
	const p1 = newPass.value;
	const p2 = confirmPass.value;
	
	if (p1 && p2 && p1 === p2) {
		states.passMatch = true;
		if (passMatchError) passMatchError.style.display = "none";
		confirmPass.classList.remove('is-invalid');
		confirmPass.classList.add('is-valid');
		updateTooltipItem(reqPw, true);
	} else {
		states.passMatch = false;
		if (p2 && passMatchError) {
			passMatchError.innerText = "Mật khẩu không khớp!";
			passMatchError.style.display = "block";
			confirmPass.classList.add('is-invalid');
		}
		updateTooltipItem(reqPw, false);
	}
	validateFinal();
}