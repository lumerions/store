
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById("loginForm");
    const OTPBtn = document.getElementById("send-otp-btn");
    const emailModal = document.getElementById("emailModal");
    const verifyCodeBtn = document.getElementById("verifyCodeBtn");
    if (!loginForm) return;

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById('submit-btn');
        const errorBox = document.getElementById('error-box');
        const errorMessage = document.getElementById('error-message');
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        errorBox.style.display = 'none'
        submitBtn.disabled = true;
        submitBtn.innerText = "Logging in...";

        function showError(text) {
            errorMessage.innerText = text;
            errorBox.style.display = 'block';
            submitBtn.disabled = false;
            submitBtn.innerText = "Create account";
        }

        try {
            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                })
            })

            const responseJson = await response.json()

            console.log(responseJson)

            if (!responseJson.success) {
                const message = responseJson.message || responseJson.detail[0].msg
                showError(message)
                return
            }
            
            window.location.replace("/")
        } catch(error) {
            console.log(error)
            if (error.message) {
                showError(error.message)
            } else {
                showError(String(error))
            }
        }
    })

    OTPBtn.addEventListener("click", async () => {
        emailModal.style.display = "flex"
    })

    verifyCodeBtn.addEventListener("click",async () => {
        const verificationCodeInput = document.getElementById("verificationCode")
        const code = verificationCodeInput.value

        try {
            const response = await fetch("/api/OTP", {
                method: "POST",
                headers: {
                    "Content-Type":"application/json",
                },
                body: JSON.stringify({
                    code: code,
                })
            })

            const data = await response.json()
    
            if (data.success) {
                verificationCodeInput.value = ""
                emailModal.style.display = "none"
                showNotification("Successfully logged in via OTP.", "success")
            } else {
                showNotification(data.message)
            }
        } catch {
            window.location.href = "/internalerror"
        }
    })
})