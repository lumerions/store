document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    function showError(text) {
        errorMessage.innerText = text;
        errorBox.style.display = 'block';
    }

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const username = document.getElementById('username').value.trim();
    const submitBtn = document.getElementById('submit-btn');

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

    submitBtn.disabled = true;
    submitBtn.innerText = "Creating account...";

    async function signup() {
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
            
            console.log(await response.json())
        } catch(error) {
            console.log(error)
        }
    }

    signup()
})