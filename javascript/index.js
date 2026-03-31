import { showNotification } from './functions.js';
import { logout } from './functions.js';
let cart = JSON.parse(localStorage.getItem('store_cart')) || [];
const loginBtn = document.querySelector('.login-btn'); 
const loginBtnText = document.querySelector('button.login-btn'); 

function toggleCart() {
    const panel = document.getElementById('cart-panel');
    const overlay = document.getElementById('cart-overlay');
    
    panel.classList.toggle('open');
    overlay.style.display = panel.classList.contains('open') ? 'block' : 'none';
    
    renderCart();
}

function addToCart(name, price) {
    const item = {
        id: Date.now(), 
        name: name,
        price: price
    };
    
    cart.push(item);
    saveAndRefresh();
}

function removeItem(id) {
    cart = cart.filter(item => item.id !== id);
    saveAndRefresh();
}

function saveAndRefresh() {
    localStorage.setItem('store_cart', JSON.stringify(cart));
    updateCountBadge();
    renderCart();
}

function updateCountBadge() {
    const badge = document.getElementById('cart-count');
    if(badge) badge.innerText = cart.length;
}

function renderCart() {
    const container = document.getElementById('cart-items');
    const totalEl = document.getElementById('cart-total');
    
    container.innerHTML = '';
    let total = 0;

    if (cart.length === 0) {
        container.innerHTML = `
            <div class="empty-cart-state">
                <svg width="50" height="50" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"></circle><circle cx="20" cy="21" r="1"></circle><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path></svg>
                <p>Your cart is empty</p>
            </div>`;
    } else {
        cart.forEach((item, index) => {
            const numPrice = parseFloat(item.price.replace('$', ''));
            total += numPrice;

            container.innerHTML += `
                <div class="cart-item-row">
                    <div class="cart-item-info">
                        <div class="cart-item-details">
                            <h4 class="cart-item-name">${item.name}</h4>
                            <span class="cart-item-price">${item.price}</span>
                        </div>
                    </div>
                    <button class="cart-item-remove" onclick="removeItem(${index})" aria-label="Remove item">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
            `;
        });
    }
    
    totalEl.innerText = `$${total.toFixed(2)}`;
}

function openCheckout() {
    if (cart.length === 0) {
        showNotification("Add some items first!")
        return;
    }

    document.getElementById('cart-panel').classList.remove('open');
    document.getElementById('cart-overlay').style.display = 'none';
    const total = cart.reduce((sum, item) => sum + parseFloat(item.price.replace('$', '')), 0);
    document.getElementById('modal-total-display').innerText = `$${total.toFixed(2)}`;
    document.getElementById('checkout-modal').style.display = 'block';
    document.getElementById('modal-overlay').style.display = 'block';
}

function closeCheckout() {
    document.getElementById('checkout-modal').style.display = 'none';
    document.getElementById('modal-overlay').style.display = 'none';
}

function processPayment(method) {    
    saveAndRefresh();
    closeCheckout();
    showNotification("Success! Your order has been placed.", "success");
}

updateCountBadge();

async function CheckIfUserLoggedIn() {
    try {
        const response = await fetch("/userloggedin", {
            method: "GET",
            credentials: "include"
        })

        if (!response) {
            throw new Error("GET request was not okay. " + response.statusText)
        }

        const data = await response.json()

        if (!data.loggedin) {
            loginBtnText.innerText = "Login"
            loginBtn.style.display = "flex"
        } else {
            loginBtnText.innerText = "Logout"
            loginBtn.style.display = "flex"
        }

        if (data.isadmin) {
            const adminBtn = document.getElementById("admin-btn");
            adminBtn.style.display = "flex"
        }

    } catch {
        window.location.href = "/internalerror"
    }
}

CheckIfUserLoggedIn()
logout()

window.toggleCart = toggleCart
window.addToCart = addToCart
window.removeItem = removeItem
window.openCheckout = openCheckout
window.closeCheckout = closeCheckout
window.processPayment = processPayment