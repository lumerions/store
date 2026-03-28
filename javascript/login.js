document.addEventListener('DOMContentLoaded', () => {
    const signupForm = document.getElementById('signupForm');
    if (!signupForm) return;

    document.getElementById('signupForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = document.getElementById('submit-btn');
        const errorBox = document.getElementById('error-box');
        const errorMessage = document.getElementById('error-message');
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        if (!submitBtn) {
            console.error("Critical Error: submit-btn not found in HTML.");
            return;
        }

        errorBox.style.display = 'none'

        function showError(text) {
            errorMessage.innerText = text;
            errorBox.style.display = 'block';
            submitBtn.disabled = false;
            submitBtn.innerText = "Log In";
        }

        submitBtn.disabled = true;
        submitBtn.innerText = "Logging in...";

        try {
            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    password: password,
                    username: username,
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