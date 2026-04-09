document.addEventListener('DOMContentLoaded', function() {
    // --- 1. Khai báo các phần tử ---
    const registerForm = document.getElementById('registerForm');

    // Mật khẩu (Django id mặc định của UserCreationForm)
    const pass1 = document.getElementById('id_password1');
    const pass2 = document.getElementById('id_password2');
    const passError = document.getElementById('password-error');

    // Email
    const emailInput = document.getElementById('id_email');
    const emailError = document.getElementById('email-error');
    const emailSuccess = document.getElementById('email-success');

    // OTP
    const otpSection = document.getElementById('otp-section');
    const actionOtpBtn = document.getElementById('actionOtpBtn');
    const otpInput = document.getElementById('otp_code_input');
    const otpStatusMsg = document.getElementById('otp-status-msg');
    const resendArea = document.getElementById('resend-text');
    const resendLink = document.getElementById('resend-link');
    const timerText = document.getElementById('timer');

    // Nút đăng ký & Tooltip
    const submitBtn = document.getElementById('submitBtn');
    const reqPw = document.getElementById('req-pw');
    const reqEmail = document.getElementById('req-email');
    const reqOtp = document.getElementById('req-otp');

    // --- 2. Biến trạng thái (Logic bước 6) ---
    let states = {
        passwordMatch: false,
        emailUnique: false,
        otpVerified: false,
        codeSent: false
    };

    const MAX_RESEND = 10;
    let resendCount = parseInt(localStorage.getItem('otp_resend_count') || 0);

    // --- 3. Logic Kiểm tra Mật khẩu (Bước 2) ---
    function checkPasswords() {
        const p1 = pass1.value;
        const p2 = pass2.value;

        if (p1 && p2 && p1 === p2) {
            states.passwordMatch = true;
            passError.style.display = "none";
            pass2.classList.remove('is-invalid');
            pass2.classList.add('is-valid');
            updateTooltipItem(reqPw, true);
        } else {
            states.passwordMatch = false;
            if (p2) {
                passError.innerText = "Mật khẩu không khớp!";
                passError.style.display = "block";
                pass2.classList.add('is-invalid');
            }
            updateTooltipItem(reqPw, false);
        }
        validateForm();
    }

    pass1.addEventListener('input', checkPasswords);
    pass2.addEventListener('input', checkPasswords);

    // --- 4. Logic Kiểm tra Email (Bước 3 & 4) ---
    emailInput.addEventListener('blur', function() {
        const email = this.value.trim();
        if (!email || states.otpVerified) return;

        fetch('/check-email/?email=' + encodeURIComponent(email))
            .then(res => res.json())
            .then(data => {
                if (data.is_taken) {
                    states.emailUnique = false;
                    emailError.innerText = "Email này đã được sử dụng!";
                    emailError.style.display = "block";
                    emailSuccess.style.display = "none";
                    emailInput.classList.add('is-invalid');
                    otpSection.style.display = "none"; // Bước 4: Ẩn nếu trùng
                    updateTooltipItem(reqEmail, false);
                } else {
                    states.emailUnique = true;
                    emailError.style.display = "none";
                    emailSuccess.style.display = "block";
                    emailInput.classList.remove('is-invalid');
                    emailInput.classList.add('is-valid');
                    otpSection.style.display = "block"; // Bước 4: Hiện khung OTP
                    updateTooltipItem(reqEmail, true);
                }
                validateForm();
            });
    });

    // --- 5. Logic OTP (Bước 5) ---
    actionOtpBtn.addEventListener('click', function() {
        if (!states.codeSent) {
            handleSendOtp();
        } else {
            handleVerifyOtp();
        }
    });

    // Sự kiện khi nhấn vào dòng chữ nhỏ "Gửi lại mã"
    resendLink.addEventListener('click', function(e) {
        e.preventDefault(); // Ngăn trang web nhảy lên đầu

        // Reset lại trạng thái để gửi mã mới
        isCodeSent = false;
        otpInput.value = ""; // Xóa ô nhập cũ cho người dùng nhập mã mới
        otpStatusMsg.innerText = "Đang gửi mã mới...";
        otpStatusMsg.style.color = "#3498db";

        // Gọi hàm gửi OTP (Hàm này sẽ gọi API backend)
        handleSendOtp();
    });

    function handleSendOtp() {
        if (resendCount >= MAX_RESEND) {
            otpStatusMsg.innerText = "Hết lượt gửi mã (Tối đa 3 lần 1 ngày!).";
            otpStatusMsg.style.color = "#e74c3c";
            return;
        }

        actionOtpBtn.disabled = true;
        otpStatusMsg.innerText = "Đang gửi...";

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
                localStorage.setItem('otp_resend_count', resendCount);
                actionOtpBtn.innerText = "Xác nhận mã";
                actionOtpBtn.disabled = false;
                resendArea.style.display = "block";
                otpStatusMsg.innerText = "Đã gửi mã!";
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
                otpStatusMsg.innerText = "Mã chính xác!";
                otpStatusMsg.style.color = "#2ecc71";
                otpSection.classList.add('verified'); // Bước 5: Khung đổi màu xanh
                otpInput.readOnly = true;
                actionOtpBtn.disabled = true;
                resendArea.style.display = "none";
                updateTooltipItem(reqOtp, true);
                validateForm();
            } else {
                otpStatusMsg.innerText = "Mã sai, hãy thử lại.";
                otpStatusMsg.style.color = "#e74c3c";
                otpInput.focus();
            }
        });
    }

    // --- 6. Quản lý Nút Đăng ký & Tooltip (Bước 6) ---
    function updateTooltipItem(element, isValid) {
        if (isValid) {
            element.classList.remove('invalid');
            element.classList.add('valid');
        } else {
            element.classList.remove('valid');
            element.classList.add('invalid');
        }
    }

    function validateForm() {
        const allOk = states.passwordMatch && states.emailUnique && states.otpVerified;
        if (allOk) {
            submitBtn.disabled = false;
            submitBtn.style.opacity = "1";
        } else {
            submitBtn.disabled = true;
            submitBtn.style.opacity = "0.5";
        }
    }

    // --- 7. Hàm bổ trợ (Timer, Cookie) ---
    function startTimer(seconds) {
        let count = seconds;
        resendLink.style.pointerEvents = "none";
        const itv = setInterval(() => {
            count--;
            timerText.innerText = `(${count}s)`;
            if (count <= 0) {
                clearInterval(itv);
                timerText.innerText = "";
                resendLink.style.pointerEvents = "auto";
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