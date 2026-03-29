import { showNotification } from './functions.js';

async function adminApi(url,payload,btnID) {
    const btn = document.getElementById(btnID)
    const originalText = btn.innerText

    btn.disabled = true
    btn.innerText = "Processing..."

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        })

        const apiData = await response.json()

        if (apiData.success) {
            showNotification("Successfully ran admin command.", "success")
            return true
        } else {
            showNotification(apiData.message || "An unknown error occurred.")
            return false
        }
    } catch(error) {
        showNotification("Internal Server Error")
        return false
    } finally {
        btn.disabled = false
        btn.innerText = originalText
    }
}

document.getElementById('add-item-form').onsubmit = async (e) => {
    e.preventDefault()
    const offsaleInput = document.getElementById('editItemOffsale').value.toLowerCase()
    const isOffsale = (offsaleInput === "true")
    const data = {
        itemname: document.getElementById('itemName').value,
        price: document.getElementById('itemPrice').value,
        imageurl: document.getElementById('itemImage').value,
        description: document.getElementById('itemDesc').value,
        offsale: isOffsale
    }
    if (await adminApi("/adminapi/newitem", data, "submitBtn")) e.target.reset()
}

document.getElementById('lock-account-form').onsubmit = async (e) => {
    e.preventDefault()
    const data = {
        username: document.getElementById('lockUsername').value,
        lockaccount: document.getElementById('lockAction').value
    }
    await adminApi("/adminapi/lockAccount", data, "lockSubmitBtn")
}

document.getElementById('edit-item-form').onsubmit = async (e) => {
    e.preventDefault()
    const offsaleInput = document.getElementById('editItemOffsale').value.toLowerCase()
    const isOffsale = (offsaleInput === "true")
    const data = {
        itemname: document.getElementById('editItemName').value,
        price: document.getElementById('editItemPrice').value,
        imageurl: document.getElementById('editItemImage').value,
        description: document.getElementById('editItemDesc').value,
        offsale: isOffsale
    }
    await adminApi("/adminapi/changeItem", data, "editSubmitBtn")
}