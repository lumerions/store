import { showNotification } from './functions.js';
const passwordForm = document.getElementById("password-form")
const savePrefsBtn = document.getElementById("savePrefsBtn")
const orderEmailsCheckBox = document.getElementById("notifyToggle")
const emailModal = document.getElementById("emailModal")
const profileForm = document.getElementById("profile-form")
const verifyCodeBtn = document.getElementById("verifyCodeBtn")
const closeModalBtn = document.getElementById('closeModalBtn')

passwordForm.addEventListener("submit",async (e) => {
    e.preventDefault()
    const currentPassword = document.getElementById("currentPass").value
    const newPassword = document.getElementById("newPass").value

    try {
        const response = await fetch("/api/changePassword",{
            method: "POST",
            headers: {
                "Content-Type":"application/json",
            },
            body: JSON.stringify({
                currentpassword: currentPassword,
                newpassword: newPassword
           })
        })

        const data = await response.json()

        if (data.success) {
            showNotification("Successfully changed password.", "success")
        } else {
            showNotification(data.message)
        }

    } catch(error) {
        window.location.href = "/internalerror"
    }
})

savePrefsBtn.addEventListener("click", async () => {
    const Enabled = orderEmailsCheckBox.checked
    try {
        const response = await fetch("/api/ChangeOrderEmail",{
            method: "POST",
            headers: {
                "Content-Type":"application/json",
            },
            body: JSON.stringify({
                enable: Enabled
            })
        })

        const data = await response.json()

        if (data.success) {
            showNotification("Successfully changed order email preference.", "success")
        } else {
            showNotification(data.message)
        }

    } catch(error) {
        window.location.href = "/internalerror"
    }
})

profileForm.addEventListener("submit", async (e) => {
    e.preventDefault()

    const newEmail = document.getElementById("settingsEmail").value

    try {
        const response = await fetch("/api/ChangeAccountEmail",{
            method: "POST",
            headers: {
                "Content-Type":"application/json",
            },
            body: JSON.stringify({
                email: newEmail
            })
        })

        const data = await response.json()

        if (data.success) {
            emailModal.style.display = "flex"
        } else {
            showNotification(data.message || data.detail[0].msg)
        }

    } catch {
        window.location.href = "/internalerror"
    }
})

verifyCodeBtn.addEventListener("click", async () => {
    const verificationCodeInput = document.getElementById("verificationCode")
    const code = verificationCodeInput.value
    try {
        const response = await fetch("/api/VerifyEmail", {
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
            showNotification("Email verified successfully!", "success")
        } else {
            showNotification(data.message)
        }

    } catch(error) {
        window.location.href = "/internalerror"
    }
})

closeModalBtn.addEventListener("click", async () => {
    emailModal.style.display = "none"
})

async function LoadSettingsData() {
    try {
        const response = await fetch("/api/getSettingsData")
        const data = await response.json()

        console.log(data)

        if (data.currentemailaddress !== undefined) {
            document.getElementById("settingsEmail").value = data.currentemailaddress.trim();
        }

        if (data.orderEmails !== undefined) {
            document.getElementById("notifyToggle").checked = data.orderEmails;
        }

    } catch(error) {
        console.log(error)
    }
}

LoadSettingsData()