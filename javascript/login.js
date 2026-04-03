import { showNotification } from "./functions.js";

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const OTPBtn = document.getElementById("send-otp-btn");
    const emailModal = document.getElementById("emailModal");
    const verifyCodeBtn = document.getElementById("verifyCodeBtn");
    const verificationCodeInput = document.getElementById("verificationCode");
    const closeModalBtn = document.getElementById("closeModalBtn");
    const delay = (ms) => new Promise(res => setTimeout(res, ms));
    let username = null;

    if (!loginForm) return;

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById("submit-btn");
        const errorBox = document.getElementById("error-box");
        const errorMessage = document.getElementById("error-message");
        const password = document.getElementById("password").value;
        username = document.getElementById("username").value.trim();

        if (!submitBtn || !errorBox || !errorMessage) return; 

        errorBox.style.display = "none";
        submitBtn.disabled = true;
        submitBtn.innerText = "Logging in...";

        function showError(text) {
            errorMessage.innerText = text;
            errorBox.style.display = "block";
            submitBtn.disabled = false;
            submitBtn.innerText = "Login";
        }

        try {
            const response = await fetch("/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });

            const responseJson = await response.json();
            console.log(responseJson);

            if (!responseJson.success) {
                const message = responseJson.message || responseJson.detail?.[0]?.msg;
                showError(message);
                return;
            }

            window.location.replace("/");
        } catch (error) {
            console.log(error);
            if (error.message) {
                showError(error.message);
            } else {
                showError(String(error));
            }
        }
    });

    if (OTPBtn && emailModal) {
        OTPBtn.addEventListener("click", async () => {
            emailModal.style.display = "flex";
            username = document.getElementById("username")?.value.trim() || "";

            try {
                const response = await fetch("/api/OTP", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username })
                });

                const data = await response.json();
                if (data.success) {
                    showNotification("Sent verification email to the email linked to your account.", "success");
                } else {
                    showNotification(data.message);
                }
            } catch (error) {
                window.location.href = "/internalerror";
            }
        });
    }

    if (verifyCodeBtn && verificationCodeInput && emailModal) {
        verifyCodeBtn.addEventListener("click", async () => {
            const code = verificationCodeInput.value;

            try {
                const response = await fetch("/api/VerifyOTP", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ code })
                });

                const data = await response.json();
                if (data.success) {
                    await delay(1000);
                    verificationCodeInput.value = "";
                    emailModal.style.display = "none";
                    showNotification("Successfully logged in via OTP.", "success");
                    await delay(2500);
                    window.location.href = "/";
                } else {
                    emailModal.style.display = "none";
                    showNotification(data.message);
                }
            } catch (error) {
                window.location.href = "/internalerror";
            }
        });
    }

    if (closeModalBtn && emailModal) {
        closeModalBtn.addEventListener("click", () => {
            emailModal.style.display = "none";
        });
    }
});