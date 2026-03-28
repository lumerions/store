document.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signupForm');
    if (!signupForm) return;

    document.getElementById('signupForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById('submit-btn');
        const errorBox = document.getElementById('error-box');
        const errorMessage = document.getElementById('error-message');
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;

        if (!submitBtn) {
            console.error("Critical Error: submit-btn not found in HTML.");
            return;
        }

        errorBox.style.display = 'none'

        function showError(text) {
            errorMessage.innerText = text;
            errorBox.style.display = 'block';
            submitBtn.disabled = false;
            submitBtn.innerText = "Create account";
        }

        submitBtn.disabled = true;
        submitBtn.innerText = "Creating account...";

        if (password !== confirmPassword) {
            showError("Passwords dont match.")
            return
        }

        if (username.length > 20) {
            showError("Username cannot be over 20 characters.")
            return
        }

        if (password.length < 8) {
            showError("Passwords must be atleast 8 characters long.")
            return
        }

        const usernameRegex = /^\w{3,20}$/;

        if (!usernameRegex.test(username)) {
            showError("Username can only contain letters, numbers, and underscores (3-20 characters).");
            return;
        }

        try {
            const response = await fetch("/signup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    confirmpassword: confirmPassword,
                    password: password,
                    username: username,
                    email: email
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
})