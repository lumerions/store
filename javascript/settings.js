const passwordForm = document.getElementById("password-form")
const savePrefsBtn = document.getElementById("savePrefsBtn")
const orderEmailsCheckBox = document.getElementById("notifyToggle")
import { showNotification } from './functions.js';

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
        const response = await fetch("ChangeOrderEmail",{
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