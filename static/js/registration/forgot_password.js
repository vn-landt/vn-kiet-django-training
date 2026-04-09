document.addEventListener('DOMContentLoaded', function() {
    // --- 1. Khai báo các phần tử ---
    const emailInput = document.getElementById('id_email');
    const emailError = document.getElementById('email-error');
    const otpSection = document.getElementById('otp-section');
    const actionOtpBtn = document.getElementById('actionOtpBtn');
    const otpInput = document.getElementById('otp_code_input');
    const otpStatusMsg = document.getElementById('otp-status-msg');
    const resendArea = document.getElementById('resend-text');
    const resendLink = document.getElementById('resend-link');
    const timerText = document.getElementById('timer');
    const submitBtn = document.getElementById('submitBtn');

    // Tooltip items
    const reqEmail = document.getElementById('req-email');
    const reqOtp = document.getElementById('req-otp');
    const reqPw = document.getElementById('req-pw'); // Đảm bảo ID này có trong HTML

    // Phần mật khẩu mới
    const passSection = document.getElementById('password-reset-section');
    const newPass = document.getElementById('new_password');
    const confirmPass = document.getElementById('confirm_new_password');
    const passMatchError = document.getElementById('pass-match-error');

    // --- 2. Trạng thái hệ thống ---
    let states = {
        emailExists: false,
        otpVerified: false,
        codeSent: false,
        passMatch: false // Đã bổ sung
    };

    const MAX_RESEND = 3;
    // Đồng bộ với localStorage như trang Register
    let resendCount = parseInt(localStorage.getItem('forgot_otp_count') || 0);

    // --- 3. Kiểm tra Email tồn tại ---
    emailInput.addEventListener('blur', function() {
        const email = this.value.trim();
        if (!email || states.otpVerified) return;

        fetch('/check-email/?email=' + encodeURIComponent(email))
            .then(res => res.json())
            .then(data => {
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
                    emailInput.classList.add('is-invalid');
                    otpSection.style.display = "none";
                    updateTooltipItem(reqEmail, false);
                }
                validateFinal(); // Phải gọi ở đây để cập nhật nút
            })
            .catch(err => console.error("Lỗi kiểm tra email:", err));
    });

    // --- 4. Gửi/Xác nhận mã ---
    actionOtpBtn.addEventListener('click', function() {
        if (!states.codeSent) handleSendOtp();
        else handleVerifyOtp();
    });

    resendLink.addEventListener('click', function(e) {
        e.preventDefault();
        if (countdown <= 0) handleSendOtp();
    });

    function handleSendOtp() {
        if (resendCount >= MAX_RESEND) {
            otpStatusMsg.innerText = "Hết lượt gửi mã (Max 3).";
            otpStatusMsg.style.color = "#e74c3c";
            return;
        }

        actionOtpBtn.disabled = true;
        otpStatusMsg.innerText = "Đang gửi mã...";

        fetch('/send-otp/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: emailInput.value })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                states.codeSent = true;
                resendCount++;
                localStorage.setItem('forgot_otp_count', resendCount);

                actionOtpBtn.innerText = "Xác nhận mã";
                actionOtpBtn.disabled = false;
                resendArea.style.display = "block";
                otpStatusMsg.innerText = "Mã mới đã được gửi!";
                otpStatusMsg.style.color = "#2ecc71";
                startTimer(60);
            } else {
                otpStatusMsg.innerText = data.message;
                otpStatusMsg.style.color = "#e74c3c";
                actionOtpBtn.disabled = false;
            }
        });
    }

    function handleVerifyOtp() {
        const code = otpInput.value.trim();
        fetch('/verify-otp-ajax/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
            body: JSON.stringify({ otp: code })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                states.otpVerified = true;
                otpStatusMsg.innerText = "Xác nhận thành công!";
                otpStatusMsg.style.color = "#2ecc71";
                otpSection.classList.add('verified');

                passSection.style.display = "block";
                otpInput.readOnly = true;
                actionOtpBtn.disabled = true;
                resendArea.style.display = "none";
                updateTooltipItem(reqOtp, true);
                validateFinal();
            } else {
                otpStatusMsg.innerText = "Mã sai.";
                otpStatusMsg.style.color = "#e74c3c";
            }
        });
    }

    // --- 5. Kiểm tra mật khẩu (Bước cuối) ---
    function checkPass() {
        const p1 = newPass.value;
        const p2 = confirmPass.value;

        if (p1 && p2 && p1 === p2) {
            states.passMatch = true;
            passMatchError.style.display = "none";
            confirmPass.classList.remove('is-invalid');
            confirmPass.classList.add('is-valid');
            updateTooltipItem(reqPw, true); // Cập nhật tooltip
        } else {
            states.passMatch = false;
            if (p2) {
                passMatchError.innerText = "Mật khẩu không khớp!";
                passMatchError.style.display = "block";
                confirmPass.classList.add('is-invalid');
            }
            updateTooltipItem(reqPw, false);
        }
        validateFinal();
    }

    newPass.addEventListener('input', checkPass);
    confirmPass.addEventListener('input', checkPass);

    // --- 6. Điều khiển nút Đăng ký ---
    function validateFinal() {
        const isReady = states.emailExists && states.otpVerified && states.passMatch;
        if (isReady) {
            submitBtn.disabled = false;
            submitBtn.style.opacity = "1";
            submitBtn.style.cursor = "pointer";
        } else {
            submitBtn.disabled = true;
            submitBtn.style.opacity = "0.5";
            submitBtn.style.cursor = "not-allowed";
        }
    }

    // --- 7. Gửi dữ liệu Đổi mật khẩu ---
    submitBtn.addEventListener('click', function() {
        const btnText = this.querySelector('.btn-text');
        const loader = this.querySelector('.loader');

        submitBtn.disabled = true;
        btnText.style.display = "none";
        loader.style.display = "block";

        fetch('/reset-password-final/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
            body: JSON.stringify({
                password: newPass.value,
                email: emailInput.value
            })
        })
        .then(res => res.json())
        .then(async (data) => { // Thêm async ở đây để dùng được await bên trong
            if (data.success) {
                // Thông báo thành công và chờ người dùng nhấn OK
                await Swal.fire({
                    title: 'Thành công!',
                    text: 'Mật khẩu của bạn đã được cập nhật thành công.',
                    icon: 'success',
                    confirmButtonText: 'Đăng nhập ngay',
                    confirmButtonColor: '#3498db',
                });

                // Sau khi nhấn OK mới chuyển trang
                window.location.href = "/login/";

            } else {
                // Thông báo lỗi
                await Swal.fire({
                    title: 'Thất bại!',
                    text: 'Lỗi: ' + (data.message || 'Đã có lỗi xảy ra'),
                    icon: 'error',
                    confirmButtonText: 'Thử lại',
                    confirmButtonColor: '#e74c3c',
                });

                // Reset lại trạng thái nút bấm sau khi đóng thông báo lỗi
                submitBtn.disabled = false;
                if (btnText) btnText.style.display = "block";
                if (loader) loader.style.display = "none";
            }
        })
    });

    // --- Hàm bổ trợ ---
    function updateTooltipItem(el, ok) {
        if (!el) return;
        el.className = ok ? "req-item valid" : "req-item invalid";
    }

    let countdown = 0;
    function startTimer(seconds) {
        countdown = seconds;
        resendLink.style.pointerEvents = "none";
        resendLink.style.color = "#ccc";
        const itv = setInterval(() => {
            countdown--;
            timerText.innerText = `(${countdown}s)`;
            if (countdown <= 0) {
                clearInterval(itv);
                timerText.innerText = "";
                resendLink.style.pointerEvents = "auto";
                resendLink.style.color = "#3498db";
            }
        }, 1000);
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});