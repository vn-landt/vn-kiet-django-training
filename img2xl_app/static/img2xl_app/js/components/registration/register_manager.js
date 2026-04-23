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
	
	// BƯỚC 1: Luôn xóa sạch các class trạng thái cũ trước khi kiểm tra lại
	pass1.classList.remove('is-valid', 'is-invalid');
	pass2.classList.remove('is-valid', 'is-invalid');
	
	if (p1 && p2 && p1 === p2) {
		// TRƯỜNG HỢP KHỚP NHAU
		registrationStates.passwordMatch = true;
		passError.style.display = "none";
		
		// Thêm class xanh cho cả hai ô để đồng bộ UI
		pass1.classList.add('is-valid');
		pass2.classList.add('is-valid');
		
		updateTooltipStatus(reqPw, true);
	} else {
		// TRƯỜNG HỢP KHÔNG KHỚP HOẶC ĐANG TRỐNG
		registrationStates.passwordMatch = false;
		
		// Chỉ hiện thông báo lỗi và màu đỏ khi ô thứ 2 đã có dữ liệu mà vẫn sai
		if (p2 !== "") {
			passError.innerText = "Mật khẩu không khớp!";
			passError.style.display = "block";
			pass2.classList.add('is-invalid');
			// (Tùy chọn) pass1 cũng có thể hiện đỏ nếu bạn muốn
			// pass1.classList.add('is-invalid');
		} else {
			passError.style.display = "none";
		}
		
		updateTooltipStatus(reqPw, false);
	}
	
	// Luôn gọi hàm này để cập nhật trạng thái nút Submit
	if (typeof validateRegistrationForm === 'function') {
		validateRegistrationForm();
	}
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