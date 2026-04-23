// -*- coding: utf-8 -*-

/**
 * Kiểm tra email có tồn tại trong hệ thống hay không
 */
function apiCheckEmailExists(email) {
	return fetch('/check-email/?email=' + encodeURIComponent(email))
		.then(res => res.json());
}

/**
 * Gửi mã OTP tới email
 */
function apiSendOtp(email) {
	return fetch('/send-otp/', {
		method: 'POST',
		headers: {
			'X-CSRFToken': getCookie('csrftoken'), //
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({email: email})
	}).then(res => res.json());
}

/**
 * Xác nhận mã OTP người dùng nhập
 */
function apiVerifyOtp(code) {
    // Dùng URLSearchParams là cách an toàn nhất cho Django trên GAE
    const params = new URLSearchParams();
    params.append('otp', code);

    return fetch('/verify-otp-ajax/', {
       method: 'POST',
       headers: {
          'X-CSRFToken': getCookie('csrftoken'), // Đảm bảo hàm getCookie này hoạt động
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'XMLHttpRequest'
       },
       body: params
    }).then(res => res.json());
}

/**
 * Gửi yêu cầu đổi mật khẩu cuối cùng
 */
function apiResetPasswordFinal(email, password) {
	return fetch('/reset-password-final/', {
		method: 'POST',
		headers: {
			'X-CSRFToken': getCookie('csrftoken'),
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			password: password,
			email: email
		})
	}).then(res => res.json());
}
