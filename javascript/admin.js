import { showNotification } from './functions.js';

async function adminApi(url, payload, btnID) {
    const btn = document.getElementById(btnID);
    const originalText = btn.innerText;

    btn.disabled = true;
    btn.innerText = "Processing...";

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const apiData = await response.json();

        if (apiData.success) {
            showNotification("Successfully ran admin command.", "success");
            return true;
        } else {
            showNotification(apiData.message || "An unknown error occurred.");
            return false;
        }
    } catch(error) {
        showNotification("Internal Server Error");
        return false;
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
}

document.getElementById('add-item-form').onsubmit = async (e) => {
    e.preventDefault();
    const offsaleInput = document.getElementById('editItemOffsale').value.toLowerCase();
    const isOffsale = (offsaleInput === "true");
    const data = {
        itemname: document.getElementById('itemName').value,
        price: document.getElementById('itemPrice').value,
        imageurl: document.getElementById('itemImage').value,
        description: document.getElementById('itemDesc').value,
        offsale: isOffsale
    };
    if (await adminApi("/adminapi/newitem", data, "submitBtn")) e.target.reset();
};

document.getElementById('lock-account-form').onsubmit = async (e) => {
    e.preventDefault();
    const data = {
        username: document.getElementById('lockUsername').value,
        lockaccount: document.getElementById('lockAction').value
    };
    await adminApi("/adminapi/lockAccount", data, "lockSubmitBtn");
};

document.getElementById('edit-item-form').onsubmit = async (e) => {
    e.preventDefault();
    const offsaleInput = document.getElementById('editItemOffsale').value.toLowerCase();
    const isOffsale = (offsaleInput === "true");
    const data = {
        itemname: document.getElementById('editItemName').value,
        price: document.getElementById('editItemPrice').value,
        imageurl: document.getElementById('editItemImage').value,
        description: document.getElementById('editItemDesc').value,
        offsale: isOffsale
    };
    await adminApi("/adminapi/changeItem", data, "editSubmitBtn");
};

async function deliverOrder(OrderId) {
    try {
        const payload = {
            orderid: Number(OrderId)
        };
        const response = await fetch("/adminapi/deliverOrder", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const apiData = await response.json();

        if (apiData.success) {
            showNotification("Successfully ran admin command.", "success");
        } else {
            showNotification(apiData.message || "An unknown error occurred.");
        }
    } catch(error) {
        showNotification("Internal Server Error");
    }
}

async function loadPendingOrders() {
    try {
        const response = await fetch("/adminapi/getPendingOrders");
        const data = await response.json();

        console.log(data);

        const tableBody = document.getElementById('orders-table-body');
        const orderCount = document.getElementById('order-count');

        if (data.success && data.orders.length > 0) {
            tableBody.innerHTML = '';
            orderCount.innerText = `${data.orders.length} Pending`;

            data.orders.forEach(order => {
                tableBody.innerHTML += `
                    <tr style="border-bottom: 1px solid #eee">
                        <td style="padding: 12px; font-weight: 600">#${order.id}</td>
                        <td style="padding: 12px">${order.username}</td>
                        <td style="padding: 12px; font-size: 0.9rem">${order.items}</td>
                        <td style="padding: 12px; color: var(--accent); font-weight: 700">${order.total}</td>
                        <td style="padding: 12px">
                            <button class="add-btn" 
                                    onclick="deliverOrder(${order.id})" 
                                    style="padding: 6px 12px; font-size: 0.8rem; background: #10b981">
                                Mark Delivered
                            </button>
                        </td>
                    </tr>
                `;
            });
        } else {
            tableBody.innerHTML = '<tr><td colspan="5" style="padding: 40px; text-align: center; color: #999">No pending orders found.</td></tr>';
            orderCount.innerText = '0 Pending';
        }
    } catch (err) {
        console.log(err);
        showNotification("Failed to load orders:");
    }
}

loadPendingOrders();